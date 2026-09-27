"""
evaluar_modelo.py
===================

Paso 10 del roadmap: validación, análisis de errores y fijación de los
umbrales definitivos de banda_riesgo.

Reutiliza el entrenamiento de src/model/train_model.py (Random Forest
calibrado, seleccionado en el paso 9) para no duplicar la lógica de
entrenamiento -- este script se centra en analizar sus resultados, no en
volver a decidir qué modelo usar.

Regla de oro de este script: TODO lo que fija un valor -- método de
calibración, umbral de decisión, umbrales de banda_riesgo -- se decide
mirando ÚNICAMENTE train y/o validación. El conjunto de TEST se toca en
un único punto del pipeline, `confirmar_en_test()`, y solo para reportar
cómo se comportan esos valores YA FIJADOS -- nunca para ajustarlos. Antes
de esta corrección, las bandas de riesgo se calculaban directamente sobre
los resultados de test (percentiles de su score_riesgo), lo que
contaminaba ese conjunto como evaluación independiente. Ver
docs/entregas/14_validacion_y_umbrales.md para el detalle completo.

Produce:
  - Umbrales definitivos de banda_riesgo (reemplazan los provisionales
    40/70 del contrato analítico §7), fijados por percentil de
    score_riesgo sobre TRAIN+VAL
  - Matriz de confusión y casos de error, calculados UNA vez sobre test,
    como confirmación final -- no como fuente de ningún umbral
  - Rendimiento desagregado por segmento_rfm (test), incluida una nota
    explícita cuando el segmento es "Campeonas" (menor fiabilidad del
    modelo ahí, ver docs/entregas/14_validacion_y_umbrales.md §3-4)
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
from sklearn.metrics import confusion_matrix

sys.path.insert(0, str(Path(__file__).parent))
from train_model import (
    ID_COLS, TARGET, cargar_splits, elegir_metodo_calibracion,
    elegir_umbral_optimo, entrenar_random_forest,
)

SEGMENTO_MENOR_FIABILIDAD = "Campeonas"
NOTA_MENOR_FIABILIDAD = (
    "Menor fiabilidad: el modelo detecta con menos fiabilidad el no-retorno en este segmento"
    "(recall notablemente inferior al del resto). Tratar la probabilidad"
    "individual con más cautela aquí que en otros segmentos."
)


# ---------------------------------------------------------------------------
# Entrenamiento del modelo seleccionado (Random Forest calibrado)
# ---------------------------------------------------------------------------

def entrenar_modelo_final(gold_dir: Path):
    """Entrena el Random Forest en train, y fija calibración y umbral de
    decisión usando EXCLUSIVAMENTE validación. No toca test en ningún
    momento -- test se usa después, una sola vez, en confirmar_en_test().
    """
    splits, feature_cols = cargar_splits(gold_dir)
    X_train, y_train = splits["train"]["X"], splits["train"]["y"]
    X_val, y_val = splits["val"]["X"], splits["val"]["y"]

    rf = entrenar_random_forest(X_train, y_train, feature_cols)

    metodo_calibracion, diagnostico_calibracion = elegir_metodo_calibracion(rf, X_val, y_val, feature_cols)
    rf_calibrado = diagnostico_calibracion[metodo_calibracion]["modelo"]

    proba_val = rf_calibrado.predict_proba(X_val[feature_cols])[:, 1]
    umbral = elegir_umbral_optimo(y_val, proba_val)

    return {
        "modelo": rf_calibrado,
        "rf_base": rf,
        "feature_cols": feature_cols,
        "umbral": umbral,
        "metodo_calibracion": metodo_calibracion,
        "diagnostico_calibracion": diagnostico_calibracion,
        "splits": splits,
    }


def calcular_score_riesgo(modelo, X: pd.DataFrame, feature_cols: list):
    proba_retorno = modelo.predict_proba(X[feature_cols])[:, 1]
    score_riesgo = (1 - proba_retorno) * 100
    return proba_retorno, score_riesgo


# ---------------------------------------------------------------------------
# Umbrales definitivos de banda_riesgo -- SOLO train+val
# ---------------------------------------------------------------------------

def calcular_umbrales_banda_riesgo(entrenamiento: dict, out_dir: Path):
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
    Medio = el resto.

    IMPORTANTE (corrección Entrega 4): estos percentiles se calculan
    sobre TRAIN+VAL, nunca sobre test. Usar test aquí -- como hacía la
    versión anterior de este script -- convierte a test en un segundo
    conjunto de ajuste, y ya no permite reportar sus métricas como una
    evaluación independiente. La confirmación de cómo se comportan estas
    bandas ya fijadas, sobre test, ocurre por separado en
    confirmar_en_test() y es evidencia de calidad, no la regla que las
    define.
    """
    splits = entrenamiento["splits"]
    modelo = entrenamiento["modelo"]
    feature_cols = entrenamiento["feature_cols"]

    X_trainval = pd.concat([splits["train"]["X"], splits["val"]["X"]], ignore_index=True)
    y_trainval = pd.concat([splits["train"]["y"], splits["val"]["y"]], ignore_index=True)
    _, score_riesgo_trainval = calcular_score_riesgo(modelo, X_trainval, feature_cols)

    resultado = pd.DataFrame({"y_real": y_trainval.values, "score_riesgo": score_riesgo_trainval})
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
    ax.set_title("Tasa real de no-retorno por decil de score_riesgo -- train+val")
    ax.axhline(por_decil["tasa_no_retorno_real"].mean() * 100, color="gray", linestyle="--",
               label="Promedio general (base rate del negocio)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_dir / "02_umbrales_banda_riesgo.png", dpi=130)
    plt.close(fig)

    umbral_alto = float(resultado["score_riesgo"].quantile(0.75))   # top 25% por volumen
    umbral_bajo = float(resultado["score_riesgo"].quantile(0.35))   # bottom 35% por volumen

    return por_decil, umbral_bajo, umbral_alto


# ---------------------------------------------------------------------------
# Confirmación final -- ÚNICO punto del pipeline que toca test, una sola vez
# ---------------------------------------------------------------------------

def confirmar_en_test(entrenamiento: dict, umbral_bajo: float, umbral_alto: float, out_dir: Path):
    """Aplica sobre test, UNA SOLA VEZ, el umbral de decisión y las bandas
    de riesgo ya fijados exclusivamente con train+val. Este es el único
    lugar del pipeline en que test se usa, y es solo para reportar --
    nada de lo calculado aquí retroalimenta ningún parámetro del modelo.
    """
    splits = entrenamiento["splits"]
    modelo = entrenamiento["modelo"]
    feature_cols = entrenamiento["feature_cols"]
    umbral_decision = entrenamiento["umbral"]

    X_test, y_test, meta_test = splits["test"]["X"], splits["test"]["y"], splits["test"]["meta"]
    proba_test, score_riesgo_test = calcular_score_riesgo(modelo, X_test, feature_cols)
    pred_test = (proba_test >= umbral_decision).astype(int)

    resultado = meta_test.copy()
    resultado["y_real"] = y_test.values
    resultado["prob_retorno"] = proba_test
    resultado["score_riesgo"] = score_riesgo_test
    resultado["prediccion"] = pred_test
    resultado["segmento_rfm"] = X_test["segmento_rfm"].values if "segmento_rfm" in X_test.columns \
        else X_test.filter(like="segmento_rfm_").idxmax(axis=1).str.replace("segmento_rfm_", "")
    resultado["recency_dias"] = X_test["recency_dias"].values
    resultado["frequency_visitas"] = X_test["frequency_visitas"].values
    resultado["banda_riesgo"] = np.select(
        [resultado["score_riesgo"] >= umbral_alto, resultado["score_riesgo"] <= umbral_bajo],
        ["Alto", "Bajo"], default="Medio",
    )

    # matriz de confusión sobre la clase "no retorna" (0 = no retorna = positiva de negocio)
    cm = confusion_matrix(y_test, pred_test, labels=[0, 1])
    # ojo: en sklearn con labels=[0,1], posición (0,0)=verdaderos "0" bien clasificados,
    # (0,1)=falsos "1" (se predijo 1 siendo 0 -> el error que más le cuesta al negocio)

    # Peores errores: clientas que NO retornaron de verdad (y_real=0) pero el
    # modelo les dio score de riesgo BAJO (predijo que sí iban a volver)
    peores_errores = (
        resultado[(resultado["y_real"] == 0) & (resultado["prediccion"] == 1)]
        .sort_values("score_riesgo")
        .head(15)
    )

    graficar_matriz_confusion(cm, out_dir)

    rendimiento_segmento = rendimiento_por_grupo(resultado, "segmento_rfm")
    rendimiento_segmento["nota"] = np.where(
        rendimiento_segmento["segmento_rfm"] == SEGMENTO_MENOR_FIABILIDAD,
        NOTA_MENOR_FIABILIDAD, "",
    )

    # Evidencia de calidad de las bandas ya fijadas (confirmación, no la regla)
    evidencia_bandas = resultado.groupby("banda_riesgo").agg(
        n=("y_real", "size"),
        tasa_no_retorno_real=("y_real", lambda s: (s == 0).mean()),
    ).reindex(["Bajo", "Medio", "Alto"])

    return resultado, cm, peores_errores, rendimiento_segmento, evidencia_bandas


def graficar_matriz_confusion(cm, out_dir: Path):
    fig, ax = plt.subplots(figsize=(5, 4.5))
    im = ax.imshow(cm, cmap="Blues")
    etiquetas = ["No retorna (0)", "Retorna (1)"]
    ax.set_xticks([0, 1]); ax.set_xticklabels(etiquetas)
    ax.set_yticks([0, 1]); ax.set_yticklabels(etiquetas)
    ax.set_xlabel("Predicción")
    ax.set_ylabel("Real")
    ax.set_title("Matriz de confusión -- test (confirmación única)")
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
# Vista previa de producción (snapshot más reciente, sin horizonte completo)
# ---------------------------------------------------------------------------

def preview_produccion(modelo, feature_cols, gold_dir: Path, umbral_bajo, umbral_alto, n_preview=10):
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

    # 1) Entrenar y fijar calibración + umbral de decisión -- SOLO train/val
    entrenamiento = entrenar_modelo_final(gold_dir)

    # 2) Fijar bandas de riesgo por percentil -- SOLO train+val
    por_decil, umbral_bajo, umbral_alto = calcular_umbrales_banda_riesgo(entrenamiento, out_dir)

    # 3) Test: UNA sola vez, solo para confirmar lo ya fijado en 1) y 2)
    resultado, cm, peores_errores, rendimiento_segmento, evidencia_bandas = confirmar_en_test(
        entrenamiento, umbral_bajo, umbral_alto, out_dir
    )

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
        "metodo_calibracion": entrenamiento["metodo_calibracion"],
        "diagnostico_calibracion": entrenamiento["diagnostico_calibracion"],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gold-dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()

    pd.set_option("display.width", 160)
    pd.set_option("display.max_columns", None)

    r = ejecutar(args.gold_dir, args.out_dir)

    print("=== Método de calibración elegido (solo con validación) ===")
    for m, d in r["diagnostico_calibracion"].items():
        marca = " <- elegido" if m == r["metodo_calibracion"] else ""
        print(f"  {m}: brier_val={d['brier_val']:.4f}  valores_distintos_val={d['valores_distintos_val']}{marca}")
    print()
    print(f"Umbral de decisión (fijado en val): {r['umbral_decision']:.4f}")
    print()
    print(f"Umbrales de banda de riesgo (fijados en train+val) -> Bajo: <= {r['umbral_bajo']:.1f}   Alto: >= {r['umbral_alto']:.1f}")
    print()
    print("=== [CONFIRMACIÓN ÚNICA EN TEST] Matriz de confusión ===")
    print(r["cm"])
    print()
    print("=== [CONFIRMACIÓN ÚNICA EN TEST] Peores errores (no retornaron de verdad, modelo dijo bajo riesgo) ===")
    print(r["peores_errores"][["id_cliente_anon", "score_riesgo", "recency_dias", "frequency_visitas"]].to_string(index=False))
    print()
    print("=== [CONFIRMACIÓN ÚNICA EN TEST] Rendimiento por segmento RFM ===")
    print(r["rendimiento_segmento"].to_string(index=False))
    print()
    print("=== [CONFIRMACIÓN ÚNICA EN TEST] Evidencia de calidad de las bandas ya fijadas ===")
    print(r["evidencia_bandas"].to_string())
    print()
    print("=== Tasa real de no-retorno por decil de score_riesgo (train+val, base de los umbrales) ===")
    print(r["por_decil"])
    print()
    print(f"=== Vista previa de producción (fecha_referencia = {r['fecha_actual'].date()}) ===")
    print(r["preview"].to_string(index=False))
    print()
    print("Distribución de bandas en producción:")
    print(r["conteo_bandas"])


if __name__ == "__main__":
    main()