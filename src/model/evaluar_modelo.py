"""
evaluar_modelo.py
===================

Paso 10 del roadmap: validación, análisis de errores y fijación de los
umbrales definitivos de banda_riesgo.

Reutiliza el entrenamiento de src/model/train_model.py (Random Forest
calibrado, seleccionado en el paso 9) para no duplicar la lógica de
entrenamiento -- este script se centra en analizar sus resultados, no en
volver a decidir qué modelo usar.

Produce:
  - Matriz de confusión y casos de error en test
  - Rendimiento desagregado por segmento_rfm y categoria_favorita
  - Umbrales definitivos de banda_riesgo (reemplazan los provisionales
    40/70 del contrato analítico §7), justificados con la tasa real de
    no-retorno observada por decil de score_riesgo en test
  - Una vista previa del ranking de riesgo sobre el snapshot de
    producción más reciente (horizonte_completo = False), como
    demostración de extremo a extremo antes de conectar el dashboard
"""

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import confusion_matrix

sys.path.insert(0, str(Path(__file__).parent))
from train_model import (
    ID_COLS, TARGET, cargar_splits, elegir_umbral_optimo,
    entrenar_random_forest,
)


# ---------------------------------------------------------------------------
# Reentrenamiento del modelo seleccionado (Random Forest calibrado)
# ---------------------------------------------------------------------------

def entrenar_modelo_final(gold_dir: Path):
    splits, feature_cols = cargar_splits(gold_dir)
    X_train, y_train = splits["train"]["X"], splits["train"]["y"]
    X_val, y_val = splits["val"]["X"], splits["val"]["y"]
    X_test, y_test = splits["test"]["X"], splits["test"]["y"]

    rf = entrenar_random_forest(X_train, y_train, feature_cols)
    # cv="prefit": NO reentrenar, solo calibrar sobre val (ver nota en
    # train_model.py junto a esta misma línea)
    rf_calibrado = CalibratedClassifierCV(rf, method="sigmoid", cv="prefit")
    rf_calibrado.fit(X_val[feature_cols], y_val)

    proba_val = rf_calibrado.predict_proba(X_val[feature_cols])[:, 1]
    umbral = elegir_umbral_optimo(y_val, proba_val)

    proba_test = rf_calibrado.predict_proba(X_test[feature_cols])[:, 1]

    return {
        "modelo": rf_calibrado,
        "rf_base": rf,
        "feature_cols": feature_cols,
        "umbral": umbral,
        "splits": splits,
        "proba_test": proba_test,
    }


# ---------------------------------------------------------------------------
# Análisis de errores en test
# ---------------------------------------------------------------------------

def analizar_errores(splits, proba_test, umbral, out_dir: Path):
    X_test, y_test, meta_test = splits["test"]["X"], splits["test"]["y"], splits["test"]["meta"]

    pred_test = (proba_test >= umbral).astype(int)
    score_riesgo = (1 - proba_test) * 100

    resultado = meta_test.copy()
    resultado["y_real"] = y_test.values
    resultado["prob_retorno"] = proba_test
    resultado["score_riesgo"] = score_riesgo
    resultado["prediccion"] = pred_test
    resultado["segmento_rfm"] = X_test["segmento_rfm"].values if "segmento_rfm" in X_test.columns \
        else X_test.filter(like="segmento_rfm_").idxmax(axis=1).str.replace("segmento_rfm_", "")
    resultado["recency_dias"] = X_test["recency_dias"].values
    resultado["frequency_visitas"] = X_test["frequency_visitas"].values

    # matriz de confusión sobre la clase "no retorna" (0 = no retorna = positiva de negocio)
    cm = confusion_matrix(y_test, pred_test, labels=[0, 1])
    tn_no_retorna, fp, fn, tp = cm.ravel()
    # ojo: en sklearn con labels=[0,1], posición (0,0)=verdaderos "0" bien clasificados,
    # (0,1)=falsos "1" (se predijo 1 siendo 0 -> el error que más le cuesta al negocio)

    # Peores errores: clientas que NO retornaron de verdad (y_real=0) pero el
    # modelo les dio score de riesgo BAJO (predijo que sí iban a volver)
    peores_errores = (
        resultado[(resultado["y_real"] == 0) & (resultado["prediccion"] == 1)]
        .sort_values("score_riesgo")
        .head(15)
    )

    return resultado, cm, peores_errores


def graficar_matriz_confusion(cm, out_dir: Path):
    fig, ax = plt.subplots(figsize=(5, 4.5))
    im = ax.imshow(cm, cmap="Blues")
    etiquetas = ["No retorna (0)", "Retorna (1)"]
    ax.set_xticks([0, 1]); ax.set_xticklabels(etiquetas)
    ax.set_yticks([0, 1]); ax.set_yticklabels(etiquetas)
    ax.set_xlabel("Predicción")
    ax.set_ylabel("Real")
    ax.set_title("Matriz de confusión -- test")
    for i in range(2):
        for j in range(2):
            ax.text(j, i, str(cm[i, j]), ha="center", va="center",
                     color="white" if cm[i, j] > cm.max() / 2 else "black", fontsize=13)
    fig.colorbar(im)
    fig.tight_layout()
    fig.savefig(out_dir / "01_matriz_confusion.png", dpi=130)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Rendimiento desagregado
# ---------------------------------------------------------------------------

def rendimiento_por_grupo(resultado: pd.DataFrame, columna: str, min_n: int = 20) -> pd.DataFrame:
    filas = []
    for valor, grupo in resultado.groupby(columna):
        if len(grupo) < min_n:
            continue
        y_real = grupo["y_real"]
        pred = grupo["prediccion"]
        tp0 = ((y_real == 0) & (pred == 0)).sum()
        fn0 = ((y_real == 0) & (pred == 1)).sum()
        fp0 = ((y_real == 1) & (pred == 0)).sum()
        recall0 = tp0 / (tp0 + fn0) if (tp0 + fn0) > 0 else np.nan
        precision0 = tp0 / (tp0 + fp0) if (tp0 + fp0) > 0 else np.nan
        filas.append({
            columna: valor, "n": len(grupo),
            "tasa_no_retorno_real": (y_real == 0).mean(),
            "recall_no_retorna": recall0,
            "precision_no_retorna": precision0,
        })
    return pd.DataFrame(filas).sort_values("n", ascending=False)


# ---------------------------------------------------------------------------
# Umbrales definitivos de banda_riesgo
# ---------------------------------------------------------------------------

def calcular_umbrales_banda_riesgo(resultado: pd.DataFrame, out_dir: Path):
    """
    Los umbrales NO se definen cruzando una tasa absoluta de no-retorno
    (ver docs/entregas/14_validacion_y_umbrales.md §2 para el porqué):
    como "no retorna" ya es la clase mayoritaria del negocio (~75-78%),
    cualquier corte por tasa absoluta captura casi a toda la población en
    "Alto", lo que no sirve para priorizar.

    En su lugar, los umbrales se fijan por PERCENTIL de score_riesgo
    (contrato analítico §7: "distribución real de score_riesgo"),
    dimensionando las bandas a un volumen que la propietaria pueda
    trabajar: Alto = 25% con más riesgo, Bajo = 35% con menos riesgo,
    Medio = el resto. La tasa real de no-retorno dentro de cada banda
    se calcula DESPUÉS, como evidencia de calidad (coste/beneficio) -
    no como la regla que define la banda.
    """
    resultado = resultado.copy()
    resultado["decil"] = pd.qcut(resultado["score_riesgo"], 10, labels=False, duplicates="drop") + 1

    por_decil = resultado.groupby("decil").agg(
        n=("y_real", "size"),
        score_min=("score_riesgo", "min"),
        score_max=("score_riesgo", "max"),
        tasa_no_retorno_real=("y_real", lambda s: (s == 0).mean()),
    )

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(por_decil.index, por_decil["tasa_no_retorno_real"] * 100, color="#e76f51")
    ax.set_xlabel("Decil de score_riesgo (1 = riesgo más bajo, 10 = riesgo más alto)")
    ax.set_ylabel("% que realmente NO retornó")
    ax.set_title("Tasa real de no-retorno por decil de score_riesgo -- test")
    ax.axhline(por_decil["tasa_no_retorno_real"].mean() * 100, color="gray", linestyle="--",
               label="Promedio general (base rate del negocio)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_dir / "02_umbrales_banda_riesgo.png", dpi=130)
    plt.close(fig)

    umbral_alto = resultado["score_riesgo"].quantile(0.75)   # top 25% por volumen
    umbral_bajo = resultado["score_riesgo"].quantile(0.35)   # bottom 35% por volumen

    # Evidencia de calidad de las bandas resultantes (no es la regla, es la
    # justificación de coste/beneficio que pide el contrato §7)
    resultado["banda_preliminar"] = np.select(
        [resultado["score_riesgo"] >= umbral_alto, resultado["score_riesgo"] <= umbral_bajo],
        ["Alto", "Bajo"], default="Medio",
    )
    evidencia_bandas = resultado.groupby("banda_preliminar").agg(
        n=("y_real", "size"),
        tasa_no_retorno_real=("y_real", lambda s: (s == 0).mean()),
    ).reindex(["Bajo", "Medio", "Alto"])

    return por_decil, umbral_bajo, umbral_alto, evidencia_bandas


# ---------------------------------------------------------------------------
# Vista previa de producción (snapshot más reciente, sin horizonte completo)
# ---------------------------------------------------------------------------

def preview_produccion(modelo, feature_cols, gold_dir: Path, umbral_bajo, umbral_alto, n_preview=10):
    snapshot = pd.read_parquet(gold_dir / "gold_cliente_snapshot.parquet")
    model_input = pd.read_parquet(gold_dir / "model_input.parquet")

    actual = model_input[model_input["horizonte_completo"] == False]  # noqa: E712
    fecha_actual = actual["fecha_referencia"].max()
    actual = actual[actual["fecha_referencia"] == fecha_actual]

    X_actual = actual[feature_cols]
    proba = modelo.predict_proba(X_actual)[:, 1]
    score_riesgo = (1 - proba) * 100

    def banda(score):
        if score >= umbral_alto:
            return "Alto"
        if score <= umbral_bajo:
            return "Bajo"
        return "Medio"

    preview = actual[["id_cliente_anon"]].copy()
    preview["fecha_referencia"] = fecha_actual
    preview["prob_retorno_90d"] = proba.round(3)
    preview["score_riesgo"] = score_riesgo.round(1)
    preview["banda_riesgo"] = [banda(s) for s in score_riesgo]
    preview = preview.sort_values("score_riesgo", ascending=False)

    return preview.head(n_preview), fecha_actual, preview["banda_riesgo"].value_counts()


# ---------------------------------------------------------------------------
# Orquestación
# ---------------------------------------------------------------------------

def ejecutar(gold_dir: Path, out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)

    entrenamiento = entrenar_modelo_final(gold_dir)
    resultado, cm, peores_errores = analizar_errores(
        entrenamiento["splits"], entrenamiento["proba_test"], entrenamiento["umbral"], out_dir
    )
    graficar_matriz_confusion(cm, out_dir)

    rendimiento_segmento = rendimiento_por_grupo(resultado, "segmento_rfm")

    por_decil, umbral_bajo, umbral_alto, evidencia_bandas = calcular_umbrales_banda_riesgo(resultado, out_dir)

    preview, fecha_actual, conteo_bandas = preview_produccion(
        entrenamiento["modelo"], entrenamiento["feature_cols"], gold_dir, umbral_bajo, umbral_alto
    )

    return {
        "cm": cm,
        "peores_errores": peores_errores,
        "rendimiento_segmento": rendimiento_segmento,
        "por_decil": por_decil,
        "umbral_bajo": umbral_bajo,
        "umbral_alto": umbral_alto,
        "evidencia_bandas": evidencia_bandas,
        "preview": preview,
        "fecha_actual": fecha_actual,
        "conteo_bandas": conteo_bandas,
        "umbral_decision": entrenamiento["umbral"],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gold-dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()

    pd.set_option("display.width", 160)
    pd.set_option("display.max_columns", None)

    r = ejecutar(args.gold_dir, args.out_dir)

    print("=== Matriz de confusión (test) ===")
    print(r["cm"])
    print()
    print("=== Peores errores (no retornaron de verdad, modelo dijo bajo riesgo) ===")
    print(r["peores_errores"][["id_cliente_anon", "score_riesgo", "recency_dias", "frequency_visitas"]].to_string(index=False))
    print()
    print("=== Rendimiento por segmento RFM ===")
    print(r["rendimiento_segmento"].to_string(index=False))
    print()
    print("=== Tasa real de no-retorno por decil de score_riesgo ===")
    print(r["por_decil"])
    print()
    print(f"Umbrales definitivos -> Bajo: <= {r['umbral_bajo']:.1f}   Alto: >= {r['umbral_alto']:.1f}")
    print()
    print("Evidencia de calidad de las bandas (no es la regla, es el coste/beneficio):")
    print(r["evidencia_bandas"].to_string())
    print()
    print(f"=== Vista previa de producción (fecha_referencia = {r['fecha_actual'].date()}) ===")
    print(r["preview"].to_string(index=False))
    print()
    print("Distribución de bandas en producción:")
    print(r["conteo_bandas"])


if __name__ == "__main__":
    main()