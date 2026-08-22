# Entrega 3 - Modelo de datos y diseño de la capa Gold

**Máster en Data Science & AI**  
**Tarea:** Entrega 3 - Modelo de datos y diseño de la capa Gold  
**Proyecto:** Beauty Girl Studio Smart Data Suite  
**Fecha de entrega:** 18 de Julio de 2026

---

> **Nota aclaratoria sobre la modificación de esta entrega**  
> Tras la revisión del tutor, se decidió acotar el alcance del proyecto para garantizar su viabilidad dentro del tiempo disponible y la calidad real de los datos.  
>  
> Las versiones anteriores de las entregas 2 y 3 incluían múltiples líneas de análisis (predicción de demanda, cancelaciones, segmentación avanzada, CLV, recomendación y uso de IA generativa) que excedían el volumen, la granularidad y la estabilidad del histórico disponible.  
>  
> Además, el tutor señaló dos aspectos críticos:  
> - La necesidad de **priorizar un único problema predictivo** para el MVP.  
> - La obligación de **proteger la privacidad**, evitando que datos personales lleguen al warehouse o a la capa gold.  
>  
> Por ello, ambas entregas fueron reformuladas para centrarse exclusivamente en un problema acotado, viable y alineado con los datos:  
> **la medición de fidelización mediante RFM y la predicción de probabilidad de retorno de las clientas en un horizonte temporal definido.**  
>  
> Esta modificación mejora la coherencia del proyecto, reduce riesgos metodológicos y garantiza que las siguientes fases (EDA, modelado y dashboard) puedan desarrollarse con rigor y trazabilidad.

---

# 1. Resumen de la idea y datos del proyecto

## 1.1 Problema que resuelve el proyecto

El proyecto se centra en un único problema de negocio: **medir y predecir la probabilidad de retorno de las clientas** de Beauty Girl Studio. El estudio quiere saber qué clientas están fidelizadas, cuáles están en riesgo de abandono y qué patrones de comportamiento se asocian a una mayor recurrencia.

Resolver este problema permite priorizar acciones de fidelización, diseñar promociones dirigidas y tomar decisiones basadas en datos sobre qué perfiles de clientas conviene cuidar más para mantener ingresos recurrentes.

## 1.2 Solución que se quiere construir

La solución consiste en construir una **base analítica de clientas** a partir de los datos reales del negocio (clientes, reservas, ventas, ítems, servicios y transacciones), aplicar un análisis RFM (Recency, Frequency, Monetary) y entrenar un **modelo predictivo de probabilidad de retorno** en un horizonte temporal definido (por ejemplo, 90 días).

El modelo trabajará sobre snapshots de cliente en fechas de referencia, utilizando únicamente información disponible hasta ese momento para evitar fugas de información. A partir de ahí se podrán definir segmentos de fidelización y reglas simples de recomendación. Otras líneas (cancelaciones, demanda, CLV, campañas, LLM) se dejarán explícitamente como **mejoras futuras**.

## 1.3 Fuentes de datos utilizadas

Las fuentes principales del proyecto son:

- **clientes.xlsx**: datos de contacto y alta de clientas.
- **reservas.xlsx**: citas reservadas, estado, prestador, origen.
- **ventas.xlsx**: ventas realizadas, importe y cliente.
- **items.xlsx**: detalle de servicios vendidos por venta.
- **servicios.xlsx**: catálogo de servicios y categorías.
- **transacciones.xlsx**: pagos asociados a ventas.

Cada fuente aporta una parte distinta del comportamiento de las clientas: quiénes son, qué reservan, qué se les realiza, cuánto pagan y con qué frecuencia vuelven.

---

# 2. Tecnología o formato de almacenamiento elegido

## 2.1 Formatos y herramientas

Se utilizará una combinación sencilla y coherente con el volumen de datos:

- **Raw**: ficheros originales en formato **Excel** (`.xlsx`) tal y como se exportan de la aplicación.
- **Processed**: ficheros **Parquet** (`.parquet`) para datos limpios y normalizados, trabajados con **Pandas**.
- **Warehouse**: base de datos relacional **SQLite** (`beauty_studio.db`) para gestionar relaciones y consultas SQL.
- **Gold**: datasets finales en **Parquet**, consumidos por notebooks de EDA y modelos de Machine Learning.

Esta elección permite mantener el formato original para trazabilidad, trabajar de forma eficiente en Python y disponer de un modelo relacional ligero sin introducir complejidad innecesaria.

## 2.2 Justificación

- El volumen de datos (aprox. 1–4 años de histórico, varios miles de citas) es manejable con SQLite y Parquet.
- Parquet ofrece buena compresión y velocidad de lectura para EDA y modelado.
- SQLite es suficiente para definir claves, relaciones y vistas analíticas sin necesidad de un servidor dedicado.
- Excel se mantiene solo como capa de entrada; no se utilizará para análisis ni para la capa gold.

---

# 3. Estructura de capas de datos

La estructura de carpetas seguirá el esquema recomendado:

```text
data/
│
├── raw/
│   clientes.xlsx
│   reservas.xlsx
│   ventas.xlsx
│   items.xlsx
│   servicios.xlsx
│   transacciones.xlsx
│
├── processed/
│   clientes_clean.parquet
│   reservas_clean.parquet
│   ventas_clean.parquet
│   items_clean.parquet
│   servicios_clean.parquet
│   transacciones_clean.parquet
│
├── warehouse/
│   beauty_studio.db
│
└── gold/
    gold_visitas.parquet
    gold_cliente_snapshot.parquet

```

- Raw: datos originales sin modificaciones.
- Processed: datos limpios, con tipos corregidos, fechas normalizadas y categorías homogéneas.
- Warehouse: tablas relacionales con claves primarias y foráneas.
- Gold: datasets analíticos preparados para RFM y modelo de probabilidad de retorno.

# 4. Definición de la capa gold

La capa gold se limitará a dos datasets centrales, alineados con el problema de fidelización y retorno.

## 4.1 Dataset `gold_visitas.parquet`

**Descripción funcional:**  

Tabla de hechos con una fila **por visita realizada y cobrada** (cita efectivamente atendida y asociada a una venta/pago). Es la base para calcular RFM y métricas de comportamiento.

**Granularidad:**  

Una fila por visita de cliente.

**Volumen esperado:**  

Entre 2.000 y 10.000 registros, según histórico disponible.

**Campos principales y tipos:**

- `id_visita (INTEGER)`: identificador interno de la visita (PK).
- `id_cliente_anon (TEXT)`: identificador anonimizado de cliente (FK a dimensión cliente).
- `id_servicio (INTEGER)`: identificador del servicio principal realizado.
- `fecha_visita (DATE)`: fecha de realización de la cita.
- `importe_total (REAL)`: importe total de la visita (venta asociada).
- `categoria_servicio (TEXT)`: categoría (MANICURA RUSA, PEDICURE, etc.).
- `prestador (TEXT)`: profesional que realiza el servicio (opcional en gold si se considera necesario).
- `origen_reserva (TEXT)`: canal de reserva (Manual, Online).
- `estado_pago (TEXT)`: estado del pago (Pagado, No pagada, Pago asociado).

**Clave primaria:**

- `id_visita` como PK.
- `id_cliente_anon` + `fecha_visita` como clave candidata para análisis temporal.

**Uso posterior:**

- EDA de comportamiento de visitas.
- Cálculo de RFM por cliente.
- Construcción de variables de frecuencia y monetarias.
- Base para agregaciones diarias/mensuales si se necesitan.

## 4.2 Dataset gold_cliente_snapshot.parquet

**Descripción funcional:**  

Tabla analítica con una fila por cliente y fecha de referencia, que resume su comportamiento histórico hasta esa fecha y define la variable objetivo de retorno en un horizonte (por ejemplo, 90 días).

**Granularidad:**  

Una fila por cliente y fecha de corte (fecha_referencia).

**Volumen esperado:**  

Entre 500 y 2.000 clientes, con varias fechas de referencia seleccionadas (por ejemplo, cierres trimestrales).

**Campos principales y tipos:**

- `id_cliente_anon (TEXT)`: identificador anonimizado de cliente (PK parcial).
- `fecha_referencia (DATE)`: fecha de corte para el cálculo de variables (PK parcial).
- `recency_dias (INTEGER)`: días desde la última visita hasta fecha_referencia.
- `frequency_visitas (INTEGER)`: número de visitas realizadas hasta fecha_referencia.
- `monetary_total (REAL)`: gasto acumulado hasta fecha_referencia.
- `ticket_medio (REAL)`: gasto medio por visita.
- `primera_visita (DATE)`: fecha de la primera visita registrada.
- `antiguedad_dias (INTEGER)`: días desde la primera visita hasta fecha_referencia.
- `usa_promociones (BOOLEAN)`: indicador de uso de promociones (derivado de servicios/promos).
- `categoria_favorita (TEXT)`: categoría de servicio más frecuente.
- `segmento_rfm (TEXT)`: segmento RFM (por ejemplo, “Top”, “Leales”, “En riesgo”).
- `retorna_en_90_dias (BOOLEAN)`: variable objetivo, indica si el cliente realiza al menos una visita en los 90 días posteriores a fecha_referencia.

**Clave primaria:**

- PK compuesta: `id_cliente_anon` + `fecha_referencia`.

**Uso posterior:**

- Dataset principal para el **modelo de probabilidad de retorno**.
- EDA de fidelización y segmentos de clientas.
- Base para dashboards de fidelización.

## 4.3 Tabla resumen de datasets gold

| Dataset gold | Granularidad | Campos clave | Uso posterior |
| --- | --- | --- | --- |
| ``gold_visitas.parquet`` | Una fila por visita realizada | ``id_visita``, ``id_cliente_anon``, ``fecha_visita`` | EDA, RFM, agregaciones de comportamiento |
| ``gold_cliente_snapshot.parquet`` | Una fila por cliente y fecha de corte | ``id_cliente_anon``, ``fecha_referencia`` | Modelo de retorno, segmentación, dashboard |

# 5. Relaciones entre datos

## 5.1 Tablas principales del warehouse

En `beauty_studio.db` se crearán, al menos, las siguientes tablas:

- `dim_cliente_anon`
- `dim_servicio`
- `fact_reservas`
- `fact_ventas`
- `fact_items`
- `fact_transacciones`

**Claves y relaciones**

- **Cliente:**

    - `dim_cliente_anon.id_cliente_anon` (PK).
    - Se construye a partir de `clientes.xlsx` y de los nombres/emails/teléfonos presentes en reservas, ventas e ítems.
    - Relaciones 1:N con `fact_reservas`, `fact_ventas`, `fact_items`, `fact_transacciones`.

- **Servicio:**

    - `dim_servicio.id_servicio` (PK), proveniente de `servicios.xlsx`.
    - Relación 1:N con `fact_items` (cada ítem referencia un servicio).

- **Venta / Transacción:**

    - `fact_ventas.id_venta` (PK) y `fact_transacciones.id_venta` (FK).
    - Relación 1:1 o 1:N según haya varias transacciones por venta.

- **Reserva:**

    - `fact_reservas.id_reserva` (PK).
    - Se relaciona con ventas/ítems mediante combinación de cliente + fecha + servicio, cuando exista trazabilidad suficiente.

## 5.2 Joins y agregaciones

Para construir `gold_visitas`:

- Join entre `fact_ventas`, `fact_items`, `fact_transacciones` y `dim_cliente_anon`, filtrando solo ventas efectivamente pagadas o con estado de pago válido.
- Agregación por venta para obtener una visita única con importe total y servicio principal.

Para construir `gold_cliente_snapshot`:

- Agregación de `gold_visitas` por cliente hasta cada `fecha_referencia`.
- Cálculo de RFM y variables derivadas.
- Cálculo de la etiqueta `retorna_en_90_dias` utilizando visitas posteriores a la fecha de corte.

# 6. Diccionario de datos inicial

A continuación se presenta un diccionario inicial de los campos más relevantes.

| Campo | Descripción | Tipo de dato | Fuente | Obligatorio | Observaciones |
| --- | --- | --- | --- | --- | --- |
| ``id_cliente_anon`` | Identificador anonimizado de cliente | TEXT | Derivado de clientes/ventas | Sí | Hash o ID interno, sin datos personales |
| ``fecha_visita`` | Fecha de realización de la visita | DATE | ``fact_ventas`` / ``fact_items`` | Sí | Formato ``YYYY-MM-DD`` |
| ``importe_total`` | Importe total de la visita | REAL | ``fact_ventas`` / ``fact_transacciones`` | Sí | Limpieza de moneda y separadores |
| ``id_servicio`` | Identificador del servicio principal | INTEGER | ``dim_servicio`` / ``fact_items`` | Sí | Mapeo consistente con catálogo de servicios |
| ``categoria_servicio`` | Categoría del servicio | TEXT | ``dim_servicio`` | Sí | Valores normalizados (MANICURA RUSA, etc.) |
| ``fecha_referencia`` | Fecha de corte para snapshot de cliente | DATE | Derivado | Sí | Definida en el pipeline de modelado |
| ``recency_dias`` | Días desde la última visita | INTEGER | Derivado de ``gold_visitas`` | Sí | Calculado respecto a ``fecha_referencia`` |
| ``frequency_visitas`` | Número de visitas hasta la fecha de corte | INTEGER | Derivado de ``gold_visitas`` | Sí |  |
| ``monetary_total`` | Gasto acumulado hasta la fecha de corte | REAL | Derivado de ``gold_visitas`` | Sí |  |
| ``retorna_en_90_dias`` | Indicador de retorno en los 90 días siguientes | BOOLEAN | Derivado de ``gold_visitas`` | Sí | Variable objetivo del modelo |

# 7. Problemas de calidad esperados

Aplicados específicamente a las fuentes disponibles:

- **Duplicados de clientes**: misma persona con variaciones en nombre, email o teléfono.
- **Campos vacíos**: clientes sin email, sin teléfono o sin número de cliente.
- **Inconsistencia de nombres**: espacios extra, mayúsculas/minúsculas, apodos.
- **Fechas en distintos formatos**: fechas con formato texto, mezcla de día/mes/año.
- **Importes con separadores de miles y decimales distintos**: 10,000.00, 32,000, etc.
- **Relación incompleta entre reservas y ventas**: no siempre existe un ID común, habrá que inferir relaciones.
- **Cambios de catálogo de servicios**: nombres de servicios que cambian ligeramente a lo largo del tiempo.
- **Cobertura temporal desigual**: más datos completos a partir de abril/mayo 2023, menos calidad en años anteriores.

# 8. Decisiones de limpieza y transformación previstas

- **Anonimización:**

    - Los datos personales (nombre, email, teléfono, RUT, dirección) se mantendrán solo en la capa **raw/processed**.
    - En el **warehouse** y la **capa gold** se utilizará `id_cliente_anon` como identificador, sin información identificable.
    - La fecha de nacimiento se transformará en variables agregadas (por ejemplo, grupo de edad) solo si es necesaria.

- **Valores nulos:**
  
    - Registros sin cliente identificable se analizarán; si no pueden vincularse de forma fiable, se excluirán de la capa gold.
    - Importes nulos o cero se revisarán; ventas sin importe se excluirán del cálculo de RFM.

- **Duplicados:**
  
    - Se aplicará deduplicación de clientes mediante email, teléfono normalizado y similitud de nombre.
    - Se eliminarán ventas/transacciones duplicadas detectadas por ID y fecha.

- **Fechas:**
  
    - Todas las fechas se convertirán a tipo `DATE` con formato `YYYY-MM-DD`.
    - Se crearán columnas derivadas (año, mes, día de la semana) en processed/warehouse si son necesarias.

- **Variables derivadas:**
  
    - RFM (recency, frequency, monetary) por cliente.
    - Antigüedad, ticket medio, categoría favorita.
    - Etiqueta de retorno en 90 días (`retorna_en_90_dias`).
  
- **Criterios de validez:**
  
    - Una visita válida debe tener cliente identificable, fecha de visita y importe positivo.
    - Solo se considerarán para el modelo las clientas con al menos una visita y un horizonte de observación suficiente.

# 9. Riesgos del modelo de datos

- **Parte más clara:**
  
  - La estructura de visitas (`gold_visitas`) y el cálculo de RFM están bien definidos y alineados con el problema de fidelización.
  - La anonimización mediante `id_cliente_anon` permite trabajar de forma segura y coherente con la privacidad.
  
- **Parte con más incertidumbre:**
  
  - La reconstrucción exacta de la relación entre reservas y ventas en todos los casos.
  - La elección de fechas de referencia y horizonte de retorno óptimos (30, 60, 90 días).
  
- **Fuentes más problemáticas:**
  
  - `clientes.xlsx` por duplicados y campos vacíos.
  - `reservas.xlsx` por estados y notas extensas que no siempre se relacionan claramente con ventas.
  
- **Qué ocurriría si no se puede construir la capa gold tal como está definida:**
  
  - Se simplificaría el modelo a un único dataset `gold_visitas` con RFM por cliente y se trabajaría con un modelo más básico de segmentación sin predicción explícita de retorno.
 
- **Alternativa de simplificación:**
 
  - Mantener solo un snapshot por cliente (por ejemplo, a fecha de último año disponible) y construir un modelo de clasificación simple entre “cliente activo” vs “cliente inactivo” sin horizonte temporal explícito, manteniendo la misma arquitectura pero con menos complejidad.