"""
train_model.py
================

Paso 9 del roadmap: modelado.

Consume:
  - data/gold/model_input.parquet (paso 8, ya con columna 'split')

Produce:
  - Tabla comparativa de baselines y modelos candidatos (train/val/test)
  - Gráficos de calibración y de importancia/coeficientes en
    docs/assets/model/
  - Reporte impreso con la decisión final según los criterios del
    contrato analítico §6

Reglas aplicadas (ver docs/entregas/13_modelado.md):

  - Todas las métricas de clasificación se calculan sobre la clase
    "no retorna" (pos_label=0), no sobre "retorna" (contrato §2 y §6).
  - El umbral de decisión (`prediccion`) se ajusta en el set de
    VALIDACIÓN maximizando F1 de la clase "no retorna", nunca se usa
    0.5 por defecto (contrato §3). El mismo umbral, ya fijado, se aplica
    después a test sin volver a tocarlo.
  - La calibración (Brier score, curva de fiabilidad) se evalúa por
    separado en val y en test -- no alcanza con un número agregado, dado
    que el EDA (paso 7) ya detectó que la tasa base de retorno cambia
    con el tiempo.
  - Se reporta la regresión logística con y con todas las variables y
    sin `monetary_total`, por la colinealidad de 0.96 con
    `frequency_visitas` detectada en el EDA.
"""

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    brier_score_loss, confusion_matrix, f1_score, precision_score,
    recall_score, roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ID_COLS = ["id_cliente_anon", "fecha_referencia", "split", "horizonte_completo", "prestador_habitual"]
TARGET = "retorna_en_90_dias"
COL_MONETARY = "monetary_total"
NUMERICAS = ["recency_dias", "frequency_visitas", "monetary_total", "ticket_medio", "antiguedad_dias"]

RANDOM_STATE = 42


# ---------------------------------------------------------------------------
# Carga y splits
# ---------------------------------------------------------------------------

def cargar_splits(gold_dir: Path):
    df = pd.read_parquet(gold_dir / "model_input.parquet")
    df = df[df["split"].notna()].copy()
    df[TARGET] = df[TARGET].astype(int)

    feature_cols = [c for c in df.columns if c not in ID_COLS + [TARGET]]

    splits = {}
    for s in ["train", "val", "test"]:
        sub = df[df["split"] == s].reset_index(drop=True)
        splits[s] = {
            "X": sub[feature_cols],
            "y": sub[TARGET],
            "meta": sub[["id_cliente_anon", "fecha_referencia"]],
        }
    return splits, feature_cols


# ---------------------------------------------------------------------------
# Baselines
# ---------------------------------------------------------------------------

def baseline_trivial_pred(y: pd.Series) -> np.ndarray:
    """Predice que TODAS las clientas no retornan (clase 0)."""
    return np.zeros(len(y), dtype=int)


def baseline_rfm_pred(X: pd.DataFrame) -> np.ndarray:
    """recency_dias <= 45 y frequency_visitas >= 1 -> predice retorno (1)."""
    return ((X["recency_dias"] <= 45) & (X["frequency_visitas"] >= 1)).astype(int).values


# ---------------------------------------------------------------------------
# Métricas (siempre orientadas a la clase "no retorna")
# ---------------------------------------------------------------------------

def metricas(y_true: pd.Series, y_pred: np.ndarray, y_proba: np.ndarray = None) -> dict:
    out = {
        "f1_no_retorna": f1_score(y_true, y_pred, pos_label=0, zero_division=0),
        "recall_no_retorna": recall_score(y_true, y_pred, pos_label=0, zero_division=0),
        "precision_no_retorna": precision_score(y_true, y_pred, pos_label=0, zero_division=0),
    }
    if y_proba is not None:
        out["roc_auc"] = roc_auc_score(y_true, y_proba)
        out["brier_score"] = brier_score_loss(y_true, y_proba)
    return out


def precision_en_top_k(y_true: pd.Series, score_riesgo: np.ndarray, k_pct: float = 0.2) -> float:
    """De las k_pct clientas con mayor score de riesgo (= mayor prob. de NO
    retornar), qué proporción realmente no retornó."""
    n = len(score_riesgo)
    k = max(1, int(round(n * k_pct)))
    idx_top = np.argsort(-score_riesgo)[:k]
    no_retorna_real = (y_true.values == 0)
    return no_retorna_real[idx_top].mean()


def elegir_umbral_optimo(y_val: pd.Series, proba_retorno_val: np.ndarray) -> float:
    """Umbral sobre prob_retorno_90d que maximiza F1 de la clase 'no
    retorna' en VALIDACIÓN (contrato §3: nunca 0.5 por defecto).

    No se usa un único argmax sobre una grilla fija: se comprobó que la
    curva F1-vs-umbral tiene una meseta ancha y prácticamente plana (0.25
    a 0.65, variación de F1 < 0.002) donde diferencias de punto flotante
    minúsculas entre entornos/versiones de librerías bastan para que el
    argmax "salte" de un extremo a otro de la meseta -- reproducible
    dentro de una misma máquina, pero NO estable entre dos entornos
    distintos (se observó en la práctica: 0.25 en un entorno, 0.55 en
    otro, con F1 casi idéntico en ambos). Para un umbral que el contrato
    exige "fijar con datos", eso no es aceptable.

    En su lugar: se identifica la meseta de candidatos cuyo F1 está a
    menos de `tolerancia` del máximo observado, y se toma la MEDIANA de
    esa meseta -- un punto estable y reproducible, no un extremo sensible
    al ruido numérico."""
    candidatos = np.unique(np.round(proba_retorno_val, 4))
    if len(candidatos) > 200:  # limitar coste computacional sin perder resolución útil
        candidatos = np.quantile(candidatos, np.linspace(0, 1, 200))

    f1s = np.array([
        f1_score(y_val, (proba_retorno_val >= th).astype(int), pos_label=0, zero_division=0)
        for th in candidatos
    ])
    f1_maximo = f1s.max()
    tolerancia = 0.005
    meseta = candidatos[f1s >= (f1_maximo - tolerancia)]
    return float(np.median(meseta))


# ---------------------------------------------------------------------------
# Modelos candidatos
# ---------------------------------------------------------------------------

def entrenar_logistica(X_train, y_train, feature_cols, excluir_monetary=False):
    cols = [c for c in feature_cols if not (excluir_monetary and c == COL_MONETARY)]
    numericas = [c for c in NUMERICAS if c in cols]
    categoricas = [c for c in cols if c not in numericas]

    preprocesador = ColumnTransformer([
        ("num", StandardScaler(), numericas),
        ("cat", "passthrough", categoricas),
    ])
    modelo = Pipeline([
        ("prep", preprocesador),
        ("clf", LogisticRegression(max_iter=1000, class_weight="balanced", random_state=RANDOM_STATE)),
    ])
    modelo.fit(X_train[cols], y_train)
    return modelo, cols


def entrenar_random_forest(X_train, y_train, feature_cols):
    modelo = RandomForestClassifier(
        n_estimators=300, max_depth=6, min_samples_leaf=20,
        class_weight="balanced", random_state=RANDOM_STATE, n_jobs=-1,
    )
    modelo.fit(X_train[feature_cols], y_train)
    return modelo


# ---------------------------------------------------------------------------
# Calibración
# ---------------------------------------------------------------------------

def graficar_calibracion(resultados_proba: dict, y_por_split: dict, out_dir: Path):
    """resultados_proba: {nombre_modelo: {'val': proba, 'test': proba}}"""
    fig, axes = plt.subplots(1, 2, figsize=(11, 5), sharey=True)
    for ax, split in zip(axes, ["val", "test"]):
        ax.plot([0, 1], [0, 1], "k--", label="Calibración perfecta", alpha=0.5)
        for nombre, proba_dict in resultados_proba.items():
            frac_pos, media_pred = calibration_curve(
                y_por_split[split], proba_dict[split], n_bins=8, strategy="quantile"
            )
            ax.plot(media_pred, frac_pos, marker="o", label=nombre)
        ax.set_title(f"Calibración -- {split}")
        ax.set_xlabel("Probabilidad de retorno predicha (media por bin)")
        if split == "val":
            ax.set_ylabel("Frecuencia real de retorno")
        ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(out_dir / "01_calibracion_val_test.png", dpi=130)
    plt.close(fig)


def graficar_importancia_rf(modelo_rf, feature_cols, out_dir: Path):
    importancias = pd.Series(modelo_rf.feature_importances_, index=feature_cols).sort_values()
    fig, ax = plt.subplots(figsize=(8, 7))
    importancias.tail(15).plot.barh(ax=ax, color="#264653")
    ax.set_title("Random Forest -- importancia de variables (top 15)")
    fig.tight_layout()
    fig.savefig(out_dir / "02_importancia_rf.png", dpi=130)
    plt.close(fig)
    return importancias


def graficar_coeficientes_lr(modelo_lr, cols, out_dir: Path, nombre: str):
    coefs = pd.Series(modelo_lr.named_steps["clf"].coef_[0], index=cols).sort_values()
    fig, ax = plt.subplots(figsize=(10, 8))
    coefs.plot.barh(ax=ax, color="#457b9d")
    titulo = f"Regresión logística ({nombre})\nCoeficientes — signo respecto a RETORNO"
    ax.set_title(titulo, fontsize=14, wrap=True)
    ax.axvline(0, color="black", linewidth=0.8)
    fig.tight_layout()
    fig.savefig(out_dir / f"03_coeficientes_{nombre}.png", dpi=150)
    plt.close(fig)

    return coefs



# ---------------------------------------------------------------------------
# Orquestación
# ---------------------------------------------------------------------------

def ejecutar(gold_dir: Path, out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    splits, feature_cols = cargar_splits(gold_dir)
    X_train, y_train = splits["train"]["X"], splits["train"]["y"]
    X_val, y_val = splits["val"]["X"], splits["val"]["y"]
    X_test, y_test = splits["test"]["X"], splits["test"]["y"]

    filas_resultado = []
    proba_por_modelo = {}

    # --- Baseline 1: trivial ---
    for split_nombre, (X, y) in [("val", (X_val, y_val)), ("test", (X_test, y_test))]:
        pred = baseline_trivial_pred(y)
        m = metricas(y, pred)
        m.update({"modelo": "Baseline trivial (todas no retornan)", "split": split_nombre})
        filas_resultado.append(m)

    # --- Baseline 2: regla RFM ---
    for split_nombre, (X, y) in [("val", (X_val, y_val)), ("test", (X_test, y_test))]:
        pred = baseline_rfm_pred(X)
        m = metricas(y, pred)
        m.update({"modelo": "Baseline RFM (recency<=45 y frequency>=1)", "split": split_nombre})
        filas_resultado.append(m)

    # --- Modelo candidato 1a: Regresión logística (todas las variables) ---
    lr_full, cols_lr_full = entrenar_logistica(X_train, y_train, feature_cols, excluir_monetary=False)
    proba_val_lr_full = lr_full.predict_proba(X_val[cols_lr_full])[:, 1]
    proba_test_lr_full = lr_full.predict_proba(X_test[cols_lr_full])[:, 1]
    umbral_lr_full = elegir_umbral_optimo(y_val, proba_val_lr_full)
    proba_por_modelo["LR (completa)"] = {"val": proba_val_lr_full, "test": proba_test_lr_full}
    for split_nombre, y, proba in [("val", y_val, proba_val_lr_full), ("test", y_test, proba_test_lr_full)]:
        pred = (proba >= umbral_lr_full).astype(int)
        m = metricas(y, pred, proba)
        m.update({"modelo": "Regresión logística (completa)", "split": split_nombre, "umbral": umbral_lr_full})
        filas_resultado.append(m)

    # --- Modelo candidato 1b: Regresión logística sin monetary_total (colinealidad) ---
    lr_sin_mon, cols_lr_sin_mon = entrenar_logistica(X_train, y_train, feature_cols, excluir_monetary=True)
    proba_val_lr_sin = lr_sin_mon.predict_proba(X_val[cols_lr_sin_mon])[:, 1]
    proba_test_lr_sin = lr_sin_mon.predict_proba(X_test[cols_lr_sin_mon])[:, 1]
    umbral_lr_sin = elegir_umbral_optimo(y_val, proba_val_lr_sin)
    proba_por_modelo["LR (sin monetary_total)"] = {"val": proba_val_lr_sin, "test": proba_test_lr_sin}
    for split_nombre, y, proba in [("val", y_val, proba_val_lr_sin), ("test", y_test, proba_test_lr_sin)]:
        pred = (proba >= umbral_lr_sin).astype(int)
        m = metricas(y, pred, proba)
        m.update({"modelo": "Regresión logística (sin monetary_total)", "split": split_nombre, "umbral": umbral_lr_sin})
        filas_resultado.append(m)

    # --- Modelo candidato 2: Random Forest ---
    rf = entrenar_random_forest(X_train, y_train, feature_cols)
    proba_val_rf = rf.predict_proba(X_val[feature_cols])[:, 1]
    proba_test_rf = rf.predict_proba(X_test[feature_cols])[:, 1]
    umbral_rf = elegir_umbral_optimo(y_val, proba_val_rf)
    proba_por_modelo["Random Forest"] = {"val": proba_val_rf, "test": proba_test_rf}
    for split_nombre, y, proba in [("val", y_val, proba_val_rf), ("test", y_test, proba_test_rf)]:
        pred = (proba >= umbral_rf).astype(int)
        m = metricas(y, pred, proba)
        m.update({"modelo": "Random Forest", "split": split_nombre, "umbral": umbral_rf})
        filas_resultado.append(m)

    # --- Random Forest calibrado (Platt/sigmoid, ajustado sobre val) ---
    # cv="prefit" indica a CalibratedClassifierCV que NO debe reentrenar el
    # estimador: usa el `rf` ya entrenado en train tal cual, y solo ajusta
    # el mapeo de calibración sobre val. Es la API correcta para
    # scikit-learn < 1.6 (ver requirements.txt: se fija scikit-learn==1.5.0
    # precisamente por esto). En 1.6+ este parámetro se sustituye por
    # FrozenEstimator y se elimina por completo en 1.8 -- si el proyecto
    # migra de versión de scikit-learn, este es el único punto a tocar.
    # NUNCA se omite `cv`: sin especificarlo, CalibratedClassifierCV usa su
    # valor por defecto (5-fold CV) y CLONA + REENTRENA el modelo desde
    # cero sobre val, descartando por completo lo aprendido en train.
    # Se probó también method="isotonic": tenía Brier ligeramente peor
    # (0.068 vs 0.066 en test) Y colapsaba el score_riesgo a solo 14
    # valores distintos en todo el test (uno de ellos compartido por el
    # 36% de las clientas) -- inservible para priorizar dentro de un
    # grupo tan grande. "sigmoid" da 900 valores distintos sin sacrificar
    # calibración. Ver docs/entregas/14_validacion_y_umbrales.md §1.
    rf_calibrado = CalibratedClassifierCV(rf, method="sigmoid", cv="prefit")
    rf_calibrado.fit(X_val[feature_cols], y_val)
    proba_val_rf_cal = rf_calibrado.predict_proba(X_val[feature_cols])[:, 1]
    proba_test_rf_cal = rf_calibrado.predict_proba(X_test[feature_cols])[:, 1]
    umbral_rf_cal = elegir_umbral_optimo(y_val, proba_val_rf_cal)
    proba_por_modelo["Random Forest (calibrado)"] = {"val": proba_val_rf_cal, "test": proba_test_rf_cal}
    for split_nombre, y, proba in [("val", y_val, proba_val_rf_cal), ("test", y_test, proba_test_rf_cal)]:
        pred = (proba >= umbral_rf_cal).astype(int)
        m = metricas(y, pred, proba)
        m.update({"modelo": "Random Forest (calibrado)", "split": split_nombre, "umbral": umbral_rf_cal})
        filas_resultado.append(m)

    tabla = pd.DataFrame(filas_resultado)

    # --- Precision@20% (calidad del ranking de riesgo) ---
    precision_top20 = {}
    for nombre, proba_dict in proba_por_modelo.items():
        precision_top20[nombre] = {
            "val": precision_en_top_k(y_val, 1 - proba_dict["val"], k_pct=0.2),
            "test": precision_en_top_k(y_test, 1 - proba_dict["test"], k_pct=0.2),
        }

    # --- Gráficos ---
    graficar_calibracion(proba_por_modelo, {"val": y_val, "test": y_test}, out_dir)
    importancias_rf = graficar_importancia_rf(rf, feature_cols, out_dir)
    coefs_lr = graficar_coeficientes_lr(lr_full, cols_lr_full, out_dir, "completa")
    coefs_lr_sin_mon = graficar_coeficientes_lr(lr_sin_mon, cols_lr_sin_mon, out_dir, "sin_monetary")

    return {
        "tabla": tabla,
        "precision_top20": precision_top20,
        "importancias_rf": importancias_rf,
        "coeficientes_lr": coefs_lr,
        "coeficientes_lr_sin_monetary": coefs_lr_sin_mon,
        "umbrales": {
            "lr_completa": umbral_lr_full, "lr_sin_monetary": umbral_lr_sin,
            "rf": umbral_rf, "rf_calibrado": umbral_rf_cal,
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gold-dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()

    r = ejecutar(args.gold_dir, args.out_dir)

    pd.set_option("display.width", 160)
    pd.set_option("display.max_columns", None)
    print("=== Tabla comparativa (baselines + modelos) ===")
    cols_mostrar = ["modelo", "split", "f1_no_retorna", "recall_no_retorna",
                     "precision_no_retorna", "roc_auc", "brier_score"]
    print(r["tabla"][cols_mostrar].to_string(index=False))
    print()
    print("=== Precision@20% (top 20% mayor score de riesgo) ===")
    for nombre, vals in r["precision_top20"].items():
        print(f"  {nombre}: val={vals['val']:.3f}  test={vals['test']:.3f}")
    print()
    print("=== Umbrales de decisión (elegidos en validación) ===")
    for k, v in r["umbrales"].items():
        print(f"  {k}: {v:.2f}")


if __name__ == "__main__":
    main()