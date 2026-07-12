# Entrega 2 - Selección de idea de proyecto y análisis de datos necesarios

**Máster en Data Science & AI**  
**Tarea:** Entrega 2 - Selección de idea de proyecto y análisis de datos necesarios
**Proyecto:** Beauty Girl Studio Smart Data Suite  
**Fecha de entrega:** 12 de Julio de 2026

---

# 1. Idea seleccionada

## Propósito del proyecto

El propósito de este proyecto es diseñar una plataforma inteligente de apoyo a la toma de decisiones para **Beauty Girl Studio**, un centro de estética especializado principalmente en servicios de uñas, diseño de cejas, venta de bisutería, entre otros. Actualmente el negocio dispone de una aplicación para la gestión de citas que almacena información histórica de las reservas realizadas por las clientas, un programa de fidelización, así como de una presencia consolidada en Instagram, donde comparte sus trabajos y mantiene una alta interacción con su comunidad.

La propuesta consiste en desarrollar **Beauty Girl Studio Smart Data Suite**, una plataforma basada en Ciencia de Datos e Inteligencia Artificial que permita transformar los datos operativos del negocio en conocimiento accionable. El objetivo es facilitar la toma de decisiones mediante modelos predictivos, análisis descriptivos, segmentación de clientes e IA Generativa para apoyar la gestión diaria del negocio.

El proyecto pretende demostrar cómo una pequeña empresa puede aprovechar sus propios datos para mejorar la planificación de recursos, incrementar la fidelización de sus clientas, optimizar campañas comerciales y aumentar la rentabilidad sin necesidad de realizar grandes inversiones tecnológicas.

---

## Problema que resuelve

Muchos pequeños centros de estética utilizan aplicaciones para gestionar sus citas, pero normalmente estas herramientas funcionan únicamente como agendas digitales y no explotan el potencial de los datos que generan diariamente. Esto provoca que decisiones relacionadas con promociones, horarios, campañas comerciales o fidelización se basen principalmente en la experiencia del negocio y no en información objetiva.

Beauty Girl Studio no es una excepción. Aunque dispone de un histórico de aproximadamente un año de reservas, información sobre los servicios contratados, programas de fidelización y una comunidad activa en redes sociales, actualmente estos datos no se analizan de forma sistemática para identificar patrones de comportamiento de las clientas ni para optimizar la gestión del negocio.

Resolver este problema permitirá transformar la información histórica en recomendaciones que apoyen decisiones estratégicas, mejorando la ocupación de la agenda, reduciendo cancelaciones, aumentando la fidelización y ofreciendo una experiencia más personalizada para los clientes.

---

## Solución planteada

La solución propuesta consiste en desarrollar una plataforma de analítica denominada **Beauty Girl Studio Smart Data Suite**, construida desde un enfoque de Ciencia de Datos.

La plataforma integrará información procedente de distintas fuentes del negocio para construir un conjunto de datos que permita aplicar técnicas de análisis exploratorio, visualización, modelos predictivos y segmentación de clientes.

Como complemento, se incorporará un módulo de IA Generativa basado en Large Language Models (LLM) que utilizará la información generada por los modelos analíticos para crear recomendaciones comerciales, campañas personalizadas y propuestas de comunicación dirigidas a diferentes perfiles de clientas.

El objetivo no será sustituir la toma de decisiones humanas, sino proporcionar información útil que facilite la gestión diaria del negocio mediante herramientas de apoyo basadas en datos.

---

## Objetivos estratégicos del proyecto

El desarrollo del proyecto estará orientado a cuatro objetivos principales de negocio.

### Objetivo 1. Optimizar la ocupación del estudio

Analizar el histórico de reservas para identificar patrones temporales y predecir la demanda futura por días y franjas horarias.

Esto permitirá detectar horarios con baja ocupación y planificar promociones específicas que ayuden a mejorar el aprovechamiento de la agenda.

Posibles técnicas:

- Regresión lineal
- Árboles de decisión
- Random Forest Regressor
- Series temporales

---

### Objetivo 2. Mejorar la fidelización de las clientas

Analizar el comportamiento histórico de las clientas para identificar diferentes perfiles según su frecuencia de visita, gasto, utilización de promociones y participación en el programa de fidelización.

El objetivo será facilitar campañas personalizadas para aumentar la retención y el valor de cada cliente.

Posibles técnicas:

- Clustering (K-Means)
- Análisis RFM
- Customer Lifetime Value
- DBSCAN

---

### Objetivo 3. Reducir cancelaciones y ausencias

Construir un modelo capaz de estimar la probabilidad de cancelación de una cita utilizando información histórica sobre comportamiento de los clientes, horarios, tipo de servicio y antelación de la reserva.

Este modelo permitirá actuar preventivamente mediante recordatorios o promociones dirigidas a cubrir posibles huecos en la agenda.

Posibles técnicas:

- Regresión logística
- Random Forest
- Gradient Boosting
- XGBoost

---

### Objetivo 4. Automatizar acciones comerciales mediante IA Generativa

Utilizar un modelo LLM para transformar los resultados obtenidos por los modelos analíticos en contenido útil para el negocio.

Algunos ejemplos serían:

- Campañas personalizadas
- Mensajes promocionales
- Publicaciones para Instagram
- Recomendaciones comerciales
- Propuestas de fidelización

En este proyecto la IA Generativa actuará como una herramienta complementaria a los modelos de Ciencia de Datos, utilizando la información obtenida mediante el análisis para generar contenido adaptado a cada segmento de clientes.

---

## MVP del proyecto final

El producto mínimo viable consistirá en una plataforma interactiva denominada **Beauty Girl Studio Smart Data Suite**.

El MVP incluirá como mínimo:

- Dashboard interactivo con indicadores clave del negocio (KPIs).
- Visualización de ocupación, ingresos y evolución de clientes.
- Modelo predictivo de cancelaciones.
- Modelo predictivo de demanda por días y franjas horarias.
- Segmentación automática de clientas.
- Recomendador de promociones basado en datos.
- Módulo de IA Generativa para crear campañas comerciales personalizadas.

El objetivo es que el usuario pueda visualizar el estado del negocio y recibir recomendaciones generadas automáticamente a partir de los modelos desarrollados.

---

# 2. Datos necesarios

El proyecto utilizará principalmente información histórica generada por la actividad diaria de Beauty Girl Studio.

## Información de clientes

Variables previstas:

- Identificador anonimizado
- Fecha de alta
- Programa de fidelización
- Número de visitas
- Historial de servicios
- Frecuencia de visitas
- Estado (cliente activa o inactiva)

---

## Información de citas

Variables previstas:

- Fecha
- Hora
- Día de la semana
- Servicio solicitado
- Profesional asignado
- Duración estimada
- Estado de la cita
- Cancelación
- Reprogramación
- Antelación de la reserva
- Canal de reserva

---

## Información económica

Variables previstas:

- Precio del servicio
- Descuentos aplicados
- Promociones utilizadas
- Venta de bisutería
- Importe total por visita

---

## Programa de fidelización

Variables previstas:

- Número de sellos
- Recompensas obtenidas
- Servicios bonificados
- Uso de promociones

---

## Redes sociales (Instagram)

Se estudiará la posibilidad de utilizar información pública de la cuenta oficial del negocio para enriquecer el análisis.

Variables potenciales:

- Fecha de publicación
- Tipo de publicación
- Servicio promocionado
- Número de "Me gusta"
- Número de comentarios
- Engagement
- Hashtags utilizados

---

## Selección de diseños de uñas

Uno de los servicios principales del negocio consiste en la realización de diseños personalizados de uñas.

Las clientas suelen seleccionar previamente fotografías de referencia para indicar el estilo deseado.

Aunque este proyecto no desarrollará modelos de visión por computador, estas imágenes podrán utilizarse para generar variables descriptivas mediante IA Generativa, tales como:

- Estilo del diseño
- Colores predominantes
- Nivel de complejidad
- Temporada
- Temática
- Tipo de decoración

Estas variables enriquecerán el análisis y permitirán estudiar tendencias de preferencias entre los clientes.

---

## Variables derivadas

Durante el proceso de preparación de datos podrán construirse nuevas variables como:

- Tiempo desde la última visita
- Frecuencia media de asistencia
- Probabilidad de abandono
- Cliente recurrente
- Ocupación por franja horaria
- Estacionalidad
- Customer Lifetime Value (CLV)
- Tasa de cancelación

---

## Granularidad

La granularidad principal del proyecto será **una observación por cita realizada**, ya que este nivel de detalle permite posteriormente agregar la información por cliente, servicio, profesional o periodo temporal según las necesidades del análisis.

---

## Profundidad histórica

Actualmente el negocio dispone de aproximadamente un año de histórico de información en la aplicación de reservas.

Idealmente se trabajará con la totalidad del histórico disponible, ya que permitirá detectar patrones temporales y entrenar modelos predictivos con suficiente representatividad.

---

## Volumen esperado

Se estima trabajar con varios miles de registros de citas, suficientes para desarrollar modelos descriptivos y predictivos adecuados para el proyecto.

En caso de que el volumen sea inferior al esperado, podrán incorporarse variables externas que complementen el análisis.

---

## Datos imprescindibles

Los datos mínimos necesarios serán:

- Historial de citas
- Cliente anonimizado
- Fecha
- Hora
- Servicio
- Estado de la cita
- Cancelaciones
- Precio del servicio

---

## Datos deseables

Como información complementaria sería interesante disponer de:

- Información meteorológica (de ser posible)
- Calendario de festivos
- Campañas comerciales realizadas
- Estadísticas de Instagram
- Ventas de bisutería
- Preferencias de diseños de uñas

---

# 3. Fuentes de datos previstas

La principal fuente de información será la aplicación de gestión de citas utilizada por Beauty Girl Studio.

Se analizará la posibilidad de exportar los datos históricos en formato CSV o Excel para su posterior tratamiento.

Las fuentes previstas son las siguientes:

| Fuente | Información | Formato |
|---------|-------------|---------|
| Aplicación de gestión de citas | Clientes, reservas, cancelaciones, servicios | CSV / Excel |
| Programa de fidelización | Historial de visitas y recompensas | CSV / Excel |
| Instagram del negocio | Información pública de publicaciones y engagement | Manual / API (si fuera posible) |
| Open-Meteo | Información meteorológica | API JSON |
| Calendario de festivos | Variables temporales | CSV / API |

La aplicación de reservas dispone de aproximadamente un año de histórico, lo que representa una base suficientemente sólida para el desarrollo del proyecto.

Las APIs de meteorología y calendarios son abiertas, gratuitas y cuentan con mantenimiento activo.

Instagram constituye una fuente complementaria que permitirá enriquecer el análisis mediante información pública sobre la interacción de las publicaciones.

### Riesgos detectados

Los principales riesgos identificados son:

- Limitaciones para exportar datos desde la aplicación de reservas
- Registros incompletos o inconsistentes
- Ausencia de determinadas variables
- Limitaciones de acceso a métricas avanzadas de Instagram
- Posibles cambios futuros en las APIs públicas

---

# 4. Consideraciones de privacidad y protección de datos

El proyecto utilizará datos reales pertenecientes a clientes del negocio, por lo que será imprescindible aplicar medidas de anonimización antes de iniciar cualquier análisis.

Se eliminarán todos los datos personales identificables, incluyendo nombres, teléfonos, direcciones de correo electrónico o cualquier otra información que permita identificar directamente a una persona.

Cada cliente será representado mediante un identificador anónimo.

Las fotografías utilizadas como referencia para los diseños de uñas no contendrán información personal de los clientes y únicamente se emplearán para extraer características generales relacionadas con los estilos de diseño.

El proyecto tendrá una finalidad exclusivamente académica y todos los resultados se presentarán de forma agregada, respetando en todo momento el Reglamento General de Protección de Datos (RGPD).

---

# 5. Viabilidad inicial del proyecto

La viabilidad del proyecto es alta debido a que existe acceso directo a una empresa real y colaboración con la propietaria del negocio, lo que facilita la obtención de datos históricos y permite validar los resultados obtenidos sobre un caso de uso real.

La disponibilidad de aproximadamente un año de histórico en la aplicación de reservas, junto con la información del programa de fidelización y la actividad desarrollada en Instagram, proporciona una base suficientemente amplia para desarrollar análisis descriptivos, modelos predictivos y técnicas de segmentación.

El componente de IA Generativa complementará el proyecto permitiendo transformar los resultados obtenidos por los modelos analíticos en recomendaciones y acciones comerciales directamente utilizables por el negocio.

El principal riesgo identificado es la calidad y completitud de los datos almacenados en la aplicación de gestión de citas. En caso de detectar limitaciones importantes, el proyecto podrá complementarse mediante datos externos (meteorología, festivos o eventos locales) y mediante la generación de nuevas variables derivadas durante el proceso de preparación de datos.

En conjunto, el proyecto presenta una elevada viabilidad técnica y metodológica, mantiene un claro enfoque de Ciencia de Datos y responde a una necesidad real de una pequeña empresa, permitiendo demostrar cómo la analítica avanzada y la Inteligencia Artificial pueden apoyar la toma de decisiones y generar valor de negocio.