# Entrega 4 - Diseño del análisis y estrategia de modelado

**Máster en Data Science & AI**  
**Tarea:** Entrega 4 - Diseño del análisis y estrategia de modelado  
**Proyecto:** Beauty Girl Studio Smart Data Suite  
**Fecha de entrega:** 22 de Agosto de 2026  

---

# 1. Problema que se busca resolver

Beauty Girl Studio quiere comprender qué clientas están fidelizadas, cuáles están en riesgo de abandono y qué factores influyen en su retorno. Actualmente, la propietaria toma decisiones de fidelización basándose en intuición y experiencia, sin un sistema que identifique patrones de comportamiento ni que anticipe qué clientas podrían dejar de asistir.

El proyecto busca resolver un problema concreto y acotado:

> **Estimar la probabilidad de retorno de una clienta en los próximos 90 días y utilizar esa probabilidad para identificar clientas con alto riesgo de no retorno.**

Este resultado permitirá:

- Detectar clientas en riesgo.  
- Priorizar acciones comerciales.  
- Diseñar promociones dirigidas.  
- Mejorar la planificación del negocio.  

El modelo será consumido en un dashboard y en un ranking de clientas ordenadas por **baja probabilidad de retorno**.

---

# 2. Análisis de datos planteado y utilidad esperada

Antes del modelado se realizará un análisis descriptivo y exploratorio centrado en el comportamiento de las clientas y en las variables que alimentarán el modelo.

## Preguntas que se quieren responder

- ¿Con qué frecuencia vuelven las clientas?  
- ¿Cuánto tiempo pasa entre visitas (recency)?  
- ¿Qué categorías de servicios son más recurrentes?  
- ¿Qué clientas generan mayor valor monetario (monetary)?  
- ¿Qué patrones diferencian a las clientas que vuelven de las que no?  
- ¿Cómo se distribuye la variable objetivo (retorno en 90 días)?  
- ¿Qué proporción de clientas presenta **alto riesgo de no retorno**?

## Análisis descriptivos y comparativos

- Distribución de recency, frequency y monetary.  
- Comparación entre clientas que retornan vs. no retornan.  
- Análisis de ticket medio por segmento RFM.  
- Relación entre categoría favorita y retorno.  
- Evolución temporal de visitas por clienta.  
- Distribución de probabilidad de retorno y de riesgo de no retorno.

## Hipótesis a comprobar

- Las clientas con recency baja (última visita reciente) tienen mayor probabilidad de retorno.  
- Las clientas con frecuencia histórica alta tienden a ser más fieles.  
- Las clientas con ticket medio alto presentan menor riesgo de abandono.  
- Las clientas con recency alta y baja frecuencia concentran la mayor parte del riesgo de no retorno.  

## Visualizaciones previstas

- Histogramas de RFM.  
- Boxplots comparativos entre clientas que retornan vs. no retornan.  
- Curvas de visitas acumuladas por clienta.  
- Heatmaps de correlación entre variables.  
- Distribución de categorías favoritas.  
- Distribución de probabilidad de retorno y ranking de riesgo.

## Utilidad del análisis

Este análisis permitirá:

- Validar la calidad de las variables de entrada.  
- Detectar posibles fugas de información temporal.  
- Identificar relaciones relevantes para el modelo.  
- Comprender el comportamiento de las clientas y justificar las decisiones del modelado.  
- Alinear el modelo con la necesidad real del negocio: localizar clientas con **alto riesgo de no retorno**.

---

# 3. Tipo de modelos que se van a plantear

El problema se plantea como una **tarea de clasificación binaria**:

> **¿La clienta volverá en los próximos 90 días? (retorna / no retorna)**

El modelo generará una probabilidad de retorno, que se utilizará para ordenar clientas por **baja probabilidad de retorno** (alto riesgo).

## Baseline

Se utilizarán dos baselines:

### Baseline 1: Regla trivial

- **Regla:** predecir que todas las clientas NO retornan.  
- **Uso:** referencia mínima, pero insuficiente por sí sola.
- **Limitación:** si se evalúa F1 sobre la clase “retorno”, su F1 será 0 y cualquier modelo parecerá mejor.  

### Baseline 2: Regla basada en RFM (recency/frequency)

> **Regla ajustada según la lógica real del negocio:**  
> - Si `recency_dias <= 45` y `frequency_visitas >= 1` → predecir retorno.  
> - En caso contrario → predecir no retorno.

**Justificación:**

- En servicios de uñas, el ciclo natural de retorno es **30–45 días**.  
- Una clienta que vuelve **al menos una vez** en ese periodo es considerada activa.  
- Frecuencias de 2–3 visitas en 30 días son casos especiales y no representan el comportamiento típico.  
- Esta regla es coherente con la realidad operativa del negocio y constituye un baseline **realista y no sencillo de superar**.
  
**Objetivo:**  

  - El modelo debe superar esta regla en términos de capacidad para localizar clientas con alto riesgo de no retorno y generar acciones comerciales útiles.

## Modelos candidatos

### Modelo candidato 1: Regresión Logística

- **Tipo:** modelo interpretable y sencillo.  
- **Por qué se plantea:**  
  - Permite explicar qué variables influyen en la probabilidad de retorno.  
  - Fácil de entrenar y comunicar a la propietaria.  
- **Limitación:**  
  - Puede no capturar relaciones no lineales.

### Modelo candidato 2: Random Forest Classifier

- **Tipo:** modelo flexible basado en árboles.  
- **Por qué se plantea:**  
  - Captura interacciones complejas entre variables.  
  - Maneja bien variables categóricas y no requiere escalado.  
- **Limitación:**  
  - Menor interpretabilidad.  
  - Riesgo de sobreajuste si no se controla.

### Modelo candidato 3 (opcional si el tiempo lo permite): Gradient Boosting (XGBoost / LightGBM)

- **Tipo:** modelo avanzado de boosting.  
- **Por qué se plantea:**  
  - Suele ofrecer buen rendimiento en problemas tabulares.  
- **Limitación:**  
  - Mayor complejidad y coste computacional.  
  - No es imprescindible para el MVP.

---

# 4. Datos de entrada del análisis y los modelos

El dataset principal será:

## Dataset: `gold_cliente_snapshot.parquet`

### Granularidad

Una fila por cliente y fecha de referencia.

Cada snapshot representa el estado de la clienta en una fecha concreta, utilizando únicamente información disponible **hasta esa fecha**.

### Identificador principal

- `id_cliente_anon`  
- `fecha_referencia`

### Variables de entrada principales

| Variable            | Tipo      | Uso                                      |
|---------------------|-----------|------------------------------------------|
| recency_dias        | numérica  | Comportamiento temporal (última visita)  |
| frequency_visitas   | numérica  | Comportamiento histórico                 |
| monetary_total      | numérica  | Valor monetario acumulado                |
| ticket_medio        | numérica  | Calidad económica de la clienta          |
| antiguedad_dias     | numérica  | Tiempo desde la primera visita           |
| categoria_favorita  | categórica| Preferencias de servicio                 |
| usa_promociones     | booleana  | Indicador de uso de promociones          |
| segmento_rfm        | categórica| Variable derivada de RFM                 |
| prestador_habitual  | categórica| Prestador principal (para análisis)      |

### Variable objetivo

- `retorna_en_90_dias` (booleana):  
  - 1 si la clienta realiza al menos una visita en los 90 días posteriores a `fecha_referencia`.  
  - 0 si no realiza ninguna visita en ese periodo.  

Solo se etiquetarán snapshots para los que **han transcurrido completamente los 90 días posteriores**.  
Los snapshots recientes que aún no han completado ese horizonte **no se etiquetan como negativos** ni se utilizan para entrenamiento.

### Variables descartadas

- Nombre, email, teléfono → **privacidad**.  
- Fecha de nacimiento → riesgo de fuga de información y no necesaria para el MVP.  
- Origen de reserva → no aporta valor predictivo directo en esta primera versión.  

> **Prestador del servicio:**  
> Se mantiene en el dataset para análisis y posibles futuras iteraciones del modelo, dado que influye en la experiencia de la clienta y en la fidelización. En el MVP inicial no se utilizará como variable principal del modelo, pero sí podrá aparecer en análisis y dashboards.

### Información disponible en el momento de predicción

Solo se utilizarán variables calculadas **hasta la fecha de referencia**, sin incluir información posterior.  
Esto evita fuga de información y aproxima el uso real del sistema.

---

# 5. Datos de salida y forma de consumo

## Salida del modelo

| Campo              | Tipo   | Descripción                                      |
|--------------------|--------|--------------------------------------------------|
| id_cliente_anon    | TEXT   | Identificador anonimizado                        |
| fecha_referencia   | DATE   | Fecha de corte                                   |
| prob_retorno_90d   | FLOAT  | Probabilidad de retorno en 90 días              |
| prob_no_retorno_90d| FLOAT  | 1 - prob_retorno_90d                             |
| prediccion         | BOOLEAN| 1 = retorna, 0 = no retorna                      |
| explicacion        | TEXT   | Factores principales (SHAP / coeficientes)       |

El dashboard utilizará principalmente:

- `prob_no_retorno_90d` para ordenar clientas por **riesgo de no retorno**.  
- `prob_retorno_90d` y la explicación para comunicar confianza y factores al usuario.

## Formato previsto

- Fichero Parquet o CSV.  
- Vista SQL en el warehouse.  
- Integración en dashboard (ranking de clientas en riesgo, panel de fidelización y retorno).

## Uso por parte del negocio

- Identificar clientas con alto riesgo de no retorno.  
- Enviar promociones dirigidas y recordatorios.  
- Priorizar llamadas o mensajes personalizados.  
- Planificar campañas de fidelización y evaluar su impacto.

---

# 6. Estrategia para diseñar y seleccionar el modelo

## Preparación del dataset

- Construcción de snapshots por cliente y fecha de referencia.  
- Etiquetado solo cuando han transcurrido los 90 días posteriores completos.  
- Exclusión de snapshots recientes sin horizonte completo.  
- Codificación de variables categóricas.  
- Escalado de variables numéricas solo si el modelo lo requiere.  

## Baselines

- **Baseline 1:** “todas no retornan”.  
- **Baseline 2:** regla RFM basada en recency/frequency:  
  - `recency_dias <= 45` y `frequency_visitas >= 1` → retorno.

Ambos baselines se compararán con los modelos en términos de:

- Capacidad para localizar clientas con alto riesgo de no retorno.  
- Calidad de las acciones comerciales que se podrían derivar del ranking.

## Modelos candidatos

- Regresión logística.  
- Random Forest.  
- Gradient Boosting (si hay tiempo).

## Criterios de comparación

Dado que el negocio quiere localizar clientas con riesgo de no retorno, las métricas se orientarán a la clase “no retorna” y al ranking de riesgo:

- F1-score sobre la clase **“no retorna”**.  
- Recall de la clase “no retorna” (cuántas clientas en riesgo detectamos).  
- Precision de la clase “no retorna” (cuántas acciones son realmente útiles).  
- Métricas de ranking:  
  - Por ejemplo, porcentaje de clientas realmente en riesgo dentro del top N de mayor probabilidad de no retorno.  

## Regla de decisión final

El modelo será seleccionado si:

- Supera claramente ambos baselines (trivial y RFM).  
- Mantiene estabilidad en validación temporal.  
- Es interpretable o explicable.  
- No presenta fuga de información temporal.  
- Permite ordenar clientas por riesgo de no retorno de forma útil para el negocio.

---

# 7. Estrategia de validación y evaluación

## Separación de datos

Se utilizará una **separación temporal con margen de seguridad**:

- Train: snapshots con fecha de referencia hasta una fecha T1.  
- Validación: snapshots con fecha de referencia a partir de T1 + 90 días hasta T2.  
- Test: snapshots con fecha de referencia a partir de T2 + 90 días.

El margen de 90 días entre cortes garantiza que las ventanas de etiqueta (los 90 días posteriores) no se solapen entre train, validación y test, evitando contaminación temporal.

## Métricas

- F1-score sobre la clase “no retorna”.  
- Recall de la clase “no retorna” (evitar perder clientas en riesgo).  
- Precision de la clase “no retorna” (evitar acciones innecesarias).  
- Matriz de confusión.  
- ROC-AUC sobre probabilidad de retorno.  
- Métricas de ranking (por ejemplo, calidad del top N de riesgo).

## Comparación con baselines

- Comparar F1, recall y precision sobre la clase “no retorna”.  
- Comparar la calidad del ranking de riesgo frente a la regla RFM.  

## Análisis de errores

- Revisar clientas con alto riesgo real no detectadas por el modelo.  
- Analizar segmentos con peor rendimiento (por categoría, segmento RFM, antigüedad).  
- Detectar patrones temporales que afecten al rendimiento.

## Criterio de aceptación

- Mejora significativa sobre ambos baselines.  
- F1-score y recall aceptables sobre la clase “no retorna”.  
- Ranking de riesgo útil para generar acciones comerciales.  

Si ningún modelo cumple los criterios:

- Se utilizará un modelo de reglas basado en RFM y recency.  
- Se ajustará el horizonte temporal (por ejemplo, 60 o 120 días).  
- Se simplificará la salida a un score de riesgo sin probabilidad explícita.

---

# 8. Riesgos y alternativas

## Riesgos identificados

- **Variable objetivo:**  
  - Puede haber pocas clientas que retornen en 90 días → clase desbalanceada.  

- **Data leakage temporal:**  
  - Riesgo si se etiquetan snapshots recientes como “no retorna” sin haber completado el horizonte.  
  - Riesgo si se mezclan ventanas de etiqueta entre train, validación y test.

- **Volumen de datos:**  
  - Algunos periodos pueden tener menos registros o datos incompletos.

- **Cambios temporales:**  
  - Cambios en precios, servicios o comportamiento del negocio pueden afectar al modelo.

- **Segmentos pequeños:**  
  - Algunas categorías o segmentos RFM tienen pocas observaciones.

## Alternativas

- Cambiar el horizonte de retorno (60 o 120 días) si el 90 resulta demasiado estricto.  
- Simplificar el modelo a un score RFM de riesgo de no retorno.  
- Construir un modelo de clasificación “cliente activa vs. inactiva” con horizonte más amplio.  
- Utilizar únicamente variables numéricas para mayor estabilidad.  

---