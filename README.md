#  Beauty Girl Studio Smart Data Suite

> Plataforma analítica para medir la fidelización de clientas y predecir su probabilidad de retorno mediante **Data Engineering, Data Science y Machine Learning**, con un dashboard elegante, cálido y funcional inspirado en una estética otoñal.

---

# Descripción

Este repositorio contiene el desarrollo del **Trabajo Fin de Máster (TFM)** del **Máster en Data Science & Artificial Intelligence**, cuyo objetivo es construir una plataforma analítica que permita a **Beauty Girl Studio** comprender el comportamiento de sus clientas y anticipar su retorno.

Este MVP parte de los datos reales del negocio (clientes, reservas, ventas, servicios y transacciones) y construye, paso a paso y con verificación en cada etapa, un pipeline completo que:

- Resuelve la identidad de las clientas y las anonimiza de forma segura
- Mide la fidelización mediante **RFM**
- Identifica clientas en riesgo de no retorno
- Estima la **probabilidad calibrada de retorno en 90 días** con un modelo entrenado y validado
- Presenta los resultados en un dashboard funcional (Streamlit)

---

# Objetivo del proyecto

## Predecir la probabilidad de retorno de una clienta

A partir del historial de visitas, gasto y comportamiento, se estima si una clienta volverá en los próximos 90 días. Esto permite:

- Detectar clientas en riesgo
- Diseñar acciones de fidelización
- Mejorar la planificación comercial
- Optimizar la comunicación con las clientas

El contrato que fija con precisión qué significa cada número del sistema (score, probabilidad, riesgo, bandas, variables permitidas, reglas temporales) vive en **`docs/architecture/contrato_analitico.md`** — es la fuente única de verdad, referenciada desde todas las entregas y desde el propio código.

---

#  Arquitectura del proyecto

```text
Fuentes de datos (Excel)
        │
        ▼
 Raw Layer
(Datos originales, sin modificar)
        │
        ▼
 Resolución de identidad
(id_cliente_anon -- hash + código de 4 dígitos solo para UI)
        │
        ▼
 Processed Layer
(Limpieza, normalización, sin ningún dato personal)
        │
        ▼
 Data Warehouse (SQLite)
(dim_cliente_anon, dim_servicio, fact_ventas, fact_items,
 fact_transacciones, fact_reservas -- con FK activas)
        │
        ▼
 Gold Layer
(gold_visitas, gold_cliente_snapshot -- con columna 'split')
        │
        ├────────► EDA (paso 7)
        │
        ├────────► Feature engineering (paso 8)
        │
        ├────────► Modelo de retorno (pasos 9-10)
        │                  │
        │                  ▼
        │           models/ (persistido: rf_calibrado.joblib,
        │           rf_base.joblib, model_meta.json)
        │                  │
        └──────────────────┴───────► Dashboard (Streamlit, paso 11)
```

Esta arquitectura se decidió en la Entrega 3 y se fue corrigiendo con evidencia real a medida que se implementaba — cada corrección está documentada en la entrega del paso donde se detectó (ver tabla de la sección siguiente).

---

#  Estado del proyecto

>  Dashboard funcional conectado al modelo real. Proyecto cerrado tras auditoría final (26/09/2026).

## Entregas del curso (evaluadas por el tutor)

- ✅ Entrega 1: Ideas de producto
- ✅ Entrega 2: Datos necesarios (reformulada tras feedback)
- ✅ Entrega 3: Modelo de datos y capa gold (reformulada tras feedback)
- ✅ Entrega 4: Estrategia de análisis y modelado
- ✅ Entrega 5: Diseño del frontal y experiencia de usuario

## Pasos de implementación (`docs/entregas/06` en adelante)

| Paso | Documento | Qué hace | Hallazgo o corrección más importante |
|---|---|---|---|
| 1 | `06_data_profiling.md` | Perfilado real de los 6 Excel | La clave de unión real es `ventas."ID interno"` = `items/transacciones."ID Venta"`, no `ventas.ID`; `reservas."N° de Cliente"` inutilizable (99.4% nulo) |
| 2 | `07_resolucion_identidad.md` | Resolución de identidad + anonimización | Dos identificadores (`id_cliente_anon` hash, `codigo_display` de 4 dígitos) para evitar colisiones; 46 nombres con identidad genuinamente ambigua |
| 3 | `08_limpieza_normalizacion.md` | Limpieza → capa `processed/` | `clave_venta` llevaba el nombre de la clienta en texto plano sin hashear -- corregido; 2 ventas fusionadas por colisión de minuto (el sistema de origen no guarda segundos) |
| 4 | `09_warehouse.md` | Warehouse relacional (SQLite) | `PRAGMA foreign_keys=ON` detectó en la práctica la colisión de `clave_venta` del punto anterior |
| 5 | `10_capa_gold.md` | `gold_visitas` + `gold_cliente_snapshot` | Verificación de fuga de información recalculando a mano sobre una muestra: 0 errores; `retorna_en_90_dias` nunca se rellena con 0 sin horizonte completo |
| 6 | `11_eda.md` | EDA orientado a riesgo de no retorno | La tasa de retorno del negocio cae de 73% a 19% con el tiempo (deriva real, no ruido) -- confirma que el split temporal es obligatorio, no opcional |
| 7 | `12_feature_engineering.md` | Split temporal + codificación | Margen de 90 días entre splits verificado en tiempo de ejecución, no solo por diseño |
| 8 | `13_modelado.md` | Baselines + Regresión Logística + Random Forest | Colinealidad 0.96 entre `frequency_visitas`/`monetary_total` invierte el signo de un coeficiente -- corregido probando la variante sin `monetary_total` |
| 9 | `14_validacion_y_umbrales.md` | Validación, errores, umbrales de `banda_riesgo` | Un umbral definido por tasa absoluta (80%) metía al 75% de las clientas en "Alto riesgo" -- redefinido por percentil de score |
| 10 | `15_dashboard.md` | Dashboard (Streamlit) conectado al modelo real | Explicabilidad real vía SHAP (no simulada); validado sin excepciones con `streamlit.testing.v1.AppTest` |

**Nota de trazabilidad:** varias cifras de `13_modelado.md` y `14_validacion_y_umbrales.md` se corrigieron después de la primera versión, por un problema de estabilidad numérica en la selección del umbral de decisión entre distintos entornos (documentado con su propio diagnóstico y validación en `13_modelado.md` §6). Los documentos actuales ya reflejan los valores definitivos.

**Nota de auditoría final (26/09/2026):** el proyecto pasó por una auditoría de cierre que reprodujo el pipeline completo desde los Excel originales hasta el modelo entrenado, para verificar con evidencia ejecutable — no solo documental — que el sistema desplegado se comporta como dice el contrato analítico. El hallazgo de esa auditoría que requería acción antes del cierre ya está resuelto:

- Este README ya refleja el estado real de cada funcionalidad (ver más abajo): la exportación a PDF, CSV y Excel está completamente implementada y funcional, no pendiente.

## Próximos pasos

- 🔄 Persistencia de la exclusión de clientas del panel (hoy vive solo en la sesión del navegador)
- 🔄 Validación con Beauty Girl Studio del alcance final y de las limitaciones descritas más abajo

---

#  Modelo de datos

## Dimensiones

- `dim_cliente_anon` — identidad anonimizada (hash de 16 caracteres + código de 4 dígitos solo para UI)
- `dim_servicio` — catálogo de servicios

## Tablas de hechos

- `fact_ventas`, `fact_items`, `fact_transacciones`, `fact_reservas` — con claves foráneas activas y verificadas contra los datos reales

## Datasets Gold

- `gold_visitas.parquet` → una fila por visita pagada
- `gold_cliente_snapshot.parquet` → una fila por cliente y fecha de referencia, con la variable objetivo `retorna_en_90_dias`, la columna `split` (train/val/test/producción) y `prestador_habitual`/`categoria_favorita` para el frontal

Contrato completo de campos, tipos y reglas en `docs/architecture/contrato_analitico.md`.

---

#  Modelo predictivo (resultado real, no objetivo)

**Modelo seleccionado: Random Forest calibrado (sigmoid/Platt)**, sobre 5.192 snapshots con horizonte de 90 días ya completado (632 clientas).

| Métrica (test) | Valor |
|---|---|
| ROC-AUC | 0.952 |
| Brier score | 0.065 |
| F1 (clase "no retorna") | 0.946 |
| Precision@20% (top clientas de mayor riesgo) | 0.996 |

Estas cifras fueron reproducidas de forma independiente en la auditoría final de cierre, ejecutando el pipeline completo desde los Excel originales hasta el entrenamiento del modelo.

Supera con claridad a ambos baselines (trivial y regla RFM) en capacidad de ranking y calibración. Alternativa documentada: regresión logística sin `monetary_total` (por colinealidad con `frequency_visitas`), con rendimiento casi equivalente y coeficientes más directos de explicar. Detalle completo, incluida la comparación de las 4 métricas por split y la justificación de cada decisión, en `docs/entregas/13_modelado.md` y `14_validacion_y_umbrales.md`.

---

#  Producto (MVP funcional)

## **Beauty Girl Studio Smart Data Suite — Dashboard de Fidelización y Retorno**

![Mockup del frontal](docs/assets/05_mockup_frontal.png)

*(el mockup original de la Entrega 5; el dashboard funcional se ejecuta con `streamlit run dashboard/app.py` sobre datos y modelo reales -- ver `docs/entregas/15_dashboard.md` para el detalle de qué se implementó igual y qué se simplificó respecto al mockup y la sección "Funcionalidades previstas en el mockup y fuera del alcance final" más abajo)*

Incluye, con datos reales de principio a fin:

- Ranking de clientas ordenado por `score_riesgo`
- KPIs (% en riesgo, probabilidad de retorno, ticket promedio, visitas promedio)
- Filtros (segmento RFM, nivel de riesgo, categoría favorita, prestador habitual, antigüedad, ticket)
- Panel de detalle por clienta (RFM, historial de visitas, factores del modelo vía SHAP)
- Botón de exclusión de clientas del panel (en memoria de sesión, ver "Próximos pasos")
- **Exportación CSV, Excel y PDF completamente funcionales** en las pestañas "Clientas en riesgo" y "Reportes" (informe ejecutivo con logo, KPIs y notas explicativas)
- Tendencia de retorno por corte histórico

**Funcionalidades que quedan como mejoras futuras** (documentadas y fuera del MVP, no olvidadas):

- Predicción de demanda, predicción de cancelaciones, segmentación avanzada, CLV, recomendación de promociones, IA generativa

---

# Funcionalidades previstas en el mockup y fuera del alcance final

Durante el diseño del frontal (Entrega 5) se previeron tres botones de acción sobre el panel de
detalle de clienta: "Descargar CSV", "Exportar informe" y "Exportar caso". Los dos primeros forman
parte del producto final. El tercero no:

**"Exportar caso"** → No forma parte de la versión final del dashboard. La propietaria va a ver
clientas anonimizadas (identificadas solo por un código de 4 dígitos) y no es necesario exportar
un caso individual fuera del contexto del panel; la información de cada clienta ya es visible y
exportable dentro del ranking general. Se documenta como decisión de alcance, no como pendiente.

Otras diferencias entre el mockup y el producto final, ambas justificadas con datos reales y no
por limitación técnica:

- **Escala del score de riesgo:** el mockup mostraba umbrales de banda de riesgo en una escala
  intuitiva (Alto ≥70, Medio 40-69, Bajo <40). El negocio real tiene una tasa base de no-retorno
  muy alta (≈78% en el conjunto de test), lo que concentra el `score_riesgo` real en el tramo
  superior de la escala. Los umbrales definitivos, fijados por percentil de la distribución real
  (no por una tasa de acierto absoluta), son distintos: ver `docs/entregas/14_validacion_y_umbrales.md`.
- **Tendencia de retorno:** el mockup mostraba una curva diaria de 180 días. El producto final usa
  únicamente los cortes trimestrales reales disponibles en los datos del negocio, para no rellenar
  con datos inventados los días sin información real.

---

# Limitaciones conocidas

- **Segmento "Campeonas":** el modelo es notablemente más débil identificando el no-retorno de las
  clientas más fieles (recall del 70.1% en ese segmento, frente a >99% en clientas inactivas o en
  riesgo) — es un patrón estructural (RFM no captura eventos externos como mudanza o cambio de
  trabajo), no un error corregible ajustando el modelo. Ver `docs/entregas/14_validacion_y_umbrales.md` §3-4.
- **`items.xlsx` no registra ítems de bisutería**, aunque el negocio también la vende — se vende por
  otro canal no incluido en esta exportación. Pendiente de validar directamente con la propietaria
  si es relevante para futuras versiones.
- **Exclusión de clientas del panel es solo de sesión**: al cerrar el navegador se pierde. No hay
  persistencia entre sesiones en esta versión.
- **El nombre real del personal (`prestador_habitual`) aparece en el dashboard y en las
  exportaciones**, por diseño, para dar contexto de cartera por profesional. No se anonimiza al
  personal, solo a las clientas.
- **Este MVP no incluye** (y no está previsto que incluya en esta versión): IA generativa, predicción
  de demanda, predicción de cancelaciones, segmentación avanzada más allá de RFM, CLV, recomendación
  automática de promociones, ni automatización de campañas comerciales.

---

#  Estructura del repositorio

```text
BeautyGirlStudioSmartDataSuite/

├── data/
│   ├── raw/            # Excel originales -- NUNCA se versiona (.gitignore)
│   ├── local/           # id_bridge_local.parquet (con PII) -- NUNCA se versiona
│   ├── processed/       # Parquet limpios, sin PII
│   ├── warehouse/       # beauty_studio.db (SQLite)
│   ├── gold/             # gold_visitas, gold_cliente_snapshot, model_input, scoring_actual
│   └── models/           # rf_calibrado.joblib, rf_base.joblib, model_meta.json
│
├── docs/
│   ├── architecture/
│   │   └── contrato_analitico.md   # fuente única de verdad del proyecto
│   ├── entregas/
│   │   ├── 01_ideas_producto.md ... 05_diseno_frontal.md   (evaluadas por el tutor)
│   │   └── 06_data_profiling.md ... 15_dashboard.md         (implementación)
│   └── assets/
│       ├── 05_mockup_frontal.png
│       ├── eda/           # gráficos del paso 7
│       ├── model/         # gráficos del paso 9
│       └── eval/          # gráficos del paso 10
│
├── src/
│   ├── identity/         # resolve_identity.py
│   ├── cleaning/         # clean_normalize.py
│   ├── warehouse/        # build_warehouse.py
│   ├── gold/              # build_gold.py
│   ├── eda/               # run_eda.py
│   ├── features/         # build_features.py
│   ├── model/             # train_model.py, evaluar_modelo.py, persistir_modelo.py
│   └── dashboard/         # score_clientas.py
│
├── dashboard/
│   └── app.py             # aplicación Streamlit
│
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
└── LICENSE
```

---

#  Fuentes de datos

- Aplicación de gestión de citas (`clientes.xlsx`, `reservas.xlsx`)
- Módulo de ventas (`ventas.xlsx`, `items.xlsx`, `transacciones.xlsx`)
- Catálogo de servicios (`servicios.xlsx`)

Fuentes futuras (no incluidas en el MVP): API meteorológica, calendario de festivos, métricas de Instagram, eventos locales.

**Alerta pendiente de validada con la propietaria** (ver `docs/entregas/06_data_profiling.md` §6): `items.xlsx` no registra ningún ítem de bisutería, aunque el negocio también la vende — se vende por otro canal no incluido en esta exportación.

---

#  Stack tecnológico

## Ingeniería de Datos
Python · Pandas · NumPy · SQLite · Apache Parquet (pyarrow)

## Ciencia de Datos
Scikit-learn 1.5.x (fijado por compatibilidad con `CalibratedClassifierCV(cv="prefit")`, ver `requirements.txt`) · SHAP (explicabilidad) · SciPy

## Visualización
Matplotlib · Seaborn · Plotly · Streamlit

## Desarrollo
Git · GitHub · python-dotenv (`.env`) · joblib (persistencia de modelo)

---

#  Privacidad

- Ningún dato personal (nombre, email, teléfono, RUT, dirección, fecha de nacimiento) sale de `data/raw/` o de `data/local/id_bridge_local.parquet` (ambos excluidos del repositorio).
- Identidad de cliente resuelta mediante `id_cliente_anon` (hash irreversible con salt) + `codigo_display` (4 dígitos, solo para mostrar en el dashboard, nunca usado como clave de unión).
- El salt de anonimización (`ID_SALT`) vive únicamente en un `.env` local, fuera del repositorio y fuera de cualquier entrega o publicación; el repositorio y las entregas del MVP solo incluyen `.env.example`, sin valores reales.
- Verificación de ausencia de PII aplicada **por contenido de celda, no solo por nombre de columna** — tras detectar en el paso 4 que un campo con nombre neutro (`clave_venta`) llevaba un nombre de clienta en texto plano sin hashear.
- El repositorio es público con fines académicos; los datos originales de Beauty Girl Studio no se publican.

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
- [x] Capa Gold (diseño)

## Fase 3 — Ingeniería de Datos
- [x] Data Profiling
- [x] Resolución de identidad y anonimización
- [x] Limpieza y normalización
- [x] Construcción del Data Warehouse
- [x] Construcción de la capa Gold (implementación)

## Fase 4 — Ciencia de Datos
- [x] EDA
- [x] Feature Engineering
- [x] Modelo de retorno (entrenamiento y comparación)
- [x] Validación, análisis de errores y umbrales de riesgo

## Fase 5 — Producto
- [x] Dashboard (Streamlit) conectado a datos y modelo reales
- [x] Exportación CSV, Excel y PDF
- [x] Auditoría final de cierre (datos, contrato, seguridad, dashboard, README)
- [ ] Persistencia de exclusión de clientas
- [x] Validación con Beauty Girl Studio

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