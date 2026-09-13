"""
clean_normalize.py
===================

Paso 4 del roadmap: Limpieza y normalización -> capa `processed/`.

Consume:
  - data/raw/*.xlsx                         (fuentes originales)
  - data/local/id_bridge_local.parquet       (mapa nombre_norm -> id_cliente_anon,
                                               generado en el paso 3, SOLO local)

Produce (todo en data/processed/, sin ningún dato personal):
  - reservas_clean.parquet
  - ventas_clean.parquet
  - items_clean.parquet
  - transacciones_clean.parquet
  - servicios_clean.parquet

No se genera `clientes_clean.parquet`: la identidad de cliente ya vive en
`dim_cliente_anon.parquet` (paso 3), que reemplaza a clientes.xlsx como
fuente de verdad de cliente a partir de aquí.

Reglas aplicadas (ver docs/entregas/06_data_profiling.md y
docs/entregas/08_limpieza_normalizacion.md):

  - Todo campo personal (nombre, email, teléfono, RUT, dirección) se
    resuelve a id_cliente_anon en este mismo paso y se descarta. Ningún
    archivo de processed/ contiene PII.
  - Clave de unión ventas/items: `ID interno` = `ID Venta`, con fallback
    por `Cliente + Fecha (minuto)` para el ~29-31% de filas anteriores a
    abril de 2024 que no tienen `ID interno`.
  - Nombres ambiguos (mismo nombre, distinto teléfono/email en
    clientes.xlsx) no se pueden desambiguar en ventas/items porque esas
    fuentes no traen teléfono ni email: se colapsan en una identidad
    canónica marcada `identidad_ambigua = True`.
  - `transacciones` solo se vincula por `ID Venta` exacto (no tiene
    columna de cliente ni de fecha de venta para construir un fallback
    fiable); el estado de pago de una venta se determina con
    `ventas."Monto pendiente" == 0`, no con `transacciones."Estado de pago"`
    (ver alerta de profiling §6.2).
  - `Local` se descarta en todas las fuentes: valor constante
    ("Beauty Girl Studio"), no aporta información.
"""

import argparse
import hashlib
import re
import unicodedata
from pathlib import Path

import pandas as pd


# ---------------------------------------------------------------------------
# Normalización (debe mantenerse en sincronía con src/identity/resolve_identity.py)
# ---------------------------------------------------------------------------

def normalizar_nombre(s) -> str:
    if pd.isna(s):
        return ""
    s = str(s).strip().lower()
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("utf-8")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def parsear_fecha(serie: pd.Series) -> pd.Series:
    return pd.to_datetime(serie, dayfirst=True, errors="coerce")


def clave_fallback(nombre_norm: str, fecha) -> str:
    """Clave de respaldo cuando no hay ID interno / ID Venta: Cliente + minuto."""
    if pd.isna(fecha):
        minuto = "sin_fecha"
    else:
        minuto = pd.Timestamp(fecha).strftime("%Y-%m-%d %H:%M")
    return f"FB|{nombre_norm}|{minuto}"


# ---------------------------------------------------------------------------
# Mapa de identidad (nombre_norm -> id_cliente_anon), canonicalizando
# nombres ambiguos porque ventas/items no traen teléfono/email para
# desambiguar (ver docs/entregas/08_limpieza_normalizacion.md §2)
# ---------------------------------------------------------------------------

def construir_mapa_identidad(bridge: pd.DataFrame) -> pd.DataFrame:
    """
    IMPORTANTE: el flag `identidad_ambigua` que trae `bridge` (paso 3) marca
    TODO nombre que tuvo más de un registro en clientes.xlsx, incluidos los
    casos donde esos registros se fusionaron correctamente en una sola
    identidad (mismo teléfono/email -> 92 casos de 187 en la validación de
    la Entrega 07). Ese flag original es útil como trazabilidad de origen,
    pero NO debe usarse tal cual como "riesgo de mezclar dos clientas
    distintas en ventas/items", porque en la mayoría de los casos no hay
    tal riesgo: ya se resolvió con evidencia (teléfono o email).

    Aquí se calcula un flag distinto y más preciso para processed/:
    `identidad_ambigua_transaccional` = True solo cuando un mismo
    nombre_norm quedó repartido en 2+ id_cliente_anon distintos (los 46
    nombres / 95 identidades de la Entrega 07). Es en ESOS casos, y solo en
    esos, donde ventas/items no pueden distinguir a qué persona pertenece
    cada transacción (no tienen teléfono/email) y por eso se colapsan en
    una identidad canónica marcada con este flag.
    """
    n_identidades_por_nombre = bridge.groupby("nombre_norm")["id_cliente_anon"].nunique()
    ambiguedad_transaccional = (n_identidades_por_nombre > 1).rename("identidad_ambigua_transaccional")

    canon = (
        bridge.sort_values(
            ["nombre_norm", "n_registros_clientes_xlsx", "fecha_creacion_declarada"],
            ascending=[True, False, True],
        )
        .groupby("nombre_norm", as_index=False)
        .first()[["nombre_norm", "id_cliente_anon"]]
    )
    canon = canon.merge(ambiguedad_transaccional, on="nombre_norm", how="left")
    return canon


def mapear_a_id_cliente(df: pd.DataFrame, col_nombre_norm: str, mapa: pd.DataFrame) -> pd.DataFrame:
    out = df.merge(mapa, left_on=col_nombre_norm, right_on="nombre_norm", how="left")
    out["identidad_ambigua_transaccional"] = out["identidad_ambigua_transaccional"].fillna(False)
    return out


# ---------------------------------------------------------------------------
# Limpieza por fuente
# ---------------------------------------------------------------------------

def limpiar_reservas(reservas: pd.DataFrame, mapa: pd.DataFrame) -> pd.DataFrame:
    df = reservas.copy()
    df = df.drop_duplicates()  # 112 duplicados exactos detectados en el profiling

    df["nombre_norm"] = (
        df["Nombre"].fillna("").astype(str).str.strip()
        + " "
        + df["Apellido"].fillna("").astype(str).str.strip()
    ).map(normalizar_nombre)

    df["fecha_realizacion"] = parsear_fecha(df["Fecha de realización"])
    df["fecha_creacion"] = parsear_fecha(df["Fecha de creación"])
    df["fecha_pago"] = parsear_fecha(df["Fecha pago"])

    df = mapear_a_id_cliente(df, "nombre_norm", mapa)

    columnas_finales = [
        "id_cliente_anon",
        "identidad_ambigua_transaccional",
        "fecha_realizacion",
        "fecha_creacion",
        "Servicio",
        "Precio lista",
        "Precio real",
        "Prestador",
        "Estado",
        "Estado de pago",
        "fecha_pago",
        "Origen",
        "Preferencia Cliente",
    ]
    return df[columnas_finales]


def limpiar_ventas(ventas: pd.DataFrame, mapa: pd.DataFrame) -> pd.DataFrame:
    df = ventas.copy()
    df = df.drop_duplicates()

    df["nombre_norm"] = df["Cliente"].map(normalizar_nombre)
    df["fecha"] = parsear_fecha(df["Fecha"])

    tiene_id_interno = df["ID interno"].notna()
    df["clave_venta"] = df["ID interno"].astype(str)
    df.loc[~tiene_id_interno, "clave_venta"] = df.loc[~tiene_id_interno].apply(
        lambda r: clave_fallback(r["nombre_norm"], r["fecha"]), axis=1
    )
    df["clave_venta_origen"] = tiene_id_interno.map({True: "id_interno", False: "fallback_cliente_fecha"})

    df = mapear_a_id_cliente(df, "nombre_norm", mapa)

    columnas_finales = [
        "id_cliente_anon",
        "identidad_ambigua_transaccional",
        "clave_venta",
        "clave_venta_origen",
        "ID",
        "fecha",
        "Monto venta",
        "Monto a pagar",
        "Monto pendiente",
    ]
    return df[columnas_finales]


def limpiar_items(items: pd.DataFrame, mapa: pd.DataFrame) -> pd.DataFrame:
    df = items.copy()
    df = df.drop_duplicates()  # 3 duplicados exactos detectados en el profiling

    df["nombre_norm"] = df["Cliente"].map(normalizar_nombre)
    df["fecha_venta"] = parsear_fecha(df["Fecha venta"])
    df["fecha_reserva"] = parsear_fecha(df["Fecha reserva"])

    tiene_id_venta = df["ID Venta"].notna()
    df["clave_venta"] = df["ID Venta"].astype(str)
    df.loc[~tiene_id_venta, "clave_venta"] = df.loc[~tiene_id_venta].apply(
        lambda r: clave_fallback(r["nombre_norm"], r["fecha_venta"]), axis=1
    )
    df["clave_venta_origen"] = tiene_id_venta.map({True: "id_venta", False: "fallback_cliente_fecha"})

    df = mapear_a_id_cliente(df, "nombre_norm", mapa)

    columnas_finales = [
        "id_cliente_anon",
        "identidad_ambigua_transaccional",
        "clave_venta",
        "clave_venta_origen",
        "Tipo item",
        "Categoría",
        "Nombre item",
        "Cantidad",
        "Precio unitario",
        "Descuento",
        "Total",
        "Prestador",
        "fecha_venta",
        "fecha_reserva",
    ]
    return df[columnas_finales]


def limpiar_transacciones(transacciones: pd.DataFrame) -> pd.DataFrame:
    """
    transacciones.xlsx no tiene columna de cliente ni forma fiable de
    construir un fallback de unión (no hay nombre ni Local). Por eso solo
    se vincula por 'ID Venta' exacto; el 30.7% sin match queda con
    clave_venta nula y se documenta como no vinculable (ver
    docs/entregas/08_limpieza_normalizacion.md §3).
    """
    df = transacciones.copy()
    df = df.drop_duplicates()

    df["fecha"] = parsear_fecha(df["Fecha"])
    df["clave_venta"] = df["ID Venta"].astype(str).where(df["ID Venta"].notna(), None)

    columnas_finales = ["clave_venta", "fecha", "Monto", "Propina", "Método de Pago"]
    return df[columnas_finales]


def limpiar_servicios(servicios: pd.DataFrame) -> pd.DataFrame:
    # Catálogo pequeño y sin PII: limpieza mínima (nombres de columna,
    # tipos). No requiere anonimización ni descarte de columnas.
    return servicios.copy()


# ---------------------------------------------------------------------------
# Orquestación
# ---------------------------------------------------------------------------

def ejecutar(raw_dir: Path, bridge_path: Path, processed_dir: Path) -> dict:
    clientes = None  # ya no se usa como fuente: reemplazado por id_bridge_local
    reservas = pd.read_excel(raw_dir / "reservas.xlsx")
    ventas = pd.read_excel(raw_dir / "ventas.xlsx")
    items = pd.read_excel(raw_dir / "items.xlsx")
    transacciones = pd.read_excel(raw_dir / "transacciones.xlsx")
    servicios = pd.read_excel(raw_dir / "servicios.xlsx")

    bridge = pd.read_parquet(bridge_path)
    mapa = construir_mapa_identidad(bridge)

    reservas_clean = limpiar_reservas(reservas, mapa)
    ventas_clean = limpiar_ventas(ventas, mapa)
    items_clean = limpiar_items(items, mapa)
    transacciones_clean = limpiar_transacciones(transacciones)
    servicios_clean = limpiar_servicios(servicios)

    processed_dir.mkdir(parents=True, exist_ok=True)
    reservas_clean.to_parquet(processed_dir / "reservas_clean.parquet", index=False)
    ventas_clean.to_parquet(processed_dir / "ventas_clean.parquet", index=False)
    items_clean.to_parquet(processed_dir / "items_clean.parquet", index=False)
    transacciones_clean.to_parquet(processed_dir / "transacciones_clean.parquet", index=False)
    servicios_clean.to_parquet(processed_dir / "servicios_clean.parquet", index=False)

    # -------- Reporte de calidad (para dejar constancia en la entrega) --------
    reporte = {
        "reservas_filas_raw": len(reservas),
        "reservas_filas_clean": len(reservas_clean),
        "reservas_pct_sin_id_cliente": round(reservas_clean["id_cliente_anon"].isna().mean() * 100, 1),

        "ventas_filas_raw": len(ventas),
        "ventas_filas_clean": len(ventas_clean),
        "ventas_pct_sin_id_cliente": round(ventas_clean["id_cliente_anon"].isna().mean() * 100, 1),
        "ventas_pct_clave_fallback": round((ventas_clean["clave_venta_origen"] == "fallback_cliente_fecha").mean() * 100, 1),
        "ventas_pct_identidad_ambigua_transaccional": round(ventas_clean["identidad_ambigua_transaccional"].mean() * 100, 1),

        "items_filas_raw": len(items),
        "items_filas_clean": len(items_clean),
        "items_pct_sin_id_cliente": round(items_clean["id_cliente_anon"].isna().mean() * 100, 1),
        "items_pct_clave_fallback": round((items_clean["clave_venta_origen"] == "fallback_cliente_fecha").mean() * 100, 1),

        "transacciones_filas_raw": len(transacciones),
        "transacciones_filas_clean": len(transacciones_clean),
        "transacciones_pct_sin_clave_venta": round(transacciones_clean["clave_venta"].isna().mean() * 100, 1),

        "servicios_filas": len(servicios_clean),
    }
    return reporte


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", type=Path, required=True)
    parser.add_argument("--bridge-path", type=Path, required=True,
                         help="Ruta a id_bridge_local.parquet generado en el paso 3")
    parser.add_argument("--processed-dir", type=Path, required=True)
    args = parser.parse_args()

    reporte = ejecutar(args.raw_dir, args.bridge_path, args.processed_dir)

    print("=== Reporte de limpieza y normalización ===")
    for k, v in reporte.items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()