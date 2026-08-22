# Entrega 4 - Diseño del análisis y estrategia de modelado

**Máster en Data Science & AI**  
**Tarea:** Entrega 4 - Diseño del análisis y estrategia de modelado
**Proyecto:** Beauty Girl Studio Smart Data Suite  
**Fecha de entrega:** 22 de Agosto de 2026

---

# 1. Problema que se busca resolver

Beauty Girl Studio quiere comprender qué clientas están fidelizadas, cuáles están en riesgo de abandono y qué factores influyen en su retorno. Actualmente, la propietaria toma decisiones de fidelización basándose en intuición y experiencia, sin un sistema que identifique patrones de comportamiento ni que anticipe qué clientas podrían dejar de asistir.

El proyecto busca resolver un problema concreto y acotado:

> **Estimar la probabilidad de que una clienta vuelva en los próximos 90 días, utilizando únicamente información disponible hasta una fecha de referencia.**

Este resultado permitirá:

- Detectar clientas en riesgo.  
- Priorizar acciones comerciales.  
- Diseñar promociones dirigidas.  
- Mejorar la planificación del negocio.  

El modelo será consumido en un dashboard y en un ranking de clientas con riesgo de abandono.

---

# 2. Análisis de datos planteado y utilidad esperada

Antes del modelado se realizará un análisis descriptivo y exploratorio centrado en el comportamiento de las clientas y en las variables que alimentarán el modelo.

## Preguntas que se quieren responder

- ¿Con qué frecuencia vuelven las clientas?  
- ¿Cuánto tiempo pasa entre visitas?  
- ¿Qué categorías de servicios son más recurrentes?  
- ¿Qué clientas generan mayor valor monetario?  
- ¿Qué patrones diferencian a las clientas que vuelven de las que no?  
- ¿Cómo se distribuye la variable objetivo (retorno en 90 días)?  

## Análisis descriptivos y comparativos

- Distribución de recency, frequency y monetary.  
- Comparación entre clientas que retornan vs. no retornan.  
- Análisis de ticket medio por segmento.  
- Relación entre categoría favorita y retorno.  
- Evolución temporal de visitas por clienta.  

## Hipótesis a comprobar

- Las clientas con menor recency tienen mayor probabilidad de retorno.  
- Las clientas con mayor frecuencia histórica tienden a ser más fieles.  
- Las clientas con ticket medio alto presentan menor riesgo de abandono.  
- Las promociones pueden influir en el retorno, pero no necesariamente en la fidelización real.  

## Visualizaciones previstas

- Histogramas de RFM.  
- Boxplots comparativos entre clientas que retornan vs. no retornan.  
- Curvas de visitas acumuladas.  
- Heatmaps de correlación entre variables.  
- Distribución de categorías favoritas.  

## Utilidad del análisis

Este análisis permitirá:

- Validar la calidad de las variables de entrada.  
- Detectar posibles fugas de información.  
- Identificar relaciones relevantes para el modelo.  
- Comprender el comportamiento de las clientas y justificar las decisiones del modelado.  

---

# 3. Tipo de modelos que se van a plantear

El problema es una **tarea de clasificación binaria**:

> **¿La clienta volverá en los próximos 90 días? (Sí/No)**

## Baseline

- **Regla simple:** predecir que todas las clientas NO retornan.  
- Justificación: en negocios de estética, la mayoría de clientas no vuelve en periodos cortos.  
- Permite medir si el modelo realmente aporta valor.

## Modelos candidatos

### Modelo candidato 1: Regresión Logística

- **Tipo:** modelo interpretable y sencillo.  
- **Por qué se plantea:**  
  - Permite explicar qué variables influyen en el retorno.  
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

### Identificador principal

- `id_cliente_anon`  
- `fecha_referencia`

### Variables de entrada principales

| Variable | Tipo | Uso |
|----------|------|-----|
| recency_dias | numérica | Feature clave del modelo |
| frequency_visitas | numérica | Comportamiento histórico |
| monetary_total | numérica | Valor monetario |
| ticket_medio | numérica | Calidad de la clienta |
| antiguedad_dias | numérica | Relación temporal |
| categoria_favorita | categórica | Preferencias |
| usa_promociones | booleana | Indicador comercial |
| segmento_rfm | categórica | Variable derivada |

### Variable objetivo

- `retorna_en_90_dias` (boolean)

### Variables descartadas

- Nombre, email, teléfono → **privacidad**  
- Fecha de nacimiento → riesgo de fuga de información  
- Origen de reserva → no aporta valor predictivo directo  
- **Prestador del servicio** → no se descarta; se mantiene como variable disponible para análisis y futuras iteraciones del modelo, aunque no se utilizará como variable principal en esta primera versión del MVP.

> **Nota:** Aunque el prestador del servicio no se utilizará como variable principal en el modelo predictivo inicial, se mantiene en el dataset porque influye en la experiencia de la clienta y puede ser relevante para análisis de fidelización o para futuras iteraciones del modelo.


### Información disponible en el momento de predicción

Solo variables calculadas **hasta la fecha de referencia**, nunca posteriores.

---

# 5. Datos de salida y forma de consumo

## Salida del modelo

| Campo | Tipo | Descripción |
|--------|------|-------------|
| id_cliente_anon | TEXT | Identificador anonimizado |
| fecha_referencia | DATE | Fecha de corte |
| prob_retorno_90d | FLOAT | Probabilidad entre 0 y 1 |
| prediccion | BOOLEAN | 1 = retorna, 0 = no retorna |
| explicacion | TEXT | Factores principales (SHAP / coeficientes) |

## Formato previsto

- Fichero Parquet o CSV.  
- Vista SQL en el warehouse.  
- Integración en dashboard (ranking de clientas en riesgo).  

## Uso por parte del negocio

- Identificar clientas en riesgo.  
- Enviar promociones dirigidas.  
- Priorizar recordatorios.  
- Planificar campañas de fidelización.

---

# 6. Estrategia para diseñar y seleccionar el modelo

## Preparación del dataset

- Filtrar snapshots con suficiente histórico.  
- Codificar variables categóricas.  
- Escalar variables numéricas solo si el modelo lo requiere.  
- Dividir en train/validation/test con separación temporal.  

## Baseline

- Regla “todas no retornan”.  
- Comparación con accuracy, recall y F1.

## Modelos candidatos

- Regresión logística.  
- Random Forest.  
- Gradient Boosting (si hay tiempo).

## Criterios de comparación

- F1-score (clase positiva = retorno).  
- Recall (evitar perder clientas que sí retornan).  
- Interpretabilidad.  
- Estabilidad temporal.  
- Riesgo de sobreajuste.  

## Regla de decisión final

El modelo será seleccionado si:

- Supera claramente el baseline.  
- Mantiene estabilidad en validación temporal.  
- Es interpretable o explicable.  
- No presenta fuga de información.  
- Puede integrarse fácilmente en el dashboard.

---

# 7. Estrategia de validación y evaluación

## Separación de datos

- **Split temporal**:  
  - Train: snapshots hasta 2024  
  - Validation: 2025  
  - Test: 2026  
- Justificación: evita fuga de información y simula uso real.

## Métricas

- **F1-score** (principal)  
- **Recall** (evitar falsos negativos)  
- **Precision** (evitar acciones innecesarias)  
- Matriz de confusión  
- Curva ROC-AUC  

## Comparación con baseline

- El modelo debe mejorar recall y F1.  

## Análisis de errores

- Revisar clientas con predicción incorrecta.  
- Analizar segmentos con peor rendimiento.  
- Detectar patrones temporales.

## Criterio de aceptación

- F1-score > baseline + 15%  
- Recall > 0.60  
- Estabilidad temporal aceptable  

Si ningún modelo cumple los criterios:

- Se utilizará un modelo de reglas basado en RFM.  
- Se ajustará el horizonte temporal.  
- Se simplificará la variable objetivo.

---

# 8. Riesgos y alternativas

## Riesgos identificados

- **Variable objetivo:**  
  - Puede haber pocas clientas que retornen en 90 días → clase desbalanceada.

- **Data leakage:**  
  - Riesgo si se usan variables posteriores a la fecha de referencia.

- **Volumen de datos:**  
  - Algunos años tienen menos registros o datos incompletos.

- **Cambios temporales:**  
  - Cambios en precios, servicios o comportamiento del negocio.

- **Segmentos pequeños:**  
  - Algunas categorías tienen pocas observaciones.

## Alternativas

- Cambiar el horizonte de retorno (60 o 120 días).  
- Simplificar el modelo a un score RFM sin predicción.  
- Construir un modelo de clasificación “cliente activa vs. inactiva”.  
- Utilizar únicamente variables numéricas para mayor estabilidad.  

---