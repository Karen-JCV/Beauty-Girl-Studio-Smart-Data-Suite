"""
persistir_modelo.py
=====================

Entrena el modelo final (Random Forest calibrado, seleccionado en el
paso 9 y validado en el paso 10) UNA vez, y lo guarda en disco junto con
los umbrales definitivos -- para que el dashboard (paso 11) haga
inferencia cargando estos artefactos, sin reentrenar en cada carga de
página.

Produce:
  - models/rf_calibrado.joblib   (modelo calibrado, para prob_retorno_90d)
  - models/rf_base.joblib        (Random Forest sin calibrar, SOLO para
                                   explicabilidad vía SHAP -- la
                                   calibración sigmoid es un reescalado
                                   monótono posterior que no cambia qué
                                   variables pesan más en cada predicción)
  - models/model_meta.json       (columnas del modelo, umbral de decisión,
                                   umbrales de banda_riesgo, fecha de
                                   entrenamiento)
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import joblib

sys.path.insert(0, str(Path(__file__).parent))
from evaluar_modelo import calcular_umbrales_banda_riesgo, confirmar_en_test, entrenar_modelo_final


def ejecutar(gold_dir: Path, models_dir: Path) -> dict:
    models_dir.mkdir(parents=True, exist_ok=True)

    # 1) Entrenar y fijar calibración + umbral de decisión -- SOLO train/val
    entrenamiento = entrenar_modelo_final(gold_dir)

    # 2) Fijar bandas de riesgo por percentil -- SOLO train+val (nunca test,
    #    corrección aplicada tras feedback del tutor de la Entrega 4)
    _, umbral_bajo, umbral_alto = calcular_umbrales_banda_riesgo(entrenamiento, models_dir)

    # 3) Confirmación única en test -- genera los gráficos/evidencia de
    #    cierre pero NO cambia ni el modelo ni ninguno de los umbrales ya
    #    fijados en los pasos 1) y 2)
    confirmar_en_test(entrenamiento, umbral_bajo, umbral_alto, models_dir)

    joblib.dump(entrenamiento["modelo"], models_dir / "rf_calibrado.joblib")
    joblib.dump(entrenamiento["rf_base"], models_dir / "rf_base.joblib")

    meta = {
        "feature_cols": entrenamiento["feature_cols"],
        "metodo_calibracion": entrenamiento["metodo_calibracion"],
        "umbral_decision": round(float(entrenamiento["umbral"]), 4),
        "umbral_bajo": round(float(umbral_bajo), 2),
        "umbral_alto": round(float(umbral_alto), 2),
        "fecha_entrenamiento": datetime.now(timezone.utc).isoformat(),
        "nota_bandas": (
            "Las bandas Alto/Medio/Bajo son percentiles de score_riesgo "
            "dentro de la cartera actual (prioridad operativa relativa), "
            "no umbrales de probabilidad absoluta."
        ),
    }
    with open(models_dir / "model_meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    return meta


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gold-dir", type=Path, required=True)
    parser.add_argument("--models-dir", type=Path, required=True)
    args = parser.parse_args()

    meta = ejecutar(args.gold_dir, args.models_dir)

    print("=== Modelo persistido ===")
    for k, v in meta.items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()