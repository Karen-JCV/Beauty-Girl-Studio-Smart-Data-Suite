#  Beauty Girl Studio Smart Data Suite

> Plataforma analítica para medir la fidelización de clientas y predecir su probabilidad de retorno mediante **Data Engineering, Data Science y Machine Learning**.

---

# Descripción

Este repositorio contiene el desarrollo del **Trabajo Fin de Máster (TFM)** del **Máster en Data Science & Artificial Intelligence**, cuyo objetivo es construir una plataforma analítica que permita a **Beauty Girl Studio** comprender el comportamiento de sus clientas y anticipar su retorno.

El proyecto utiliza datos reales del negocio (clientes, reservas, ventas, servicios y transacciones) para desarrollar un sistema que:

- Mide la fidelización mediante **RFM**  
- Identifica clientas en riesgo 
- Estima la **probabilidad de retorno en 90 días**.

Esta solución escalable combinará técnicas de Ingeniería de Datos y Ciencia de Datos para optimizar la gestión comercial y operativa.

---

# Objetivo del proyecto

El proyecto persigue un objetivo estratégico principal:

## Predecir la probabilidad de retorno de una clienta

A partir del historial de visitas, gasto y comportamiento, se construye un modelo que estima si una clienta volverá en los próximos 90 días. Este resultado permitirá:

- Detectar clientas en riesgo
- Diseñar acciones de fidelización
- Mejorar la planificación comercial

---

#  Arquitectura del proyecto

El proyecto sigue una arquitectura por capas, inspirada en principios de ingeniería de datos:

```text
Fuentes de datos
        │
        ▼
 Raw Layer
(Datos originales en Excel)
        │
        ▼
 Processed Layer
(Limpieza y normalización en Parquet)
        │
        ▼
 Data Warehouse
(SQLite)
        │
        ▼
 Gold Layer
(Datasets analíticos para RFM y modelado)
        │
        ├────────► EDA
        │
        └────────► Modelo de retorno        
```


Esta arquitectura permite mantener trazabilidad, evitar fuga de información y preparar los datos para análisis y modelado.

---

#  Modelo de datos

El modelo de datos se basa en un esquema dimensional sencillo:

### Dimensiones

- `dim_cliente_anon` (cliente anonimizado)
- `dim_servicio`
- `dim_fecha`

### Tablas de hechos

- `fact_reservas`
- `fact_ventas`
- `fact_items`
- `fact_transacciones`

### Datasets Gold (datasets finales)

- `gold_visitas.parquet`  → una fila por visita realizada
- `gold_cliente_snapshot.parquet` → una fila por cliente y fecha de referencia

Estos datasets constituyen la entrada del análisis RFM y del modelo de probabilidad de retorno.

---

#  Producto esperado (MVP)

El resultado final será una plataforma denominada:

## **Beauty Girl Studio Smart Data Suite — Versión Fidelización**

Incluye:

- Análisis RFM por clienta
- Segmentos de fidelización
- Modelo de probabilidad de retorno (90 días)
- Ranking de clientas en riesgo
- Dashboard analítico

**Funcionalidades que quedan como mejoras futuras**

- Predicción de demanda
- Predicción de cancelaciones
- Segmentación avanzada
- CLV
- Recomendación de promociones
- IA Generativa
  
Estas líneas se documentan como futuras extensiones del proyecto, pero no forman parte del MVP.

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
│   ├── eda/
│   └── model/
│
├── src/
│   ├── ingestion/
│   ├── cleaning/
│   ├── warehouse/
│   ├── features/
│   ├── model_return/
│   └── dashboards/
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

El proyecto utiliza información real procedente de:

- Aplicación de gestión de citas
- Base de datos de clientes
- Historial de ventas
- Ítems de servicios
- Catálogo de servicios
- Historial de transacciones

Fuentes futuras (no incluidas en el MVP):

- API meteorológica
- Calendario de festivos
- Métricas de Instagram
- Eventos locales

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
- Regresión Logística
- Random Forest

## Visualización

- Plotly
- Streamlit

## Desarrollo

- Git
- GitHub
- VS Code

---

#  Modelos previstos

## Modelo principal (MVP)

- Regresión Logística → modelo interpretable
- Random Forest → modelo flexible para comparación

## Analítica

- RFM
- Segmentos de fidelización
- Variables derivadas
  
## Modelos futuros (no incluidos en el MVP)

- Predicción de demanda
- Cancelaciones
- CLV
- Segmentación avanzada
- IA Generativa

---

#  Privacidad

El proyecto utiliza datos reales de clientas.
Se aplican medidas estrictas de anonimización:

- Eliminación de nombres, emails, teléfonos y RUT
- Uso de identificadores anónimos
- Capa gold sin datos personales
- Cumplimiento del RGPD

---

#  Estado del proyecto

Actualmente el proyecto se encuentra en la fase de:

> 🟢 Diseño del análisis y estrategia de modelado..

Se ha completado:

- ✅ Entrega 1: Ideas de producto
- ✅ Entrega 2: Datos necesarios (reformulada)
- ✅ Entrega 3: Modelo de datos y capa gold (reformulada)
- ✅ Entrega 4: Estrategia de análisis y modelado

La siguiente etapa será:

- 🔄 Data Profiling
- 🔄 Limpieza y normalización
- 🔄 Construcción del Data Warehouse
- 🔄 EDA
- 🔄 Entrenamiento del modelo de retorno

---

#  Roadmap

## Fase 1 — Comprensión del negocio

- [x] Selección del caso de estudio
- [x] Definición del problema
- [x] Acotación del alcance

## Fase 2 — Arquitectura de datos

- [x] Identificación de fuentes
- [x] Diseño de capas
- [x] Modelo dimensional
- [x] Capa Gold

## Fase 3 — Ingeniería de Datos

- [ ] Data Profiling
- [ ] Limpieza y normalización
- [ ] Resolución de duplicados
- [ ] Construcción del Data Warehouse

## Fase 4 — Ciencia de Datos

- [ ] EDA
- [ ] Feature Engineering
- [ ] Modelo de retorno
- [ ] Validación

## Fase 5 — Producto

- [ ] Dashboard
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