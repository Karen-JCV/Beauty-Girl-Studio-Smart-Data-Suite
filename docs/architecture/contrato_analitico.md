# Contrato Analítico — Beauty Girl Studio Smart Data Suite

**Estado:** v1.0 — cerrado tras feedback de Entregas 4 y 5.
**Ubicación en el repositorio:** `docs/architecture/contrato_analitico.md`
**Referenciado desde:** `04_analisis_modelado.md`, `05_diseno_frontal.md`, código de `src/model_return/`, `dashboard/`

> Este documento es la **fuente única de verdad** sobre qué significa cada número que el sistema calcula y muestra. Ningún componente (modelo, pipeline, dashboard) puede introducir un campo, métrica o etiqueta que no esté definida aquí. Si en el futuro se necesita un campo nuevo, se añade primero a este contrato y luego se implementa.

---

## 1. Por qué existe este documento

En las dos revisiones de la Entrega 5 se detectó el mismo problema de fondo: el frontal mostraba conceptos (`score`, `confianza`, `factores del modelo IA`, `riesgo incierto`) que no estaban definidos de forma unívoca en el diseño del modelo, o que directamente no existían todavía. Este documento cierra esa brecha fijando, antes de escribir una sola línea de pipeline o de dashboard, exactamente:

- Qué predice el modelo.
- Qué significa cada campo de salida, con su fórmula.
- Qué puede y qué no puede usarse como variable de entrada.
- Qué reglas temporales son innegociables.
- Qué métrica de negocio se optimiza y por qué.
- Qué queda fuera del MVP y no debe aparecer en ningún componente todavía.

---

## 2. Problema y variable objetivo

**Pregunta de negocio:** ¿qué clientas tienen alto riesgo de **no volver** en los próximos 90 días?

**Variable objetivo del modelo:** `retorna_en_90_dias` (booleana)

- `1` → la clienta realiza al menos una visita pagada en los 90 días posteriores a `fecha_referencia`.
- `0` → la clienta no realiza ninguna visita pagada en esos 90 días.

**Regla dura de etiquetado (no negociable):**
Un snapshot solo puede etiquetarse cuando **han transcurrido completamente los 90 días posteriores** a su `fecha_referencia`. Los snapshots que aún no completan ese horizonte:

- No se etiquetan como `0`.
- No se usan en entrenamiento, validación ni test.
- Se excluyen del dataset de modelado (aunque puedan existir para otros usos, como el ranking en producción, que sí puede predecir sobre snapshots "abiertos").

**Orientación de negocio:** aunque la variable objetivo está codificada como *retorno* (1 = vuelve), el sistema completo — análisis, métricas de evaluación y frontal — se orienta a detectar **riesgo de no retorno**. Esto significa:

- La clase de interés operativo es `no retorna` (0), no `retorna` (1).
- Las métricas de evaluación (F1, recall, precision) se calculan **sobre la clase "no retorna"**, no sobre "retorna".
- El ranking del dashboard ordena de **mayor a menor riesgo de no retorno**, no de mayor a menor probabilidad de retorno.

---

## 3. Definiciones cerradas de los campos de salida

Esta tabla resuelve ambigüedades detectadas anteriormente (score vs. confianza). **No existen más campos de salida que los siguientes.**

| Campo | Tipo | Fórmula / definición exacta | Fuente de verdad |
|---|---|---|---|
| `prob_retorno_90d` | float [0–1] | Salida directa del modelo, **después de calibración** (ver §6) | Modelo calibrado |
| `prob_no_retorno_90d` | float [0–1] | `1 - prob_retorno_90d` | Derivado |
| `score_riesgo` | int [0–100] | `round(prob_no_retorno_90d * 100)` | Derivado |
| `prediccion` | boolean | `prob_retorno_90d >= umbral_decision` (umbral fijado en validación, no 0.5 por defecto) | Modelo |
| `banda_riesgo` | categórica: `Bajo` / `Medio` / `Alto` | Ver §7 — basada en `score_riesgo` y umbrales **justificados con datos**, no arbitrarios | Post-modelo |
| `explicacion` | texto / lista de factores | Coeficientes de regresión logística **o** valores SHAP del modelo de árboles seleccionado. Nunca texto generado por LLM | Modelo entrenado |
| `indicador_incertidumbre` | booleano o categórico | Ver §8 — solo se activa si está formalmente definido y validado | Modelo calibrado |

**Campos que NO existen y no deben aparecer en ningún componente:**

- ❌ "Confianza del modelo" (%) — no está definida analíticamente, error detectado en revisión de E5.
- ❌ "Hallazgos con IA" — IA generativa está fuera del MVP (ver §9).
- ❌ "Factores del modelo IA" — hasta que exista un modelo entrenado con SHAP/coeficientes reales, no se muestra ningún factor.
- ❌ Cualquier campo derivado de información posterior a `fecha_referencia`.

---

## 4. Variables de entrada permitidas

Solo estas variables, todas calculadas **exclusivamente con información disponible hasta `fecha_referencia`**:

| Variable | Tipo | Descripción |
|---|---|---|
| `recency_dias` | numérica | Días desde la última visita hasta `fecha_referencia` |
| `frequency_visitas` | numérica | N.º de visitas hasta `fecha_referencia` |
| `monetary_total` | numérica | Gasto acumulado hasta `fecha_referencia` |
| `ticket_medio` | numérica | `monetary_total / frequency_visitas` |
| `antiguedad_dias` | numérica | Días desde la primera visita hasta `fecha_referencia` |
| `categoria_favorita` | categórica | Categoría de servicio más frecuente, derivada de `gold_visitas` |
| `usa_promociones` | booleana | Indicador de uso de promociones |
| `segmento_rfm` | categórica | Derivado de recency/frequency/monetary |

**Variables explícitamente prohibidas (no entran al modelo bajo ninguna circunstancia):**

- Nombre, email, teléfono, RUT, dirección, fecha de nacimiento — dato personal.
- `prestador_habitual` — se mantiene en `gold_cliente_snapshot` solo para análisis y dashboard, **no como feature del modelo en el MVP**.
- `origen_reserva` — descartado en E4 por no aportar valor predictivo demostrado en esta primera versión.
- Cualquier variable calculada con datos posteriores a `fecha_referencia` (riesgo de leakage).

---

## 5. Reglas temporales (innegociables)

1. Un snapshot representa el estado de una clienta en una fecha `t` (`fecha_referencia`).
2. Etiquetado solo si han transcurrido 90 días completos posteriores (§2).
3. **Split temporal con margen de seguridad de 90 días** entre train, validación y test, para que las ventanas de etiqueta no se solapen:
   - Train: snapshots con `fecha_referencia` hasta `T1`.
   - Validación: snapshots desde `T1 + 90 días` hasta `T2`.
   - Test: snapshots desde `T2 + 90 días` en adelante.
4. Ninguna variable de entrada puede usar información no disponible en el momento real de `fecha_referencia`.

---

## 6. Métrica de negocio y evaluación

**Principio rector:** nunca se optimiza la clase "retorna". El sistema existe para encontrar a las clientas que probablemente **no** volverán.

| Métrica | Sobre qué se calcula | Uso |
|---|---|---|
| F1-score | Clase `no retorna` | Métrica principal de comparación entre modelos |
| Recall | Clase `no retorna` | Evitar perder clientas en riesgo real |
| Precision | Clase `no retorna` | Evitar acciones comerciales innecesarias |
| ROC-AUC | Sobre `prob_retorno_90d` | Capacidad discriminativa general |
| Precision@k / Lift | Top-N por `score_riesgo` | Calidad del ranking que ve la propietaria |
| Brier score | `prob_retorno_90d` calibrada | Calidad de la calibración |
| Reliability curve | `prob_retorno_90d` por bandas | Verificar que probabilidad predicha ≈ frecuencia real observada |

**Baselines obligatorios de comparación (ningún modelo se acepta sin superar ambos):**

- **Baseline 1 — trivial:** predecir que todas las clientas no retornan. Solo válido como referencia mínima; no se reporta su F1 sobre la clase "retorna" como argumento de comparación (sería 0 y distorsiona la lectura).
- **Baseline 2 — regla RFM:** `recency_dias <= 45` y `frequency_visitas >= 1` → predice retorno; en caso contrario, no retorno.

**Calibración obligatoria antes de mostrar probabilidades en el frontal:** si el modelo no está calibrado (Brier score y reliability curve dentro de umbrales aceptables, a definir en la fase de validación), las probabilidades **no se muestran como valores de negocio**; se muestra únicamente la `banda_riesgo`.

---

## 7. Umbrales de banda de riesgo

- Valores **provisionales** de partida: `Alto ≥ 70`, `Medio 40–69`, `Bajo < 40` (sobre `score_riesgo`).
- Estado: **no validados**. Deben ajustarse con:
  - Distribución real de `score_riesgo` en el dataset de validación/test.
  - Coste/beneficio estimado de las acciones comerciales (ej. coste de contactar a una clienta vs. coste de perderla).
- Hasta que exista esa validación, el dashboard debe mostrar el rótulo **"Umbrales provisionales"** junto a la banda de riesgo (tal como ya se incorporó en el mockup de E5).
- Cualquier cambio de umbral se documenta en este archivo (sección de changelog, §11) antes de desplegarse.

---

## 8. Incertidumbre por clienta

- Solo se activa **si está formalmente definida y validada** con el modelo entrenado. Hasta entonces, el campo `indicador_incertidumbre` no se muestra en el dashboard.
- Definición operativa una vez validada:
  - Probabilidad de retorno en rango intermedio (ej. 0.4–0.6), **y/o**
  - Alta variabilidad de la probabilidad entre folds/modelos.
- No se usa el término "confianza" para este concepto (para no repetir la ambigüedad detectada en la revisión).

---

## 9. Explícitamente fuera del MVP

Estos elementos no deben aparecer en el pipeline, el modelo ni el frontal hasta nueva revisión de este contrato:

- IA generativa (resúmenes, narrativas, "hallazgos con IA").
- Predicción de demanda.
- Predicción de cancelaciones.
- Segmentación avanzada más allá de RFM.
- CLV (Customer Lifetime Value).
- Recomendación de promociones.
- Automatización de acciones comerciales (envío directo de campañas, integración WhatsApp/email).
- Reglas automáticas de exclusión de clientas del panel (la exclusión es **manual**, con menú de motivos — ver `05_diseno_frontal.md`).

---

## 10. Trazabilidad y privacidad

- Toda entrada/salida del modelo usa exclusivamente `id_cliente_anon`. Ningún dato personal (nombre, email, teléfono, RUT, dirección, fecha de nacimiento) llega al warehouse, a gold, al modelo ni al frontal.
- El mapeo nombre → `id_cliente_anon` vive únicamente en una tabla puente local, fuera del repositorio público (ver `docs/architecture/` — pendiente documentar en el paso de resolución de identidad).
- Ninguna variable del §4 puede sustituirse por una prohibida sin actualizar primero este contrato.

---

## 11. Historial de cambios

| Versión | Fecha | Cambio |
|---|---|---|
| v1.0 | *13-09-2026* | Documento creado consolidando definiciones de E4 y E5 tras feedback recibido. Fija score/probabilidad/riesgo/bandas/incertidumbre y elimina "confianza" inventada. |

---

## 12. Checklist de conformidad

- [x] ¿Todo campo mostrado en el frontal está definido en §3?
- [x] ¿Las métricas reportadas están calculadas sobre la clase `no retorna`?
- [x] ¿Los umbrales de banda de riesgo llevan la etiqueta "provisional" si no han sido validados con datos?
- [ ] ¿Alguna variable de entrada usa información posterior a `fecha_referencia`?
- [ ] ¿Aparece algún elemento de la lista de "fuera del MVP" (§9) en el pipeline o el dashboard?
- [ ] ¿El indicador de incertidumbre se muestra sin estar formalmente validado?