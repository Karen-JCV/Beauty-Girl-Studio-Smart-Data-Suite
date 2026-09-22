"""
score_clientas.py
===================

Paso 11 (parte 1): aplica el modelo persistido al snapshot MÁS RECIENTE
de gold_cliente_snapshot (horizonte_completo = False -- la clienta "de
hoy", la que el dashboard necesita mostrar) y produce la tabla que
consume el dashboard.

Consume:
  - models/rf_calibrado.joblib, models/rf_base.joblib, models/model_meta.json
  - data/gold/gold_cliente_snapshot.parquet, data/gold/model_input.parquet
  - data/warehouse/dim_cliente_anon.parquet (para codigo_display -- el
    dashboard NUNCA muestra id_cliente_anon crudo, ver Entrega 07 §1)
  - data/gold/gold_visitas.parquet (para el histórico de visitas del panel
    de detalle)

Produce:
  - data/gold/scoring_actual.parquet: una fila por clienta activa, con
    prob_retorno_90d, score_riesgo, banda_riesgo, prediccion y los 3
    factores del modelo más influyentes (SHAP), lista para que el
    dashboard solo tenga que leer y filtrar -- sin tocar el modelo.

Nota de explicabilidad (contrato analítico §3): los factores se calculan
con SHAP sobre el Random Forest SIN calibrar (rf_base). La calibración
sigmoid reescala la probabilidad de forma monótona, no cambia qué
variables pesan más en cada árbol -- por eso explicar con el modelo base
es válido y evita la complejidad de propagar SHAP a través de la
calibración.
"""

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import shap

NOMBRES_LEGIBLES = {
    "recency_dias": "días desde la última visita",
    "frequency_visitas": "número de visitas",
    "monetary_total": "gasto acumulado",
    "ticket_medio": "ticket medio",
    "antiguedad_dias": "antigüedad como clienta",
    "usa_promociones": "uso de promociones",
}


def cargar_artefactos(models_dir: Path):
    modelo_calibrado = joblib.load(models_dir / "rf_calibrado.joblib")
    rf_base = joblib.load(models_dir / "rf_base.joblib")
    with open(models_dir / "model_meta.json", encoding="utf-8") as f:
        meta = json.load(f)
    return modelo_calibrado, rf_base, meta


def describir_factor(feature: str, shap_val: float, valor_cliente, mediana_global: float) -> str:
    """Traduce (feature, shap_value) a una frase legible tipo mockup:
    'Recency alto -> Muy influyente'. El signo de shap_val ya indica si
    esa variable empujó la predicción hacia MÁS o MENOS riesgo de no
    retorno para esta clienta en particular."""
    empuja_riesgo = shap_val < 0  # shap negativo en prob_retorno -> más riesgo de NO retornar

    if feature.startswith("categoria_favorita_"):
        cat = feature.replace("categoria_favorita_", "")
        direccion = "categoría de riesgo" if empuja_riesgo else "categoría favorable"
        return f"Categoría favorita ({cat}) → {direccion}"
    if feature.startswith("segmento_rfm_"):
        seg = feature.replace("segmento_rfm_", "")
        return f"Segmento RFM ({seg}) → {'de riesgo' if empuja_riesgo else 'favorable'}"

    nombre = NOMBRES_LEGIBLES.get(feature, feature)
    if feature in ("recency_dias", "antiguedad_dias"):
        nivel = "alto" if valor_cliente > mediana_global else "bajo"
    else:
        nivel = "bajo" if valor_cliente < mediana_global else "alto"

    return f"{nombre.capitalize()} {nivel} → {'influyente (riesgo)' if empuja_riesgo else 'influyente (favorable)'}"


def calcular_factores(rf_base, X: pd.DataFrame, feature_cols: list, medianas: pd.Series, top_n=3) -> list:
    explainer = shap.TreeExplainer(rf_base)
    shap_values = explainer.shap_values(X[feature_cols])

    # shap_values puede venir como lista [clase0, clase1] o array 3D según
    # versión; nos quedamos con la contribución a la clase "retorna" (1)
    if isinstance(shap_values, list):
        valores_clase1 = shap_values[1]
    elif shap_values.ndim == 3:
        valores_clase1 = shap_values[:, :, 1]
    else:
        valores_clase1 = shap_values

    factores_por_fila = []
    for i in range(len(X)):
        contribuciones = valores_clase1[i]
        orden = np.argsort(-np.abs(contribuciones))[:top_n]
        frases = [
            describir_factor(feature_cols[j], contribuciones[j], X.iloc[i][feature_cols[j]], medianas[feature_cols[j]])
            for j in orden
        ]
        factores_por_fila.append(frases)
    return factores_por_fila


def ejecutar(gold_dir: Path, warehouse_db_dim_path: Path, models_dir: Path) -> pd.DataFrame:
    modelo_calibrado, rf_base, meta = cargar_artefactos(models_dir)
    feature_cols = meta["feature_cols"]

    snapshot = pd.read_parquet(gold_dir / "gold_cliente_snapshot.parquet")
    model_input = pd.read_parquet(gold_dir / "model_input.parquet")
    dim_cliente_anon = pd.read_parquet(warehouse_db_dim_path)

    actual = model_input[model_input["horizonte_completo"] == False].copy()  # noqa: E712
    fecha_actual = actual["fecha_referencia"].max()
    actual = actual[actual["fecha_referencia"] == fecha_actual].reset_index(drop=True)

    X = actual[feature_cols]
    proba_retorno = modelo_calibrado.predict_proba(X)[:, 1]
    score_riesgo = (1 - proba_retorno) * 100
    prediccion = (proba_retorno >= meta["umbral_decision"]).astype(int)

    def banda(s):
        if s >= meta["umbral_alto"]:
            return "Alto"
        if s <= meta["umbral_bajo"]:
            return "Bajo"
        return "Medio"

    medianas = X[["recency_dias", "frequency_visitas", "monetary_total", "ticket_medio", "antiguedad_dias"]].median()
    medianas_completas = pd.Series({c: medianas.get(c, 0.5) for c in feature_cols})
    factores = calcular_factores(rf_base, X, feature_cols, medianas_completas)

    resultado = actual[["id_cliente_anon", "fecha_referencia", "recency_dias", "frequency_visitas",
                         "monetary_total", "ticket_medio", "antiguedad_dias", "usa_promociones"]].copy()

    # categoria_favorita, segmento_rfm y prestador_habitual NO viajan en
    # model_input (paso 8: excluidas a propósito de las features del
    # modelo). Se recuperan aquí desde gold_cliente_snapshot, que sí las
    # conserva -- evita tener que tocar build_features.py o reentrenar.
    contexto = snapshot[snapshot["fecha_referencia"] == fecha_actual][
        ["id_cliente_anon", "categoria_favorita", "segmento_rfm", "prestador_habitual"]
    ]
    resultado = resultado.merge(contexto, on="id_cliente_anon", how="left")

    resultado["prob_retorno_90d"] = proba_retorno.round(3)
    resultado["score_riesgo"] = score_riesgo.round(1)
    resultado["banda_riesgo"] = [banda(s) for s in score_riesgo]
    resultado["prediccion"] = prediccion
    resultado["factor_1"] = [f[0] if len(f) > 0 else "" for f in factores]
    resultado["factor_2"] = [f[1] if len(f) > 1 else "" for f in factores]
    resultado["factor_3"] = [f[2] if len(f) > 2 else "" for f in factores]

    resultado = resultado.merge(
        dim_cliente_anon[["id_cliente_anon", "codigo_display"]], on="id_cliente_anon", how="left"
    )

    resultado = resultado.sort_values("score_riesgo", ascending=False).reset_index(drop=True)
    return resultado


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gold-dir", type=Path, required=True)
    parser.add_argument("--dim-cliente-anon-path", type=Path, required=True)
    parser.add_argument("--models-dir", type=Path, required=True)
    parser.add_argument("--out-path", type=Path, required=True)
    args = parser.parse_args()

    resultado = ejecutar(args.gold_dir, args.dim_cliente_anon_path, args.models_dir)
    args.out_path.parent.mkdir(parents=True, exist_ok=True)
    resultado.to_parquet(args.out_path, index=False)

    print(f"=== Scoring de producción generado: {len(resultado)} clientas ===")
    print(f"fecha_referencia: {resultado['fecha_referencia'].iloc[0].date()}")
    print()
    print("Distribución de bandas:")
    print(resultado["banda_riesgo"].value_counts())
    print()
    print("Top 5 mayor riesgo:")
    print(resultado[["codigo_display", "score_riesgo", "banda_riesgo", "factor_1"]].head(5).to_string(index=False))


if __name__ == "__main__":
    main()