# Beauty Girl Studio Smart Data Suite

> Plataforma inteligente de apoyo a la toma de decisiones para centros de estética basada en Ciencia de Datos e Inteligencia Artificial.

## Descripción

Este repositorio contiene el desarrollo del Trabajo Fin de Máster del **Máster en Data Science & Artificial Intelligence**, cuyo objetivo es diseñar e implementar una plataforma inteligente capaz de transformar los datos operativos de un centro de estética en información útil para apoyar la toma de decisiones.

El proyecto toma como caso de estudio **Beauty Girl Studio**, un pequeño negocio especializado en servicios de uñas, diseño de cejas, venta de bisutería y entre otros.

La plataforma propuesta combinará técnicas de:

-  Análisis Exploratorio de Datos (EDA)
-  Visualización de datos
-  Machine Learning
-  Inteligencia Artificial Generativa (LLM)
-  Modelos predictivos
-  Segmentación de clientes

El objetivo final es demostrar cómo una pequeña empresa puede aprovechar sus propios datos para mejorar su gestión mediante herramientas de Ciencia de Datos.

---

#  Objetivos del proyecto

El proyecto persigue cuatro objetivos estratégicos.

## 1. Optimizar la ocupación del estudio

Analizar el histórico de reservas para identificar patrones temporales y predecir la demanda futura, facilitando la planificación de horarios y promociones.

---

## 2. Mejorar la fidelización de las clientas

Segmentar a los clientes según sus hábitos de consumo y frecuencia de visita para apoyar estrategias de retención y personalización.

---

## 3. Reducir cancelaciones

Desarrollar modelos predictivos capaces de estimar la probabilidad de cancelación de una cita y facilitar acciones preventivas.

---

## 4. Automatizar campañas mediante IA Generativa

Utilizar modelos LLM para generar campañas comerciales, promociones y recomendaciones personalizadas a partir de los resultados obtenidos por los modelos analíticos.

---

#  Producto esperado

El resultado final será una plataforma denominada:

**Beauty Girl Studio Smart Data Suite**

El MVP incluirá:

- Dashboard interactivo.
- KPIs del negocio.
- Predicción de demanda.
- Predicción de cancelaciones.
- Segmentación de clientas.
- Recomendador de promociones.
- Generación automática de campañas mediante IA Generativa.

---

#  Estructura del repositorio

```text
BeautyGirlStudioSmartDataSuite/
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── external/
│
├── docs/
│   ├── entregas/
│   │   ├── 01_ideas_producto.md
│   │   ├── 02_datos_necesarios.md
│   │   ├── 03_...
│   │   └── ...
│   │
│   ├── images/
│   └── references/
│
├── notebooks/
│
├── src/
│   ├── data/
│   ├── features/
│   ├── models/
│   ├── visualization/
│   └── llm/
│
├── dashboard/
│
├── reports/
│
├── requirements.txt
│
├── LICENSE
│
└── README.md
```

---

#  Fuentes de datos

Las principales fuentes de información previstas son:

- Aplicación de gestión de citas de Beauty Girl Studio.
- Programa de fidelización.
- Historial de servicios.
- Información pública de Instagram.
- APIs meteorológicas.
- Calendarios de festivos.
- Datos derivados generados durante el proyecto.

---

#  Tecnologías previstas

Durante el desarrollo podrán utilizarse herramientas como:

- Python
- Pandas
- NumPy
- Scikit-learn
- XGBoost
- Plotly
- Streamlit
- SQL
- OpenAI API
- Git
- GitHub

La selección definitiva dependerá de la disponibilidad y calidad de los datos.

---

#  Modelos previstos

Dependiendo de la información finalmente disponible, el proyecto podrá incorporar:

### Análisis descriptivo

- KPIs
- Dashboards
- Visualización interactiva

### Modelos predictivos

- Regresión Lineal
- Regresión Logística
- Random Forest
- Gradient Boosting
- XGBoost

### Segmentación

- K-Means
- DBSCAN
- Análisis RFM

### IA Generativa

- Generación automática de campañas.
- Recomendaciones personalizadas.
- Redacción de promociones.
- Apoyo a la comunicación con clientas.

---

#  Privacidad

El proyecto utilizará datos reales pertenecientes a una empresa colaboradora.

Antes de cualquier análisis se aplicarán procesos de anonimización para eliminar información identificable de los clientes, garantizando el cumplimiento del Reglamento General de Protección de Datos (RGPD).

---

#  Estado del proyecto

Actualmente el proyecto se encuentra en la fase de:

> 🟢 Comprensión del negocio y análisis de los datos necesarios.

---

#  Roadmap

- [x] Selección de la idea del proyecto.
- [x] Definición del problema de negocio.
- [x] Identificación de fuentes de datos.
- [ ] Obtención de los datos.
- [ ] Limpieza y preparación.
- [ ] Análisis exploratorio.
- [ ] Ingeniería de características.
- [ ] Desarrollo de modelos predictivos.
- [ ] Integración de IA Generativa.
- [ ] Desarrollo del dashboard.
- [ ] Validación del MVP.
- [ ] Documentación final.

---

#  Información académica

**Máster:** Data Science & Artificial Intelligence

**Trabajo Fin de Máster**

**Estudiante:** Karen Camacho Verastegui

**Tutor:** Julio Valero

---

#  Licencia

Este repositorio tiene fines exclusivamente académicos.

Los datos utilizados pertenecen a Beauty Girl Studio y serán tratados de forma anonimizada. No se distribuirán datos personales ni información confidencial.