"""
resolve_identity.py
====================

Paso 3 del roadmap: Resolución de identidad + anonimización.

Construye:
  1. Una tabla puente LOCAL (contiene datos personales; NUNCA se versiona en git)
     que mapea nombre/email/teléfono -> id_cliente_anon.
  2. Una tabla `dim_cliente_anon` SEGURA (sin datos personales) que sí puede
     entrar al warehouse y a la capa gold.

Reglas aplicadas (ver docs/entregas/07_resolucion_identidad.md y
docs/architecture/contrato_analitico.md):

  - Solo se considera "clienta real" a quien aparece al menos una vez como
    comprador en ventas.xlsx o items.xlsx (evita anonimizar contactos
    informales de clientes.xlsx que nunca compraron).
  - La identidad se resuelve por nombre normalizado, desambiguado por
    teléfono (prioridad 1, 96.4% de completitud) y email (prioridad 2,
    75.1% de completitud) cuando hay más de un registro con el mismo nombre.
  - id_cliente_anon es un hash largo (colisión práicamente imposible),
    NUNCA el código de 4 dígitos que se muestra en el dashboard.
  - codigo_display es un código de 4 dígitos SOLO para mostrar en pantalla
    (estilo "#8491" del mockup); se resuelve cualquier colisión de forma
    determinista para que sea único dentro del dataset, pero nunca se usa
    como clave de unión real.

Uso:
    python resolve_identity.py \
        --raw-dir /data/raw \
        --out-local /data/local/id_bridge_local.parquet \
        --out-safe /data/warehouse/dim_cliente_anon.parquet
"""

import argparse
import hashlib
import re
import unicodedata
from pathlib import Path

import pandas as pd
import os

SALT = os.getenv("ID_SALT")


# ---------------------------------------------------------------------------
# Normalización
# ---------------------------------------------------------------------------

def normalizar_nombre(s: str) -> str:
    """minúsculas, sin acentos, espacios colapsados, sin espacios en extremos."""
    if pd.isna(s):
        return ""
    s = str(s).strip().lower()
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("utf-8")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def normalizar_telefono(s) -> str:
    if pd.isna(s):
        return ""
    digitos = re.sub(r"\D", "", str(s))
    return digitos


def normalizar_email(s) -> str:
    if pd.isna(s):
        return ""
    return str(s).strip().lower()


# ---------------------------------------------------------------------------
# Carga
# ---------------------------------------------------------------------------

def cargar_fuentes(raw_dir: Path):
    clientes = pd.read_excel(raw_dir / "clientes.xlsx")
    ventas = pd.read_excel(raw_dir / "ventas.xlsx")
    items = pd.read_excel(raw_dir / "items.xlsx")
    return clientes, ventas, items


# ---------------------------------------------------------------------------
# Paso 1: universo de "clientas reales" (compraron al menos una vez)
# ---------------------------------------------------------------------------

def construir_universo_clientas_reales(ventas: pd.DataFrame, items: pd.DataFrame) -> set:
    nombres_ventas = ventas["Cliente"].map(normalizar_nombre)
    nombres_items = items["Cliente"].map(normalizar_nombre)
    universo = set(nombres_ventas) | set(nombres_items)
    universo.discard("")
    return universo


# ---------------------------------------------------------------------------
# Paso 2: candidatos de identidad desde clientes.xlsx
# ---------------------------------------------------------------------------

def construir_candidatos(clientes: pd.DataFrame) -> pd.DataFrame:
    df = clientes.copy()
    df["nombre_norm"] = (
        df["Nombres"].fillna("").astype(str).str.strip()
        + " "
        + df["Apellidos"].fillna("").astype(str).str.strip()
    ).map(normalizar_nombre)
    df["email_norm"] = df["Email"].map(normalizar_email)
    df["telefono_norm"] = df["Teléfono"].map(normalizar_telefono)
    df["fecha_creacion"] = pd.to_datetime(df["Fecha de creación."], dayfirst=True, errors="coerce")
    return df[["nombre_norm", "email_norm", "telefono_norm", "fecha_creacion"]]


# ---------------------------------------------------------------------------
# Paso 3: deduplicación / desambiguación dentro de cada nombre normalizado
# ---------------------------------------------------------------------------

def resolver_grupo(nombre_norm: str, grupo: pd.DataFrame) -> list[dict]:
    """
    Devuelve una lista de identidades resueltas para un mismo nombre
    normalizado. Normalmente será una sola identidad; puede haber más de
    una si el teléfono o el email difieren claramente entre registros
    (indicio de personas distintas con el mismo nombre).
    """
    grupo = grupo.copy()

    # Sub-agrupar por teléfono cuando existe (señal más confiable: 96.4% completa)
    con_telefono = grupo[grupo["telefono_norm"] != ""]
    sin_telefono = grupo[grupo["telefono_norm"] == ""]

    identidades = []
    ambiguo = len(grupo) > 1

    if not con_telefono.empty:
        for telefono, sub in con_telefono.groupby("telefono_norm"):
            emails = [e for e in sub["email_norm"].unique() if e]
            identidades.append(
                {
                    "nombre_norm": nombre_norm,
                    "telefono_norm": telefono,
                    "email_norm": emails[0] if emails else "",
                    "fecha_creacion": sub["fecha_creacion"].min(),
                    "n_registros_clientes_xlsx": len(sub),
                    "identidad_ambigua": ambiguo,
                }
            )
    if not sin_telefono.empty:
        # sin teléfono: si hay email, sub-agrupar por email; si no hay nada,
        # se colapsan en una única identidad "residual" (no hay forma de
        # distinguir personas distintas sin ninguna señal).
        con_email = sin_telefono[sin_telefono["email_norm"] != ""]
        sin_nada = sin_telefono[sin_telefono["email_norm"] == ""]

        for email, sub in con_email.groupby("email_norm"):
            identidades.append(
                {
                    "nombre_norm": nombre_norm,
                    "telefono_norm": "",
                    "email_norm": email,
                    "fecha_creacion": sub["fecha_creacion"].min(),
                    "n_registros_clientes_xlsx": len(sub),
                    "identidad_ambigua": ambiguo,
                }
            )
        if not sin_nada.empty:
            identidades.append(
                {
                    "nombre_norm": nombre_norm,
                    "telefono_norm": "",
                    "email_norm": "",
                    "fecha_creacion": sin_nada["fecha_creacion"].min(),
                    "n_registros_clientes_xlsx": len(sin_nada),
                    "identidad_ambigua": ambiguo,
                }
            )

    if not identidades:
        # nombre real (compró) que no aparece en clientes.xlsx: identidad
        # mínima solo con el nombre.
        identidades.append(
            {
                "nombre_norm": nombre_norm,
                "telefono_norm": "",
                "email_norm": "",
                "fecha_creacion": pd.NaT,
                "n_registros_clientes_xlsx": 0,
                "identidad_ambigua": False,
            }
        )

    return identidades


def resolver_identidades(universo_real: set, candidatos: pd.DataFrame) -> pd.DataFrame:
    filas = []
    candidatos_por_nombre = {
        nombre: grupo for nombre, grupo in candidatos.groupby("nombre_norm")
    }

    for nombre in sorted(universo_real):
        grupo = candidatos_por_nombre.get(nombre, candidatos.iloc[0:0])
        filas.extend(resolver_grupo(nombre, grupo))

    return pd.DataFrame(filas)


# ---------------------------------------------------------------------------
# Paso 4: generación de identificadores
# ---------------------------------------------------------------------------

def generar_id_cliente_anon(row: pd.Series) -> str:
    """Hash largo, clave real de unión. Prácticamente libre de colisiones."""
    clave = f"{SALT}|{row['nombre_norm']}|{row['telefono_norm']}|{row['email_norm']}"
    return hashlib.sha256(clave.encode("utf-8")).hexdigest()[:16]


def generar_codigo_display(df: pd.DataFrame) -> pd.Series:
    """
    Código de 4 dígitos SOLO para UI (estilo '#8491' del mockup).
    Determinista a partir de id_cliente_anon; si colisiona dentro del
    dataset actual, se resuelve incrementando de forma reproducible.
    NUNCA se usa como clave de unión.
    """
    base = df["id_cliente_anon"].map(
        lambda h: int(h, 16) % 9000 + 1000
    )
    usados = set()
    codigos = []
    for val in base:
        candidato = val
        while candidato in usados:
            candidato = 1000 + (candidato - 1000 + 1) % 9000
        usados.add(candidato)
        codigos.append(candidato)
    return pd.Series(codigos, index=df.index)


# ---------------------------------------------------------------------------
# Orquestación
# ---------------------------------------------------------------------------

def construir_tablas(raw_dir: Path):
    clientes, ventas, items = cargar_fuentes(raw_dir)

    universo_real = construir_universo_clientas_reales(ventas, items)
    candidatos = construir_candidatos(clientes)
    resueltas = resolver_identidades(universo_real, candidatos)

    resueltas["id_cliente_anon"] = resueltas.apply(generar_id_cliente_anon, axis=1)
    resueltas["codigo_display"] = generar_codigo_display(resueltas)

    # Tabla puente LOCAL (contiene nombre/telefono/email -> NO versionar)
    bridge_local = resueltas[
        [
            "id_cliente_anon",
            "codigo_display",
            "nombre_norm",
            "telefono_norm",
            "email_norm",
            "fecha_creacion",
            "n_registros_clientes_xlsx",
            "identidad_ambigua",
        ]
    ].rename(columns={"fecha_creacion": "fecha_creacion_declarada"})

    # Tabla SEGURA (sin PII) -> esta sí entra al warehouse / gold
    dim_cliente_anon = resueltas[
        ["id_cliente_anon", "codigo_display", "fecha_creacion", "identidad_ambigua"]
    ].rename(columns={"fecha_creacion": "fecha_creacion_declarada"})

    return bridge_local, dim_cliente_anon, universo_real


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", type=Path, required=True)
    parser.add_argument("--out-local", type=Path, required=True)
    parser.add_argument("--out-safe", type=Path, required=True)
    args = parser.parse_args()

    bridge_local, dim_cliente_anon, universo_real = construir_tablas(args.raw_dir)

    args.out_local.parent.mkdir(parents=True, exist_ok=True)
    args.out_safe.parent.mkdir(parents=True, exist_ok=True)

    bridge_local.to_parquet(args.out_local, index=False)
    dim_cliente_anon.to_parquet(args.out_safe, index=False)

    print(f"Clientas reales (compraron al menos una vez): {len(universo_real)}")
    print(f"Identidades resueltas (dim_cliente_anon):      {len(dim_cliente_anon)}")
    print(f"Identidades marcadas como ambiguas:             {int(dim_cliente_anon['identidad_ambigua'].sum())}")
    print(f"Tabla puente LOCAL guardada en:  {args.out_local}")
    print(f"Tabla segura guardada en:        {args.out_safe}")


if __name__ == "__main__":
    main()