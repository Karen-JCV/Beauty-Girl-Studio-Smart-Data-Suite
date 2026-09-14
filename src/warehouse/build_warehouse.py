"""
build_warehouse.py
====================

Paso 5 del roadmap: construcción del warehouse relacional (SQLite).

Consume (capa processed/, sin PII -- ver docs/entregas/08_limpieza_normalizacion.md):
  - reservas_clean.parquet
  - ventas_clean.parquet
  - items_clean.parquet
  - transacciones_clean.parquet
  - servicios_clean.parquet

Consume (capa segura del paso 3 -- ver docs/entregas/07_resolucion_identidad.md):
  - dim_cliente_anon.parquet

Produce:
  - beauty_studio.db (SQLite) con las tablas:
      dim_cliente_anon, dim_servicio,
      fact_ventas, fact_items, fact_transacciones, fact_reservas

Decisiones de esquema (ver docs/entregas/09_warehouse.md):
  - fact_items NO repite id_cliente_anon: se valida que items_clean y
    ventas_clean asignan siempre el mismo id_cliente_anon para una misma
    clave_venta (0% de inconsistencia comprobado), así que la identidad
    del cliente vive solo en fact_ventas; fact_items se conecta a ella por
    clave_venta.
  - fact_items NO tiene FK estricta a dim_servicio: el nombre del ítem
    coincide con el catálogo solo al 94% (incluye texto libre como
    "por Elsi" o variantes de promociones). La categoría sí coincide al
    100%, así que dim_servicio queda como catálogo de referencia
    consultable por categoría, no como FK obligatoria fila a fila.
  - Claves foráneas activas (PRAGMA foreign_keys = ON): cualquier
    violación de integridad referencial hace fallar la carga en vez de
    insertar datos inconsistentes en silencio.
  - Verificación de PII por CONTENIDO (no solo nombres de columna) sobre
    la base de datos ya construida, repitiendo el error detectado y
    corregido en el paso 4.
"""

import argparse
import sqlite3
from pathlib import Path

import pandas as pd

DDL = """
PRAGMA foreign_keys = ON;

CREATE TABLE dim_cliente_anon (
    id_cliente_anon           TEXT PRIMARY KEY,
    codigo_display            INTEGER UNIQUE NOT NULL,
    fecha_creacion_declarada  TEXT,
    identidad_ambigua         INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE dim_servicio (
    id_servicio            INTEGER PRIMARY KEY,
    nombre                 TEXT NOT NULL,
    categoria              TEXT,
    precio                 REAL,
    duracion_minutos       INTEGER,
    servicio_grupal        INTEGER,
    capacidad_grupo        REAL,
    servicio_a_domicilio   INTEGER,
    reservar_online        INTEGER
);

CREATE TABLE fact_ventas (
    id_venta                          INTEGER PRIMARY KEY,
    clave_venta                       TEXT UNIQUE NOT NULL,
    clave_venta_origen                TEXT NOT NULL,
    id_cliente_anon                   TEXT NOT NULL,
    identidad_ambigua_transaccional   INTEGER NOT NULL DEFAULT 0,
    fecha                             TEXT NOT NULL,
    monto_venta                       REAL,
    monto_a_pagar                     REAL,
    monto_pendiente                   REAL,
    ids_venta_originales               TEXT NOT NULL,
    n_ventas_fusionadas                INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (id_cliente_anon) REFERENCES dim_cliente_anon(id_cliente_anon)
);

CREATE TABLE fact_items (
    id_item          INTEGER PRIMARY KEY AUTOINCREMENT,
    clave_venta      TEXT NOT NULL,
    tipo_item        TEXT,
    categoria        TEXT,
    nombre_item      TEXT,
    cantidad         REAL,
    precio_unitario  REAL,
    descuento        REAL,
    total            REAL,
    prestador        TEXT,
    fecha_venta      TEXT,
    fecha_reserva    TEXT,
    FOREIGN KEY (clave_venta) REFERENCES fact_ventas(clave_venta)
);

CREATE TABLE fact_transacciones (
    id_transaccion  INTEGER PRIMARY KEY,
    clave_venta     TEXT,
    fecha           TEXT,
    monto           REAL,
    propina         REAL,
    metodo_pago     TEXT,
    FOREIGN KEY (clave_venta) REFERENCES fact_ventas(clave_venta)
);

CREATE TABLE fact_reservas (
    id_reserva            INTEGER PRIMARY KEY AUTOINCREMENT,
    id_cliente_anon       TEXT,
    fecha_realizacion     TEXT,
    fecha_creacion        TEXT,
    servicio_texto        TEXT,
    precio_lista          REAL,
    precio_real           REAL,
    prestador             TEXT,
    estado                TEXT,
    estado_pago           TEXT,
    fecha_pago            TEXT,
    origen                TEXT,
    preferencia_cliente   TEXT,
    FOREIGN KEY (id_cliente_anon) REFERENCES dim_cliente_anon(id_cliente_anon)
);
"""


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

def si_no_a_bool(serie: pd.Series) -> pd.Series:
    return serie.map({"Sí": 1, "No": 0}).astype("Int64")


def fecha_a_texto(serie: pd.Series) -> pd.Series:
    return pd.to_datetime(serie, errors="coerce").dt.strftime("%Y-%m-%d %H:%M:%S")


# ---------------------------------------------------------------------------
# Transformación de cada tabla a la forma final del esquema
# ---------------------------------------------------------------------------

def preparar_dim_cliente_anon(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["fecha_creacion_declarada"] = fecha_a_texto(out["fecha_creacion_declarada"])
    out["identidad_ambigua"] = out["identidad_ambigua"].astype(int)
    return out[["id_cliente_anon", "codigo_display", "fecha_creacion_declarada", "identidad_ambigua"]]


def preparar_dim_servicio(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame({
        "id_servicio": df["ID"],
        "nombre": df["Nombre"],
        "categoria": df["Categoría de servicio"],
        "precio": df["Precio"],
        "duracion_minutos": df["Duración"],
        "servicio_grupal": si_no_a_bool(df["Servicio Grupal"]),
        "capacidad_grupo": df["Capacidad de grupo"],
        "servicio_a_domicilio": si_no_a_bool(df["Servicio a domicilio"]),
        "reservar_online": si_no_a_bool(df["Reservar online"]),
    })
    return out


def preparar_fact_ventas(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame({
        "id_venta": df["id_venta"],
        "clave_venta": df["clave_venta"],
        "clave_venta_origen": df["clave_venta_origen"],
        "id_cliente_anon": df["id_cliente_anon"],
        "identidad_ambigua_transaccional": df["identidad_ambigua_transaccional"].astype(int),
        "fecha": fecha_a_texto(df["fecha"]),
        "monto_venta": df["monto_venta"],
        "monto_a_pagar": df["monto_a_pagar"],
        "monto_pendiente": df["monto_pendiente"],
        "ids_venta_originales": df["ids_venta_originales"],
        "n_ventas_fusionadas": df["n_ventas_fusionadas"],
    })
    return out


def preparar_fact_items(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame({
        "clave_venta": df["clave_venta"],
        "tipo_item": df["Tipo item"],
        "categoria": df["Categoría"],
        "nombre_item": df["Nombre item"],
        "cantidad": df["Cantidad"],
        "precio_unitario": df["Precio unitario"],
        "descuento": df["Descuento"],
        "total": df["Total"],
        "prestador": df["Prestador"],
        "fecha_venta": fecha_a_texto(df["fecha_venta"]),
        "fecha_reserva": fecha_a_texto(df["fecha_reserva"]),
    })
    return out


def preparar_fact_transacciones(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame({
        "id_transaccion": range(1, len(df) + 1),  # el 'ID' original no viaja: no aporta y evita choques
        "clave_venta": df["clave_venta"],
        "fecha": fecha_a_texto(df["fecha"]),
        "monto": df["Monto"],
        "propina": df["Propina"],
        "metodo_pago": df["Método de Pago"],
    })
    return out


def preparar_fact_reservas(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame({
        "id_cliente_anon": df["id_cliente_anon"],
        "fecha_realizacion": fecha_a_texto(df["fecha_realizacion"]),
        "fecha_creacion": fecha_a_texto(df["fecha_creacion"]),
        "servicio_texto": df["Servicio"],
        "precio_lista": df["Precio lista"],
        "precio_real": df["Precio real"],
        "prestador": df["Prestador"],
        "estado": df["Estado"],
        "estado_pago": df["Estado de pago"],
        "fecha_pago": fecha_a_texto(df["fecha_pago"]),
        "origen": df["Origen"],
        "preferencia_cliente": df["Preferencia Cliente"],
    })
    return out


# ---------------------------------------------------------------------------
# Verificación de PII por contenido (lección del paso 4: no basta con
# revisar nombres de columna)
# ---------------------------------------------------------------------------

def verificar_sin_pii(conn: sqlite3.Connection, nombres_reales_norm: set) -> list:
    """Recorre TODAS las columnas de texto de TODAS las tablas y compara su
    contenido contra la lista de nombres normalizados de clientas reales.
    Devuelve una lista de hallazgos (vacía si no hay fuga)."""
    hallazgos = []
    tablas = [r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()]

    for tabla in tablas:
        columnas = conn.execute(f"PRAGMA table_info({tabla})").fetchall()
        columnas_texto = [c[1] for c in columnas if c[2].upper() == "TEXT"]
        for col in columnas_texto:
            valores = pd.read_sql(f'SELECT DISTINCT "{col}" AS v FROM {tabla}', conn)["v"]
            valores_norm = set(valores.dropna().astype(str).str.lower())
            interseccion = valores_norm & nombres_reales_norm
            if interseccion:
                hallazgos.append((tabla, col, list(interseccion)[:5]))
    return hallazgos


# ---------------------------------------------------------------------------
# Orquestación
# ---------------------------------------------------------------------------

def construir_warehouse(processed_dir: Path, dim_cliente_anon_path: Path, db_path: Path,
                         nombres_reales_norm: set | None = None) -> dict:
    dim_cliente_anon = preparar_dim_cliente_anon(pd.read_parquet(dim_cliente_anon_path))
    dim_servicio = preparar_dim_servicio(pd.read_parquet(processed_dir / "servicios_clean.parquet"))
    fact_ventas = preparar_fact_ventas(pd.read_parquet(processed_dir / "ventas_clean.parquet"))
    fact_items = preparar_fact_items(pd.read_parquet(processed_dir / "items_clean.parquet"))
    fact_transacciones = preparar_fact_transacciones(pd.read_parquet(processed_dir / "transacciones_clean.parquet"))
    fact_reservas = preparar_fact_reservas(pd.read_parquet(processed_dir / "reservas_clean.parquet"))

    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()  # recompilar desde cero: reproducible, no acumula estado

    conn = sqlite3.connect(db_path)
    conn.executescript(DDL)

    # Orden de carga: dimensiones primero, luego fact_ventas (de la que
    # dependen items y transacciones por FK), luego el resto.
    dim_cliente_anon.to_sql("dim_cliente_anon", conn, if_exists="append", index=False)
    dim_servicio.to_sql("dim_servicio", conn, if_exists="append", index=False)
    fact_ventas.to_sql("fact_ventas", conn, if_exists="append", index=False)
    fact_items.to_sql("fact_items", conn, if_exists="append", index=False)
    fact_transacciones.to_sql("fact_transacciones", conn, if_exists="append", index=False)
    fact_reservas.to_sql("fact_reservas", conn, if_exists="append", index=False)
    conn.commit()

    # -------- Verificaciones de integridad --------
    fk_check = conn.execute("PRAGMA foreign_key_check").fetchall()

    huerfanos_dim_cliente = conn.execute("""
        SELECT COUNT(*) FROM dim_cliente_anon d
        WHERE NOT EXISTS (SELECT 1 FROM fact_ventas v WHERE v.id_cliente_anon = d.id_cliente_anon)
    """).fetchone()[0]

    reporte = {
        "dim_cliente_anon_filas": conn.execute("SELECT COUNT(*) FROM dim_cliente_anon").fetchone()[0],
        "dim_servicio_filas": conn.execute("SELECT COUNT(*) FROM dim_servicio").fetchone()[0],
        "fact_ventas_filas": conn.execute("SELECT COUNT(*) FROM fact_ventas").fetchone()[0],
        "fact_items_filas": conn.execute("SELECT COUNT(*) FROM fact_items").fetchone()[0],
        "fact_transacciones_filas": conn.execute("SELECT COUNT(*) FROM fact_transacciones").fetchone()[0],
        "fact_reservas_filas": conn.execute("SELECT COUNT(*) FROM fact_reservas").fetchone()[0],
        "violaciones_fk": len(fk_check),
        "dim_cliente_anon_huerfanos_sin_venta": huerfanos_dim_cliente,
    }

    if nombres_reales_norm:
        hallazgos_pii = verificar_sin_pii(conn, nombres_reales_norm)
        reporte["hallazgos_pii"] = hallazgos_pii

    conn.close()
    return reporte


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--processed-dir", type=Path, required=True)
    parser.add_argument("--dim-cliente-anon-path", type=Path, required=True)
    parser.add_argument("--db-path", type=Path, required=True)
    args = parser.parse_args()

    reporte = construir_warehouse(args.processed_dir, args.dim_cliente_anon_path, args.db_path)

    print("=== Reporte de construcción del warehouse ===")
    for k, v in reporte.items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()