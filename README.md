#  Beauty Girl Studio Smart Data Suite

> Plataforma inteligente de apoyo a la toma de decisiones para centros de estética mediante **Data Engineering, Data Science, Business Intelligence e Inteligencia Artificial Generativa**.

---

#  Descripción

Este repositorio contiene el desarrollo del **Trabajo Fin de Máster (TFM)** del **Máster en Data Science & Artificial Intelligence**, cuyo objetivo es diseñar e implementar una plataforma analítica capaz de transformar los datos operativos de un centro de estética en información estratégica para la toma de decisiones.

El proyecto toma como caso de estudio **Beauty Girl Studio**, un negocio especializado en:

-  Manicura y extensión de uñas
-  Diseño de cejas y pestañas
-  Venta de bisutería
-  Programas de fidelización
-  Gestión digital de citas

A partir de datos reales generados por el negocio se desarrollará una solución escalable que combine técnicas de Ingeniería de Datos, Ciencia de Datos y IA Generativa para optimizar la gestión comercial y operativa.

---

#  Objetivos del proyecto

El proyecto persigue cuatro objetivos estratégicos.

## 1. Optimizar la ocupación del estudio

Analizar el histórico de reservas para identificar patrones temporales y predecir la demanda futura.

---

## 2. Mejorar la fidelización

Segmentar a los clientes según su comportamiento para diseñar campañas de retención y personalización.

---

## 3. Reducir cancelaciones

Desarrollar modelos predictivos que permitan anticipar cancelaciones y facilitar acciones preventivas.

---

## 4. Automatizar la toma de decisiones

Integrar modelos de Inteligencia Artificial Generativa que transformen los resultados analíticos en recomendaciones comerciales, campañas y contenido personalizado.

---

#  Arquitectura del proyecto

El proyecto sigue una arquitectura inspirada en los principios de un **Lakehouse**, adaptada al tamaño del negocio.

```text
Fuentes de datos
        │
        ▼
 Raw Layer
(Datos originales)
        │
        ▼
 Processed Layer
(Limpieza y transformación)
        │
        ▼
 Data Warehouse
(SQLite)
        │
        ▼
 Gold Layer
(Datasets analíticos)
        │
        ├────────► Dashboards
        │
        ├────────► Machine Learning
        │
        └────────► IA Generativa
```

Esta arquitectura permitirá incorporar nuevas fuentes de información sin modificar el diseño general del sistema.

---

#  Modelo de datos

La arquitectura de datos se basa en un **modelo dimensional (Star Schema)** compuesto por tablas de hechos y dimensiones.

### Dimensiones

- `dim_cliente`
- `dim_servicio`
- `dim_fecha`

### Tablas de hechos

- `fact_citas`
- `fact_transacciones`

### Datasets Gold

- `gold_customer_analytics`
- `gold_daily_metrics`
- `gold_service_metrics`
- `gold_business_kpis`

Estos datasets constituirán la base para los modelos predictivos, dashboards y componentes de IA Generativa.

---

#  Producto esperado

El resultado final será una plataforma denominada:

## **Beauty Girl Studio Smart Data Suite**

El MVP incluirá:

-  Dashboard ejecutivo
-  KPIs de negocio
-  Predicción de demanda
-  Predicción de cancelaciones
-  Segmentación automática de clientes
-  Sistema inteligente de promociones
-  IA Generativa para campañas comerciales
-  Resúmenes ejecutivos para apoyo a la toma de decisiones

---

#  Estructura del repositorio

```text
BeautyGirlStudioSmartDataSuite/

├── data/
│   ├── raw/
│   ├── processed/
│   ├── warehouse/
│   └── gold/
│
├── docs/
│   ├── entregas/
│   ├── architecture/
│   ├── diagrams/
│   └── references/
│
├── notebooks/
│
├── src/
│   ├── ingestion/
│   ├── cleaning/
│   ├── warehouse/
│   ├── features/
│   ├── models/
│   ├── dashboards/
│   └── llm/
│
├── dashboard/
│
├── reports/
│
├── requirements.txt
├── README.md
└── LICENSE
```

---

#  Fuentes de datos

Actualmente el proyecto utiliza información real procedente de:

-  Aplicación de gestión de citas.
-  Base de datos de clientes.
-  Historial de transacciones.
-  Catálogo de servicios.
-  Historial de precios.
-  Información pública de Instagram.

Fuentes futuras:

-  API meteorológica.
-  Calendario de festivos.
-  Eventos locales.
-  Métricas de campañas.

---

#  Stack tecnológico

## Ingeniería de Datos

- Python
- Pandas
- NumPy
- SQLite
- Apache Parquet

## Ciencia de Datos

- Scikit-learn
- XGBoost
- Prophet
- Statsmodels

## Visualización

- Plotly
- Streamlit

## Inteligencia Artificial

- OpenAI API
- Large Language Models (LLM)

## Desarrollo

- Git
- GitHub
- VS Code

---

#  Modelos previstos

## Machine Learning

- Regresión Lineal
- Regresión Logística
- Random Forest
- Gradient Boosting
- XGBoost
- K-Means

## Analítica

- KPIs
- Customer Lifetime Value (CLV)
- Análisis RFM
- Predicción de abandono
- Predicción de demanda
- Predicción de cancelaciones

## Inteligencia Artificial Generativa

Los modelos LLM utilizarán los resultados generados por los modelos analíticos para:

- Generar campañas comerciales
- Redactar promociones
- Recomendar acciones de fidelización
- Resumir indicadores ejecutivos
- Asistir en la toma de decisiones

---

#  Privacidad

El proyecto utiliza datos reales pertenecientes a una empresa colaboradora.

Antes de cualquier análisis se aplican procesos de anonimización y limpieza para garantizar el cumplimiento del Reglamento General de Protección de Datos (RGPD).

Toda la información utilizada con fines académicos será agregada o anonimizada.

---

#  Estado del proyecto

Actualmente el proyecto se encuentra en la fase de:

> 🟢 Diseño de la arquitectura de datos y construcción del modelo dimensional.

Se ha completado:

- ✅ Definición del problema de negocio.
- ✅ Selección de fuentes de datos.
- ✅ Diseño de la arquitectura por capas.
- ✅ Diseño del modelo dimensional.
- ✅ Definición de la capa Gold.

La siguiente etapa será:

- 🔄 Data Profiling.
- 🔄 Limpieza de datos.
- 🔄 Construcción del Data Warehouse.

---

#  Roadmap

## Fase 1 — Comprensión del negocio

- [x] Selección del caso de estudio
- [x] Definición del problema
- [x] Objetivos del proyecto

## Fase 2 — Arquitectura de datos

- [x] Identificación de fuentes
- [x] Diseño de capas
- [x] Modelo dimensional
- [x] Diseño de datasets Gold

## Fase 3 — Ingeniería de Datos

- [ ] Data Profiling
- [ ] Limpieza y normalización
- [ ] Resolución de duplicados
- [ ] Construcción del Data Warehouse

## Fase 4 — Ciencia de Datos

- [ ] EDA
- [ ] Feature Engineering
- [ ] Modelos predictivos
- [ ] Evaluación

## Fase 5 — Producto

- [ ] Dashboard
- [ ] IA Generativa
- [ ] MVP
- [ ] Validación con Beauty Girl Studio


---

#  Información académica

**Máster:** Data Science & Artificial Intelligence

**Trabajo Fin de Máster**

**Estudiante:** Karen Camacho Verastegui

**Tutor:** Julio Valero

---


#  Licencia

Este repositorio tiene fines exclusivamente académicos.

Los datos pertenecen a Beauty Girl Studio y no serán publicados. Toda la información utilizada en el proyecto será previamente anonimizada y tratada conforme al Reglamento General de Protección de Datos (RGPD).