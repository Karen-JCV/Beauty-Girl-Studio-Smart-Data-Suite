# Entrega 3 - Modelo de datos y diseño de la capa Gold

**Máster en Data Science & AI**  
**Tarea:** Entrega 3 - Modelo de datos y diseño de la capa Gold
**Proyecto:** Beauty Girl Studio Smart Data Suite  
**Fecha de entrega:** 18 de Julio de 2026

---

# 1. Resumen de la idea y datos del proyecto

## 1.1 Contexto del proyecto

Beauty Girl Studio es un centro de estética ubicado en Santiago de Chile especializado principalmente en servicios de manicura, extensión de uñas, cejas, pestañas y venta de accesorios. Durante los últimos años el negocio ha experimentado un crecimiento sostenido, incorporando una aplicación para la gestión de citas, un programa de fidelización de clientes y una estrategia activa de comunicación mediante Instagram.

Actualmente el negocio genera una cantidad considerable de información relacionada con clientes, reservas, servicios, pagos y comportamiento comercial. Sin embargo, estos datos únicamente son utilizados como soporte operativo y no forman parte del proceso de toma de decisiones.

Como consecuencia, decisiones relacionadas con promociones, horarios, fidelización, rentabilidad o planificación continúan realizándose de forma manual y basadas principalmente en la experiencia de la propietaria.

El objetivo del presente proyecto consiste en transformar estos datos en un activo estratégico mediante el desarrollo de una plataforma inteligente denominada **Beauty Girl Studio Smart Data Suite**, capaz de proporcionar información analítica y modelos predictivos que faciliten la gestión del negocio.

---

## 1.2 Problema que resuelve

Actualmente el negocio dispone de distintas fuentes de información que funcionan de manera independiente.

Entre ellas se encuentran:

- Aplicación de gestión de citas
- Base de datos de clientes
- Historial de servicios
- Historial de transacciones
- Programa de fidelización
- Información pública de Instagram

Aunque todas estas fuentes contienen información valiosa, presentan diversos problemas comunes en pequeñas empresas:

- Duplicidad de clientes
- Ausencia de identificadores únicos
- Información incompleta
- Diferencias de formato
- Falta de integración entre sistemas
- Inexistencia de indicadores de negocio

Como resultado, responder preguntas aparentemente sencillas requiere un importante trabajo manual.

Por ejemplo:

- ¿Quiénes son los clientas con mayor probabilidad de abandonar el negocio?
- ¿Qué servicios generan mayor rentabilidad?
- ¿Qué horarios presentan menor ocupación?
- ¿Qué promociones funcionan mejor?
- ¿Qué perfil de cliente responde mejor a determinadas campañas?

Actualmente estas preguntas no pueden responderse utilizando únicamente la aplicación de reservas.

---

## 1.3 Solución propuesta

Para resolver este problema se propone el desarrollo de una arquitectura de datos orientada a analítica, construida siguiendo principios de Data Engineering y Business Intelligence.

La solución consistirá en diseñar un flujo de procesamiento capaz de integrar todas las fuentes de información disponibles, limpiarlas, normalizarlas y transformarlas en un conjunto de datasets analíticos preparados para alimentar procesos posteriores de:

- Análisis exploratorio de datos (EDA)
- Construcción de modelos predictivos
- Segmentación de clientes
- Dashboards ejecutivos
- Generación automática de recomendaciones mediante Inteligencia Artificial Generativa

La arquitectura propuesta permitirá que cualquier nuevo dato incorporado por el negocio pueda integrarse de forma sencilla sin necesidad de modificar el diseño general del sistema.

Este enfoque convierte la arquitectura de datos en uno de los principales activos del proyecto y garantiza su escalabilidad conforme el negocio continúe creciendo.

---

## 1.4 Objetivos de la arquitectura de datos

La arquitectura propuesta persigue cinco objetivos principales.

### Objetivo 1

Centralizar toda la información del negocio en una única estructura organizada y consistente.

---

### Objetivo 2

Eliminar problemas de calidad derivados de registros duplicados, formatos inconsistentes y datos incompletos.

---

### Objetivo 3

Construir un modelo de datos reutilizable para cualquier análisis futuro, evitando depender de múltiples hojas Excel independientes.

---

### Objetivo 4

Facilitar el entrenamiento de modelos de Machine Learning mediante datasets específicamente preparados para analítica.

---

### Objetivo 5

Proporcionar una base sólida para la incorporación futura de nuevas funcionalidades, como asistentes inteligentes, recomendadores personalizados o nuevas sucursales del negocio.

---

# 2. Tecnología y formato de almacenamiento

## 2.1 Principios de diseño

Uno de los objetivos principales del proyecto consiste en construir una arquitectura sencilla pero profesional, evitando soluciones excesivamente complejas para el tamaño actual del negocio y al mismo tiempo, permitiendo que la solución pueda evolucionar sin necesidad de rediseñar completamente la infraestructura.

Por este motivo, se ha optado por utilizar una arquitectura basada en distintos formatos de almacenamiento según la etapa del ciclo de vida del dato.

Cada formato ha sido seleccionado en función de su propósito específico.

---

## 2.2 Arquitectura tecnológica propuesta

| Capa | Tecnología | Justificación |
|-------|------------|---------------|
| Captura | Excel | Formato original exportado desde la aplicación de reservas |
| Raw | Excel / CSV | Conservación íntegra del dato original |
| Processed | Apache Parquet | Mayor velocidad de lectura, menor tamaño y mejor integración con Pandas |
| Data Warehouse | SQLite | Base de datos relacional ligera, suficiente para el volumen del proyecto |
| Gold | Parquet | Consumo eficiente por modelos de Machine Learning y dashboards |
| Visualización | Streamlit / Plotly | Desarrollo del producto final |

---

## 2.3 Justificación tecnológica

Aunque actualmente toda la información del negocio puede exportarse en formato Excel, trabajar directamente sobre estos archivos presenta importantes limitaciones.

Entre ellas destacan:

- Dificultad para mantener versiones
- Baja eficiencia de lectura
- Ausencia de relaciones entre tablas
- Elevado riesgo de modificaciones manuales
- Escasa trazabilidad del dato

Por ello, el proyecto utilizará Excel únicamente como mecanismo de extracción desde la fuente original.

Una vez obtenidos los datos, éstos serán transformados progresivamente hasta almacenarse en formatos optimizados para análisis.

El flujo general será el siguiente.

```text
Aplicación de reservas
        │
        ▼
 Exportación Excel
        │
        ▼
      Raw Layer
        │
        ▼
 Limpieza y validación
        │
        ▼
 Processed Layer
        │
        ▼
   SQLite Data Warehouse
        │
        ▼
     Gold Datasets
        │
        ▼
EDA · Machine Learning · Dashboard · IA Generativa
```

Este enfoque permite mantener una separación clara entre los datos originales y las transformaciones realizadas durante el proyecto.

---

## 2.4 Escalabilidad de la arquitectura

Aunque actualmente Beauty Girl Studio opera como un único centro de estética, el modelo propuesto ha sido diseñado pensando en el crecimiento futuro del negocio.

La arquitectura permitirá incorporar sin modificaciones estructurales:

- Nuevas sucursales
- Nuevos profesionales
- Nuevos servicios
- Nuevas fuentes de datos
- Integración con APIs
- Integración con WhatsApp Business
- Integración con sistemas ERP o CRM

Del mismo modo, la sustitución futura de SQLite por PostgreSQL o cualquier otro sistema gestor de bases de datos podrá realizarse sin modificar la lógica analítica desarrollada durante el proyecto.

Esta decisión garantiza que la inversión realizada durante el Trabajo Fin de Máster pueda evolucionar posteriormente hacia una solución empresarial.

---

# 3. Arquitectura de capas de datos

## 3.1 Filosofía de la arquitectura

La arquitectura propuesta sigue una aproximación inspirada en los principios de los modernos Data Lakehouse, adaptada al tamaño y necesidades del proyecto.

Aunque el volumen actual de información no requiere una infraestructura Big Data, adoptar esta metodología desde el inicio aporta importantes ventajas:

- Separación entre datos originales y transformados
- Trazabilidad completa del dato
- Facilidad para reproducir procesos
- Reutilización de datasets
- Escalabilidad futura

La estructura general del proyecto será la siguiente.

```text
data/

│

├── raw/

│      clientes.xlsx

│      servicios.xlsx

│      transacciones.xlsx

│      price_updater.xlsx

│      instagram/

│

├── processed/

│      clientes_clean.parquet

│      servicios_clean.parquet

│      transacciones_clean.parquet

│      calendario.parquet

│

├── warehouse/

│      beauty_studio.db

│

└── gold/

       dim_cliente.parquet

       dim_servicio.parquet

       dim_fecha.parquet

       fact_citas.parquet

       fact_transacciones.parquet

       gold_customer_analytics.parquet

       gold_daily_metrics.parquet

       gold_service_metrics.parquet
```

Esta estructura constituye el contrato de datos del proyecto y será utilizada durante todas las fases posteriores del TFM.

---

## 3.2 Capa Raw

La capa **Raw** almacenará los datos exactamente como son exportados desde cada una de las fuentes originales.

No se realizarán modificaciones sobre estos archivos, salvo aquellas estrictamente necesarias para garantizar su almacenamiento.

Esta capa actuará como respaldo permanente del dato original y permitirá reconstruir cualquier transformación realizada posteriormente.

Las principales fuentes serán:

- Aplicación de gestión de reservas
- Base de datos de clientes
- Catálogo de servicios
- Historial de transacciones
- Actualización de precios
- Información pública de Instagram (cuando sea incorporada)

## 3.3 Capa Processed

La capa **Processed** constituye el primer nivel de transformación de los datos y tiene como objetivo convertir la información operativa proveniente de las distintas fuentes en conjuntos de datos consistentes, homogéneos y preparados para su integración.

A diferencia de la capa Raw, en esta etapa sí se realizarán procesos de limpieza, normalización y enriquecimiento.

Entre las transformaciones previstas se encuentran:

- Eliminación de registros duplicados
- Estandarización de formatos de fecha
- Normalización de teléfonos
- Limpieza de nombres de clientes
- Eliminación de espacios y caracteres especiales
- Tratamiento de valores nulos
- Homologación de categorías de servicios
- Validación de precios
- Creación de claves temporales
- Generación de variables derivadas

El objetivo principal es garantizar que toda la información utilizada posteriormente posea una calidad suficiente para alimentar modelos analíticos.

Los principales datasets de esta capa serán:

| Dataset | Descripción |
|----------|-------------|
| clientes_clean | Clientes normalizados y depurados |
| servicios_clean | Catálogo de servicios normalizado |
| transacciones_clean | Historial de pagos normalizado |
| calendario | Calendario enriquecido con variables temporales |
| promociones | Historial de promociones disponibles |
| instagram_metrics | Métricas públicas de publicaciones (fase futura) |

---

## 3.4 Data Warehouse

Una vez finalizado el proceso de limpieza, los datos serán integrados dentro de un Data Warehouse relacional implementado mediante SQLite.

La utilización de una base de datos relacional ofrece importantes ventajas frente al trabajo directo sobre hojas Excel:

- Relaciones explícitas entre entidades
- Integridad referencial
- Consultas SQL
- Facilidad para generar indicadores
- Reutilización de datos
- Preparación para futuras migraciones hacia PostgreSQL u otras

El Data Warehouse actuará como la fuente oficial de información para todos los procesos analíticos desarrollados durante el proyecto.

---

# 4. Modelo dimensional

## 4.1 Justificación

Aunque los datos originales provienen de un sistema transaccional, los modelos de Ciencia de Datos no deben construirse directamente sobre dichas tablas.

Los sistemas operacionales están optimizados para registrar eventos, mientras que los sistemas analíticos deben optimizar la consulta, el cálculo de indicadores y el entrenamiento de modelos predictivos.

Por este motivo se propone utilizar un modelo dimensional basado en un esquema estrella (*Star Schema*).

Este tipo de arquitectura presenta múltiples ventajas:

- Consultas más sencillas
- Mayor velocidad de agregación
- Reutilización de dimensiones
- Facilidad para construir dashboards
- Compatibilidad con herramientas BI
- Preparación para Machine Learning

---

## 4.2 Esquema general

El modelo dimensional estará compuesto por tablas de dimensiones y tablas de hechos.

```text
                  dim_fecha
                      │
                      │
                      │
dim_cliente ───── fact_citas ───── dim_servicio
      │               │
      │               │
      └───────── fact_transacciones
```

Este diseño permitirá analizar el negocio desde distintas perspectivas sin duplicar información.

---

# 5. Diseño de dimensiones

Las dimensiones representan las entidades principales del negocio.

Serán utilizadas por todas las tablas de hechos y por los modelos analíticos posteriores.

---

## 5.1 Dimensión Cliente

Esta será probablemente la dimensión más importante del proyecto.

Uno de los principales problemas detectados durante el análisis preliminar consiste en la existencia de múltiples registros duplicados para una misma clienta.

Ejemplos observados:

- Diferencias en la escritura del nombre
- Teléfonos con distintos formatos
- Registros sin correo electrónico
- Registros creados varias veces
- Clientes identificados únicamente mediante un apodo

Por ello, la construcción de esta dimensión no consistirá simplemente en copiar la tabla original, sino en generar un **cliente canónico**.

Cada clienta dispondrá de un único identificador interno generado por el proyecto.

La estructura propuesta será:

| Campo | Descripción |
|---------|-------------|
| id_cliente | Identificador interno generado |
| nombre | Nombre normalizado |
| apellido | Apellido normalizado |
| telefono | Teléfono estandarizado |
| email | Correo electrónico |
| fecha_alta | Primera fecha registrada |
| ciudad | Ciudad |
| comuna | Comuna |
| fecha_nacimiento | Fecha de nacimiento (por definir)|
| genero | Género |
| cliente_activo | Indicador de actividad |

Esta dimensión sustituirá completamente a la tabla original durante el resto del proyecto.

---

## 5.2 Estrategia de deduplicación

La calidad de cualquier modelo predictivo depende directamente de la calidad de los datos utilizados durante el entrenamiento.

En consecuencia, antes de construir la dimensión Cliente será necesario implementar un proceso específico de resolución de duplicados.

La estrategia propuesta será progresiva.

### Nivel 1

Coincidencia exacta por correo electrónico.

---

### Nivel 2

Coincidencia exacta por teléfono una vez normalizado.

---

### Nivel 3

Coincidencia aproximada utilizando algoritmos de similitud textual.

Por ejemplo:

- Levenshtein Distance
- Fuzzy Matching
- RapidFuzz

---

### Nivel 4

Validación manual de los casos ambiguos.

Este procedimiento permitirá reducir significativamente la duplicidad existente sin comprometer la calidad de los datos.

---

## 5.3 Dimensión Servicio

Esta dimensión contendrá el catálogo único de todos los servicios ofrecidos por Beauty Girl Studio.

Aunque la aplicación ya proporciona un identificador de servicio, durante el proceso de limpieza se verificará su consistencia y permanencia en el tiempo.

La dimensión incluirá:

| Campo | Descripción |
|---------|-------------|
| id_servicio | Identificador del servicio |
| nombre | Nombre comercial |
| categoria | Categoría principal |
| precio | Precio vigente |
| duracion | Duración estimada |
| reserva_online | Disponible online |
| iva | Aplica IVA |
| servicio_domicilio | Servicio a domicilio (por definir con la propietaria) |

Esta dimensión permitirá realizar análisis por categorías y estudiar la rentabilidad individual de cada servicio.

---

## 5.4 Dimensión Fecha

Aunque pueda parecer una dimensión sencilla, disponer de una tabla calendario facilita enormemente el análisis temporal.

Su estructura incluirá variables derivadas como:

| Campo | Descripción |
|---------|-------------|
| fecha | Fecha |
| año | Año |
| trimestre | Trimestre |
| mes | Mes |
| nombre_mes | Nombre del mes |
| semana | Semana del año |
| dia | Día |
| dia_semana | Día de la semana |
| fin_semana | Indicador booleano |
| festivo | Indicador de festivo |
| estacion | Estación del año |

Esta dimensión permitirá incorporar posteriormente variables externas como meteorología o eventos especiales.

---

# 6. Diseño de tablas de hechos

Las tablas de hechos representan los eventos ocurridos dentro del negocio.

Cada fila corresponde a una transacción o actividad registrada.

---

## 6.1 Fact Citas

Esta será la tabla central del modelo dimensional.

Cada registro representará una cita realizada por una clienta.

Su estructura preliminar será:

| Campo | Descripción |
|---------|-------------|
| id_cita | Identificador de la cita |
| id_cliente | FK Cliente |
| id_servicio | FK Servicio |
| id_fecha | FK Fecha |
| precio | Precio aplicado |
| duración | Tiempo estimado |
| estado | Confirmada, cancelada, realizada |
| profesional | Profesional asignado |
| canal_reserva | App, presencial u otro |

Esta tabla permitirá calcular indicadores operativos como:

- Ocupación diaria
- Demanda por servicio
- Cancelaciones
- Tiempo promedio de atención
- Productividad

---

## 6.2 Fact Transacciones

Esta tabla almacenará todas las operaciones económicas registradas.

Cada fila representará un pago.

Campos previstos:

| Campo | Descripción |
|---------|-------------|
| id_transaccion | Identificador |
| id_cliente | FK Cliente |
| id_fecha | FK Fecha |
| monto | Importe pagado |
| propina | Propina |
| metodo_pago | Medio de pago |
| estado_pago | Estado |
| comprobante | Código de comprobante |

Esta información permitirá construir posteriormente indicadores financieros y calcular ingresos por cliente, servicio o período.

# 7. Diseño de la capa Gold

## 7.1 Objetivo de la capa Gold

La capa **Gold** representa el nivel más alto de madurez de los datos dentro de la arquitectura propuesta.

Mientras que la capa Raw conserva la información original y la capa Processed se ocupa de la limpieza y normalización, la capa Gold contiene datos preparados específicamente para responder preguntas de negocio en este proyecto y alimentar procesos de analítica avanzada.

Los datasets Gold no serán una copia de las tablas operacionales, sino una representación optimizada para facilitar:

- Análisis exploratorio de datos (EDA)
- Construcción de indicadores de negocio
- Entrenamiento de modelos predictivos
- Segmentación de clientes
- Cuadros de mando interactivos
- Generación de recomendaciones mediante Inteligencia Artificial Generativa

Cada dataset Gold responde a un objetivo analítico concreto y puede evolucionar de manera independiente sin afectar al resto de la arquitectura.

---

## 7.2 Principios de diseño

La construcción de la capa Gold seguirá los siguientes principios:

- Cada dataset debe responder a una pregunta de negocio claramente definida.
- Las tablas estarán desnormalizadas cuando ello facilite el análisis.
- Se minimizará la duplicación de información.
- Todas las métricas serán reproducibles.
- Las variables calculadas estarán documentadas.
- Los datasets podrán utilizarse directamente en herramientas de Machine Learning.

---

# 8. Datasets Gold

En lugar de construir un único dataset analítico, se diseñarán varios conjuntos de datos especializados.

Este enfoque facilita la reutilización de la información y permite que cada modelo utilice únicamente las variables necesarias.

---

## 8.1 Gold Customer Analytics

Este dataset constituye el principal activo analítico del proyecto.

Cada fila representa un cliente único y resume toda su relación histórica con Beauty Girl Studio.

Este conjunto de datos servirá como base para:

- Segmentación de clientes
- Cálculo del Customer Lifetime Value
- Predicción de abandono
- Campañas personalizadas
- IA Generativa

### Estructura propuesta

| Campo | Descripción |
|---------|-------------|
| id_cliente | Identificador único |
| primera_visita | Fecha de la primera cita |
| ultima_visita | Fecha de la última cita |
| dias_desde_ultima_visita | Antigüedad de la última visita |
| numero_visitas | Total de citas realizadas |
| numero_cancelaciones | Total de cancelaciones |
| tasa_cancelacion | Cancelaciones / citas |
| gasto_total | Ingreso generado |
| ticket_promedio | Gasto medio por visita |
| servicio_favorito | Servicio más frecuente |
| categoria_favorita | Categoría predominante |
| frecuencia_media | Días entre visitas |
| utiliza_promociones | Sí / No |
| utiliza_pack | Sí / No |
| fidelizacion | Participa en programa |
| clv_estimado | Customer Lifetime Value |
| riesgo_abandono | Bajo / Medio / Alto |
| segmento | Segmento comercial |

---

### Indicadores derivados

A partir de este dataset podrán calcularse métricas como:

- Valor medio por clienta
- Recurrencia
- Porcentaje de retención
- Probabilidad de abandono
- Distribución de clientes por segmentos
- Rentabilidad por perfil de cliente

---

## 8.2 Gold Daily Metrics

Este dataset resumirá el comportamiento operativo del negocio día a día.

Cada fila representará una fecha.

### Estructura

| Campo | Descripción |
|---------|-------------|
| fecha | Día analizado |
| numero_citas | Total de reservas |
| numero_cancelaciones | Cancelaciones |
| tasa_cancelacion | % cancelaciones |
| ingresos | Ingresos diarios |
| ticket_medio | Ticket promedio |
| clientes_unicos | Número de clientas |
| servicio_mas_vendido | Servicio principal |
| categoria_principal | Categoría dominante |
| ocupacion | Horas ocupadas |
| ingresos_promociones | Ventas en promoción |

---

### Utilidad

Este dataset permitirá desarrollar modelos de:

- Predicción de demanda
- Series temporales
- Análisis de estacionalidad
- Planificación de recursos

Además, servirá como fuente principal para los dashboards ejecutivos.

---

## 8.3 Gold Service Metrics

Cada fila representará un servicio del catálogo.

Su objetivo será analizar la rentabilidad y popularidad de los tratamientos ofrecidos.

### Estructura

| Campo | Descripción |
|---------|-------------|
| id_servicio | Identificador |
| nombre | Servicio |
| categoria | Categoría |
| precio_actual | Precio vigente |
| duracion | Tiempo estimado |
| numero_ventas | Total vendido |
| ingresos | Facturación acumulada |
| ticket_promedio | Ticket medio |
| porcentaje_ventas | Participación |
| margen_estimado | Indicador económico (si existiera información) |
| ranking | Popularidad |

---

### Aplicaciones

Este dataset permitirá:

- Identificar servicios estrella
- Detectar servicios poco rentables
- Optimizar promociones
- Analizar tendencias de consumo

---

## 8.4 Gold Business KPIs

Aunque los dashboards pueden calcular indicadores en tiempo real, disponer de un dataset específico simplifica el desarrollo del producto final.

Este dataset almacenará los principales indicadores ejecutivos.

### Variables

- Ingresos mensuales
- Ingresos anuales
- Ocupación
- Ticket promedio
- Cancelaciones
- Retención
- Nuevas clientas
- Clientes recurrentes
- Servicios más vendidos
- Promociones más utilizadas

---

# 9. Variables derivadas

Uno de los aspectos más importantes del proyecto consistirá en la creación de nuevas variables a partir de los datos originales.

Estas variables incrementarán significativamente la capacidad predictiva de los modelos.

## Variables temporales

- Día de la semana
- Semana del año
- Mes
- Trimestre
- Estación
- Festivo
- Víspera de festivo

---

## Variables de comportamiento

- Frecuencia media de visita
- Tiempo desde la última visita
- Tiempo entre citas
- Cliente recurrente
- Cliente nuevo
- Cliente inactivo

---

## Variables económicas

- Gasto acumulado
- Ticket medio
- Porcentaje de promociones utilizadas
- Gasto anual
- Gasto mensual
- Ingresos por categoría

---

## Variables comerciales

- Categoría favorita
- Servicio favorito
- Número de promociones utilizadas
- Participación en programa de fidelización
- Campañas respondidas (si existieran datos)

---

## Variables predictivas

Estas variables serán utilizadas posteriormente por los modelos de Machine Learning.

Entre ellas:

- Riesgo de abandono
- Probabilidad de cancelación
- Propensión a utilizar promociones
- Probabilidad de recompra
- Customer Lifetime Value (CLV)
- Score de fidelización

Estas variables no existirán inicialmente en los datos originales, sino que serán generadas durante el proceso de ingeniería de características (*Feature Engineering*).

---

# 10. Preparación para Machine Learning

Uno de los objetivos fundamentales de la arquitectura propuesta consiste en facilitar el entrenamiento de modelos predictivos.

Por este motivo, la capa Gold ha sido diseñada para minimizar el trabajo de preparación de datos previo al modelado.

Cada dataset incluirá variables limpias, homogéneas y documentadas, permitiendo reutilizar la misma información en diferentes algoritmos sin necesidad de repetir transformaciones.

Entre los modelos previstos para el proyecto destacan:

| Objetivo | Modelo propuesto |
|----------|------------------|
| Predicción de cancelaciones | Regresión Logística / Random Forest |
| Predicción de demanda | Prophet / Random Forest Regressor |
| Segmentación de clientas | K-Means |
| Riesgo de abandono | Gradient Boosting |
| Predicción de ingresos | Regresión Lineal |

La utilización de una arquitectura desacoplada permitirá sustituir cualquiera de estos modelos sin necesidad de modificar la estructura del Data Warehouse.

---

# 11. Preparación para Inteligencia Artificial Generativa

Uno de los elementos diferenciadores del proyecto será la incorporación de modelos de Inteligencia Artificial Generativa como complemento a los modelos tradicionales de Ciencia de Datos.

Es importante destacar que el modelo LLM no sustituirá a los modelos predictivos desarrollados, sino que utilizará sus resultados para generar contenido de valor para el negocio.

El flujo de funcionamiento previsto será el siguiente:

```text
Datos históricos
        │
        ▼
Modelo de Machine Learning
        │
Predicciones y métricas
        │
        ▼
Modelo LLM
        │
        ▼
Recomendaciones comerciales
Campañas personalizadas
Mensajes para Instagram
Promociones sugeridas
Resumen ejecutivo para la propietaria
```

Este enfoque permite combinar las fortalezas de la analítica predictiva con la capacidad de los modelos generativos para transformar datos complejos en información fácilmente interpretable y accionable.

# 12. Calidad de los datos

## 12.1 Estado inicial de la información

A partir del análisis preliminar de los datos exportados desde la aplicación de gestión del negocio, se identificaron diversos problemas de calidad que deberán resolverse antes del desarrollo de cualquier modelo analítico.

Estos problemas son habituales en sistemas operacionales cuyo objetivo principal es registrar información y no realizar análisis estadísticos.

Los principales hallazgos fueron:

- Registros duplicados de clientes
- Formatos inconsistentes en números telefónicos
- Nombres escritos de distintas formas
- Registros sin correo electrónico
- Información demográfica incompleta
- Ausencia de claves foráneas explícitas entre tablas
- Posibles inconsistencias entre catálogos históricos de servicios

Aunque estas limitaciones representan un desafío técnico, también constituyen una oportunidad para aplicar procesos de Ingeniería de Datos que incrementen significativamente el valor de la información disponible.

---

## 12.2 Estrategia de limpieza

El proceso de limpieza seguirá un flujo estructurado compuesto por varias etapas.

### Validación estructural

Se comprobará:

- Tipos de datos
- Formatos de fecha
- Registros vacíos
- Valores fuera de rango

---

### Normalización

Se aplicarán procesos como:

- Conversión de teléfonos a formato internacional
- Eliminación de espacios adicionales
- Unificación de mayúsculas y minúsculas
- Estandarización de categorías

---

### Resolución de duplicados

Los clientes serán deduplicados utilizando como fue antes mencionado una estrategia jerárquica basada en:

1. Correo electrónico
2. Teléfono
3. Similitud del nombre
4. Validación manual

---

### Enriquecimiento

Durante esta fase se crearán variables derivadas que no existen originalmente en la aplicación.

Ejemplos:

- Antigüedad del cliente
- Frecuencia de visitas
- Tiempo desde la última reserva
- Ticket medio
- Categoría favorita

---

# 13. Estrategia de identificación de clientes

Uno de los principales retos del proyecto consiste en construir un identificador único para cada cliente.

La aplicación utilizada actualmente por Beauty Girl Studio permite registrar clientes utilizando distintos criterios, lo que provoca que una misma persona pueda aparecer varias veces dentro de la base de datos.

Por ejemplo:

- Utilizando únicamente un nombre
- Utilizando un apodo
- Utilizando solamente el teléfono
- Utilizando posteriormente un correo electrónico

Desde una perspectiva analítica, esta situación genera importantes problemas.

Entre ellos:

- Cálculo incorrecto del número de clientes
- Duplicación de ingresos
- Segmentaciones erróneas
- Modelos predictivos menos precisos

Para resolver esta situación se generará un identificador interno denominado:

```text
customer_master_id
```

Este identificador será independiente del sistema de reservas y será utilizado por todas las tablas del proyecto.

De esta manera, cualquier cambio futuro en la aplicación utilizada por el negocio no afectará a la estructura analítica desarrollada.

---

# 14. Riesgos identificados

Todo proyecto de Ciencia de Datos depende directamente de la calidad de la información disponible.

Durante esta etapa se identifican los siguientes riesgos.

| Riesgo | Impacto | Mitigación |
|---------|----------|------------|
| Clientes duplicados | Alto | Algoritmos de deduplicación |
| Datos incompletos | Medio | Imputación y limpieza |
| Relaciones no documentadas | Alto | Ingeniería inversa y análisis exploratorio |
| Cambios en la aplicación de reservas | Medio | Arquitectura desacoplada |
| Crecimiento del negocio | Bajo | Modelo dimensional escalable |

---

# 15. Escalabilidad

Aunque actualmente Beauty Girl Studio opera como una pequeña empresa, la arquitectura propuesta ha sido diseñada siguiendo principios utilizados en proyectos empresariales de mayor escala.

La incorporación de nuevas fuentes de información no requerirá modificaciones importantes en la estructura del proyecto.

Entre las posibles ampliaciones futuras destacan:

- Incorporación de nuevas sucursales
- Incorporación de nuevos profesionales
- Integración con sistemas CRM
- Integración con plataformas de marketing
- Conexión con WhatsApp Business
- Análisis automático de reseñas
- Visión por computador aplicada a diseños de uñas
- Análisis de imágenes mediante modelos multimodales
- Motores de recomendación personalizados

Asimismo, el reemplazo futuro de SQLite por PostgreSQL, SQL Server o cualquier otro gestor relacional podrá realizarse sin modificar el modelo dimensional propuesto.

Esta característica garantiza la sostenibilidad técnica del proyecto a largo plazo.

---

# 16. Roadmap técnico del proyecto

La arquitectura propuesta servirá como base para el resto del Trabajo Fin de Máster.

Las siguientes fases del proyecto seguirán el siguiente orden.

```text
Comprensión del negocio
            │
            ▼
Obtención de datos
            │
            ▼
Data Profiling
            │
            ▼
Limpieza y normalización
            │
            ▼
Construcción del Data Warehouse
            │
            ▼
Generación de datasets Gold
            │
            ▼
Análisis Exploratorio (EDA)
            │
            ▼
Feature Engineering
            │
            ▼
Modelos Predictivos
            │
            ▼
Evaluación
            │
            ▼
Dashboard Ejecutivo
            │
            ▼
Integración con IA Generativa
            │
            ▼
Beauty Girl Studio Smart Data Suite
```

Cada etapa reutilizará los resultados obtenidos en la fase anterior, favoreciendo la trazabilidad y reproducibilidad del proyecto.

---

# 17. Conclusiones

La arquitectura de datos propuesta no se limita a satisfacer los requisitos de la presente entrega, sino que constituye la base tecnológica sobre la que se desarrollará el resto del Trabajo Fin de Máster.

Frente a un enfoque basado únicamente en hojas de cálculo, la solución planteada incorpora una arquitectura organizada por capas, un modelo dimensional escalable y un conjunto de datasets Gold específicamente diseñados para análisis de negocio y modelos de Machine Learning.

La separación entre datos operacionales, datos procesados y datos analíticos garantiza una mayor calidad de la información y facilita la reutilización de los datos en futuras fases del proyecto.

Asimismo, la incorporación de un Data Warehouse relacional y de un identificador canónico para clientes permite resolver uno de los principales problemas detectados durante el análisis preliminar: la existencia de registros duplicados y la ausencia de relaciones explícitas entre las distintas fuentes de información.

Finalmente, la arquitectura deja preparado el camino para integrar modelos predictivos e Inteligencia Artificial Generativa dentro de una misma plataforma, donde los algoritmos de Ciencia de Datos generarán conocimiento y los modelos LLM transformarán dicho conocimiento en recomendaciones accionables para la propietaria del negocio.

Desde esta perspectiva, **Beauty Girl Studio Smart Data Suite** no se plantea únicamente como un ejercicio académico, sino como una propuesta de transformación digital basada en datos, capaz de evolucionar junto con el crecimiento futuro de la empresa.

---

# 18. Líneas futuras de investigación

Aunque el alcance del Trabajo Fin de Máster se centrará en la construcción de una plataforma analítica para un único centro de estética, la arquitectura desarrollada permitirá abordar futuras líneas de investigación y evolución tecnológica.

Entre ellas destacan:

- Modelos de predicción de abandono basados en aprendizaje profundo
- Sistemas inteligentes de recomendación de servicios personalizados
- Optimización automática de agendas mediante algoritmos de programación
- Incorporación de modelos multimodales para clasificar diseños de uñas a partir de imágenes
- Análisis de sentimiento de reseñas y comentarios en redes sociales
- Integración con asistentes conversacionales para atención automática de clientes
- Sistemas de pricing dinámico basados en ocupación y demanda
- Expansión de la arquitectura hacia múltiples sucursales mediante un Data Warehouse corporativo

Estas posibles ampliaciones refuerzan el carácter escalable de la solución y demuestran que la arquitectura propuesta puede evolucionar desde un proyecto académico hacia una plataforma empresarial orientada a la toma inteligente de decisiones.

---