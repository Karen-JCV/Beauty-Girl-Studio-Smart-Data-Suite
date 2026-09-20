"""
build_features.py
===================

Paso 8 del roadmap: feature engineering.

Consume:
  - data/gold/gold_cliente_snapshot.parquet

Produce:
  - data/gold/gold_cliente_snapshot.parquet actualizado in place con una
    columna `split` (train / val / test / None), tal como especifica el
    contrato del dataset gold.
  - data/gold/model_input.parquet: la misma información ya codificada
    (one-hot para categóricas, booleanas a 0/1), lista para entrenar sin
    transformaciones adicionales en el paso 9.

Reglas aplicadas (ver docs/entregas/12_feature_engineering.md):

  - Se excluye el corte 2023-03-31 (n=3): ruido estadístico detectado en
    el EDA (paso 7), no una fecha de referencia útil para entrenar.
  - Solo entran a train/val/test los snapshots con horizonte_completo =
    True. Los snapshots sin horizonte completo (el corte "actual" de
    producción) quedan con split = None: no se usan para entrenar/validar/
    testear, pero siguen disponibles en la tabla para el scoring en vivo
    del dashboard.
  - Margen de 90 días verificado programáticamente entre el último corte
    de cada split y el primero del siguiente (contrato analítico §5) --
    si algún cambio futuro en los cortes rompe el margen, el script falla
    en vez de generar un split contaminado en silencio.
  - Solo se usan las variables permitidas por el contrato analítico §4.
    `prestador_habitual` y `origen_reserva` no entran aunque existan en
    upstream, porque no están en la lista de variables permitidas.
"""

import argparse
from pathlib import Path

import pandas as pd

HORIZONTE_DIAS = 90
MARGEN_MINIMO_DIAS = 90

CORTE_EXCLUIDO = [pd.Timestamp("2023-03-31")]  # n=3, ruido -- ver docs/entregas/11_eda.md §1

CORTES_TRAIN = [
    "2023-06-30", "2023-09-30", "2023-12-31", "2024-03-31",
    "2024-06-30", "2024-09-30", "2024-12-31", "2025-03-31",
]
CORTES_VAL = ["2025-06-30", "2025-09-30"]
CORTES_TEST = ["2025-12-31", "2026-03-31"]

VARIABLES_NUMERICAS = [
    "recency_dias", "frequency_visitas", "monetary_total", "ticket_medio", "antiguedad_dias",
]
VARIABLES_CATEGORICAS = ["categoria_favorita", "segmento_rfm"]
VARIABLE_BOOLEANA = "usa_promociones"
VARIABLE_OBJETIVO = "retorna_en_90_dias"


# ---------------------------------------------------------------------------
# Asignación de split y validación de márgenes
# ---------------------------------------------------------------------------

def asignar_split(df: pd.DataFrame) -> pd.Series:
    cortes_train = pd.to_datetime(CORTES_TRAIN)
    cortes_val = pd.to_datetime(CORTES_VAL)
    cortes_test = pd.to_datetime(CORTES_TEST)

    split = pd.Series(pd.NA, index=df.index, dtype="object")
    split[df["fecha_referencia"].isin(cortes_train)] = "train"
    split[df["fecha_referencia"].isin(cortes_val)] = "val"
    split[df["fecha_referencia"].isin(cortes_test)] = "test"

    # snapshots sin horizonte completo o del corte excluido -> nunca entran
    # a train/val/test, aunque coincidan por error con alguna fecha de la lista
    no_usable = (~df["horizonte_completo"]) | (df["fecha_referencia"].isin(pd.to_datetime(CORTE_EXCLUIDO)))
    split[no_usable] = pd.NA

    return split


def validar_margen_temporal():
    """Falla en seco si el margen entre splits es menor al mínimo exigido
    por el contrato analítico (§5) -- en vez de permitir un split
    contaminado por solapamiento de ventanas de etiqueta."""
    ultimo_train = pd.to_datetime(CORTES_TRAIN).max()
    primero_val = pd.to_datetime(CORTES_VAL).min()
    ultimo_val = pd.to_datetime(CORTES_VAL).max()
    primero_test = pd.to_datetime(CORTES_TEST).min()

    margen_train_val = (primero_val - ultimo_train).days
    margen_val_test = (primero_test - ultimo_val).days

    if margen_train_val < MARGEN_MINIMO_DIAS:
        raise ValueError(
            f"Margen train->val es {margen_train_val} días, menor al mínimo "
            f"de {MARGEN_MINIMO_DIAS} exigido por el contrato analítico §5."
        )
    if margen_val_test < MARGEN_MINIMO_DIAS:
        raise ValueError(
            f"Margen val->test es {margen_val_test} días, menor al mínimo "
            f"de {MARGEN_MINIMO_DIAS} exigido por el contrato analítico §5."
        )
    return margen_train_val, margen_val_test


# ---------------------------------------------------------------------------
# Codificación de variables
# ---------------------------------------------------------------------------

def construir_model_input(df: pd.DataFrame) -> pd.DataFrame:
    base = df[
        ["id_cliente_anon", "fecha_referencia", "split", "horizonte_completo", VARIABLE_OBJETIVO]
        + VARIABLES_NUMERICAS
        + [VARIABLE_BOOLEANA]
    ].copy()

    base[VARIABLE_BOOLEANA] = base[VARIABLE_BOOLEANA].astype("boolean").astype("Int64")
    base[VARIABLE_OBJETIVO] = base[VARIABLE_OBJETIVO].astype("boolean").astype("Int64")

    dummies = pd.get_dummies(
        df[VARIABLES_CATEGORICAS], prefix=VARIABLES_CATEGORICAS, dtype=int
    )

    return pd.concat([base, dummies], axis=1)


# ---------------------------------------------------------------------------
# Orquestación
# ---------------------------------------------------------------------------

def ejecutar(gold_dir: Path) -> dict:
    margen_train_val, margen_val_test = validar_margen_temporal()

    ruta_snapshot = gold_dir / "gold_cliente_snapshot.parquet"
    snapshot = pd.read_parquet(ruta_snapshot)
    snapshot["split"] = asignar_split(snapshot)
    snapshot.to_parquet(ruta_snapshot, index=False)  # actualiza la capa gold in place

    model_input = construir_model_input(snapshot)
    model_input.to_parquet(gold_dir / "model_input.parquet", index=False)

    resumen_splits = (
        model_input[model_input["split"].notna()]
        .groupby("split")
        .agg(n=(VARIABLE_OBJETIVO, "size"), tasa_retorno=(VARIABLE_OBJETIVO, "mean"))
        .reindex(["train", "val", "test"])
    )

    return {
        "margen_train_val_dias": margen_train_val,
        "margen_val_test_dias": margen_val_test,
        "n_columnas_model_input": model_input.shape[1],
        "columnas_dummy_generadas": [c for c in model_input.columns
                                      if any(c.startswith(p + "_") for p in VARIABLES_CATEGORICAS)],
        "resumen_splits": resumen_splits,
        "n_sin_split_produccion": int(model_input["split"].isna().sum()),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gold-dir", type=Path, required=True)
    args = parser.parse_args()

    reporte = ejecutar(args.gold_dir)

    print("=== Reporte de feature engineering ===")
    print(f"Margen train->val: {reporte['margen_train_val_dias']} días")
    print(f"Margen val->test:  {reporte['margen_val_test_dias']} días")
    print(f"Columnas en model_input: {reporte['n_columnas_model_input']}")
    print(f"Dummies generadas: {reporte['columnas_dummy_generadas']}")
    print()
    print("Resumen por split:")
    print(reporte["resumen_splits"])
    print()
    print(f"Filas sin split (producción / excluidas): {reporte['n_sin_split_produccion']}")


if __name__ == "__main__":
    main()