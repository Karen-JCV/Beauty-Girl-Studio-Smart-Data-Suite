# Entrega 15 - Dashboard (Streamlit)

**Máster en Data Science & AI**
**Proyecto:** Beauty Girl Studio Smart Data Suite
**Paso del roadmap:** 11 de 13
**Rige bajo:** `docs/architecture/contrato_analitico.md`, `docs/entregas/05_diseno_frontal.md`
**Código:** `dashboard/app.py`, `src/model/persistir_modelo.py`, `src/dashboard/score_clientas.py`
**Entrada:** `docs/entregas/14_validacion_y_umbrales.md`

---

## 0. Objetivo

Conectar el mockup ya validado en la Entrega 5 a datos y modelo reales. Tres piezas nuevas, en orden de ejecución:

1. **`persistir_modelo.py`**: entrena el modelo final una vez y lo guarda en disco (antes se reentrenaba en cada script del paso 9/10 — el dashboard no puede permitirse reentrenar en cada carga de página).
2. **`score_clientas.py`**: aplica el modelo persistido al snapshot de producción y genera `scoring_actual.parquet`, con explicabilidad real (SHAP) — el dashboard solo lee este archivo, nunca toca el modelo directamente.
3. **`dashboard/app.py`**: la aplicación Streamlit, que lee `scoring_actual.parquet` + `gold_visitas.parquet` + `gold_cliente_snapshot.parquet`.

---

## 1. Un campo del mockup que faltaba en la capa gold: `prestador_habitual`

Al construir el scoring para el panel de detalle, se detectó que el mockup de la Entrega 5 muestra "Prestador habitual" por clienta, pero ese campo nunca se calculó en `gold_cliente_snapshot` — solo existía `categoria_favorita`. Se añadió en `build_gold.py` con la misma lógica (moda de `prestador` entre las visitas hasta el corte) y se marcó explícitamente como **columna informativa, no variable del modelo** (el contrato analítico §4 ya la excluye de los features): se añadió a `ID_COLS` en `train_model.py` para que `cargar_splits()` no la trate por accidente como columna de entrada. Se repropagó gold → features → modelo y se confirmó que las métricas de los pasos 9 y 10 no cambiaron ni un decimal — la columna nueva no se filtró al modelo.

---

## 2. Explicabilidad real con SHAP, no simulada

El contrato analítico (§3) exige que `explicacion` salga de "coeficientes de la regresión logística o valores SHAP / feature importance", nunca de texto inventado. `score_clientas.py` calcula, para cada clienta, los 3 factores de mayor peso con `shap.TreeExplainer` sobre el Random Forest **sin calibrar** (`rf_base.joblib`).

**Por qué sobre el modelo sin calibrar:** la calibración sigmoid (paso 10) es un reescalado monótono posterior de la probabilidad — no cambia qué variables pesan más para una predicción concreta. Explicar con el modelo base evita la complejidad de propagar SHAP a través de la capa de calibración y sigue siendo fiel a por qué el Random Forest tomó esa decisión.

Ejemplo real, tomado de la ejecución contra el snapshot de producción (`fecha_referencia = 2026-08-31`):

```
Clienta #1619 (banda Alto, score 97.8):
  Segmento RFM (Inactivas) → de riesgo
  Días desde la última visita alto → influyente (riesgo)
```

---

## 3. Validación: la app se ejecuta sin excepciones, con datos reales

No es posible interactuar con un navegador desde este entorno, pero se validó con el framework oficial de testing de Streamlit (`streamlit.testing.v1.AppTest`), que ejecuta el script real de principio a fin y captura cualquier excepción:

```
1. Carga inicial de la app:              sin excepciones
2. Seleccionar una clienta del ranking:  sin excepciones
3. Abrir "Excluir del panel" y confirmar: sin excepciones
```

Los KPIs de la carga inicial se calcularon con datos reales, no de ejemplo:

```
% de clientas en riesgo:      26%   (coincide con la banda "Alto" del paso 10)
Probabilidad de retorno media: 16%
```

Al seleccionar la primera clienta del ranking (`#1619`, score 98, banda Alto), el panel de detalle mostró correctamente `Segmento RFM: Inactivas`, `Recency: 866 días atrás` y el factor SHAP explicando la predicción — confirmando que el flujo completo `scoring_actual.parquet` → filtros → panel de detalle → factores del modelo funciona de extremo a extremo.

Adicionalmente se arrancó el servidor real (`streamlit run`) y se confirmó una respuesta `HTTP 200` en la raíz, sin errores en el log de arranque.

---

## 4. Qué implementa (y qué no) respecto al mockup de la Entrega 5

| Elemento del mockup | Estado |
|---|---|
| KPIs (% en riesgo, prob. retorno, ticket promedio, visitas promedio) | ✅ con datos reales |
| Ranking ordenado por score de riesgo | ✅ |
| Filtros (segmento, nivel de riesgo, categoría, prestador, antigüedad, ticket) | ✅ |
| Panel de detalle (RFM, categoría, prestador, antigüedad, historial de visitas) | ✅ |
| Factores del modelo | ✅ vía SHAP real |
| Botón "Excluir del panel" con menú de motivos | ✅ (solo en sesión — ver nota abajo) |
| Exportar CSV / Excel | ✅ funcional |
| Exportar PDF | ⚠️ botón presente, sin generación real todavía (alcance MVP de la Entrega 5 ya lo preveía como parte "a completar") |
| Tendencia de retorno y riesgo (180 días) | ⚠️ **simplificado**, ver §5 |
| Filtro de rango de fechas | ⚠️ no aplica: solo existe un snapshot de producción (el más reciente); queda como filtro futuro si el negocio empieza a correr el scoring periódicamente |

**Nota sobre "Excluir del panel":** en esta versión, la exclusión vive en `st.session_state` (memoria de la sesión del navegador) — se pierde al recargar la página. Persistirla (por ejemplo, en una tabla local `clientas_excluidas.parquet`) es un cambio pequeño pero se deja fuera de este paso para no mezclar la validación del dashboard con una nueva pieza de almacenamiento; se propone como ajuste futuro si la propietaria lo considera necesario.

---

## 5. Simplificación documentada: la "tendencia de 180 días"

El mockup original muestra una curva de "retorno esperado vs. umbral de riesgo" con granularidad diaria. **El negocio no tiene esa granularidad**: solo existen los cortes trimestrales ya etiquetados (`gold_cliente_snapshot`, paso 6). El dashboard muestra en su lugar la evolución de la tasa de retorno real por corte trimestral — el mismo dato que ya fundamentó el EDA (paso 7) y el modelado, no una simulación diaria inventada para parecerse más al mockup. Se documenta la diferencia directamente en la app (`st.caption` bajo el gráfico) para que quien la use entienda qué está viendo.

---

## 6. Cómo ejecutar

```bash
# 1. Entrenar y persistir el modelo (una vez, o cada vez que cambien los datos)
python src/model/persistir_modelo.py --gold-dir data/gold --models-dir data/models

# 2. Generar el scoring del snapshot de producción actual
python src/dashboard/score_clientas.py \
  --gold-dir data/gold \
  --dim-cliente-anon-path data/warehouse/dim_cliente_anon.parquet \
  --models-dir data/models \
  --out-path data/gold/scoring_actual.parquet

# 3. Levantar el dashboard
streamlit run dashboard/app.py
```

---

## 7. Próximo paso

Con el dashboard funcional y validado de extremo a extremo, el siguiente paso del roadmap es el **cierre del repositorio y la documentación final** (paso 12-13): actualizar el `README.md` con el estado real del proyecto (roadmap completo, capturas del dashboard funcionando), revisar que todas las entregas anteriores queden enlazadas y trazables y trabajar en la presentación del producto.