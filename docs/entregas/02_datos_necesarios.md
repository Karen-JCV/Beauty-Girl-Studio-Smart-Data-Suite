# Entrega 2 - Selección de idea de proyecto y análisis de datos necesarios

**Máster en Data Science & AI**  
**Tarea:** Entrega 2 - Selección de idea de proyecto y análisis de datos necesarios
**Proyecto:** Beauty Girl Studio Smart Data Suite  
**Fecha de entrega:** 12 de Julio de 2026

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

# 1. Idea seleccionada

## Problema que resuelve

Beauty Girl Studio dispone de varios años de información histórica sobre citas, servicios y ventas. Sin embargo, estos datos no se utilizan para comprender el comportamiento de las clientas ni para anticipar su retorno. Esto provoca que decisiones sobre promociones, comunicación y fidelización se basen en intuición y no en evidencia. El negocio necesita identificar qué clientas están activas, cuáles están en riesgo de abandono y qué factores influyen en su retorno, para poder actuar de forma preventiva y estratégica.

## Solución planteada

El proyecto desarrollará un sistema analítico centrado en **medir la fidelización y predecir la probabilidad de retorno de las clientas**. Para ello se aplicará un análisis RFM (Recencia, Frecuencia y Valor Monetario) y un modelo predictivo basado en regresión logística que estime la probabilidad de que una clienta vuelva en un periodo determinado. Este enfoque permite transformar los datos operativos en conocimiento accionable para mejorar la retención y el valor del cliente.

## MVP del proyecto final

El MVP consistirá en un dashboard interactivo y un modelo predictivo funcional que incluya:

- Análisis RFM por clienta.
- Identificación de clientas activas, recurrentes, ocasionales y en riesgo.
- Modelo de probabilidad de retorno basado en regresión logística.
- Visualización de insights clave para la toma de decisiones.

El resto de funcionalidades (predicción de demanda, cancelaciones, segmentación avanzada, IA generativa) se incluirán como **mejoras futuras**, no como parte del MVP.

---

# 2. Datos necesarios

Para desarrollar el análisis de fidelización y el modelo de retorno se requieren datos históricos de citas, ventas y servicios.

## Variables necesarias

### Información de clientes
- Identificador anonimizado  
- Fecha de creación  
- Historial de visitas  
- Servicios contratados  
- Gasto total  
- Frecuencia de asistencia  
- Estado (activa / inactiva)

### Información de citas y reservas
- Fecha de realización  
- Fecha de creación  
- Servicio solicitado  
- Prestador  
- Estado de la cita (reservada, confirmada, cancelada)  
- Estado de pago  
- Origen de la reserva  
- Precio real  
- Fecha de pago (si aplica)

### Información de ventas e ítems
- ID de venta  
- Fecha de venta  
- Cliente  
- Servicio  
- Precio unitario  
- Total pagado  
- Descuentos  
- Prestador  
- Fecha de reserva asociada

### Información económica
- Monto total por visita  
- Promociones utilizadas  
- Método de pago  
- Comisiones (si aplica)

## Granularidad

La granularidad principal será **una observación por cita realizada**, ya que permite reconstruir el historial de cada clienta y calcular recencia, frecuencia y valor monetario.

## Profundidad histórica

Los datos disponibles incluyen registros desde 2022, aunque la calidad mejora significativamente a partir de abril–mayo de 2023.  
Se utilizará **todo el histórico disponible**, aplicando filtros de calidad cuando sea necesario.

## Volumen esperado

Se espera trabajar con varios miles de citas y ventas, suficiente para análisis RFM y modelos predictivos simples como regresión logística.

## Datos imprescindibles

- Historial de citas  
- Cliente anonimizado  
- Fecha de cita  
- Servicio  
- Precio  
- Estado de la cita  
- Ventas asociadas

## Datos deseables (no obligatorios)

- Programa de fidelización  
- Preferencias de diseño  
- Información meteorológica  
- Festivos  
- Engagement de Instagram

---

# 3. Fuentes de datos previstas

La información proviene directamente de la aplicación de gestión de citas y ventas utilizada por Beauty Girl Studio.

### Fuentes previstas

| Fuente | Información | Formato |
|--------|-------------|---------|
| Aplicación de reservas | Citas, clientes, servicios, estados | Excel |
| Módulo de ventas | Ventas, ítems, transacciones | Excel |
| Programa de fidelización | Sellos, recompensas | Excel |
| Redes sociales | Información pública de Instagram | Manual / API |
| Datos externos | Festivos, meteorología | API / CSV |

### Riesgos detectados

- Registros incompletos en años anteriores  
- Cambios en la estructura de exportación  
- Campos faltantes o inconsistentes  
- Limitaciones de acceso a métricas avanzadas de Instagram  
- Posibles duplicados o errores manuales en reservas

---

# 4. Consideraciones de privacidad y protección de datos

Los datos contienen información personal (nombre, email, teléfono).  
Antes del análisis se aplicará:

- Anonimización de clientes  
- Eliminación de datos sensibles  
- Uso exclusivo académico  
- Presentación de resultados agregados  
- Cumplimiento del RGPD

Las imágenes de diseños no contienen datos personales y solo se usarán para variables descriptivas si se incorporan en fases futuras.

---

# 5. Viabilidad inicial del proyecto

El proyecto es viable porque:

- Existe acceso directo a los datos reales del negocio.  
- Hay suficiente histórico para análisis RFM y modelos de retorno.  
- La calidad de los datos mejora a partir de 2023, lo que permite construir un dataset robusto.  
- El enfoque está acotado y es realista para el tiempo disponible.  

### Riesgos actuales

- Calidad variable en registros antiguos.  
- Posibles inconsistencias entre reservas, ventas e ítems.  
- Necesidad de limpieza y unificación de identificadores.

### Alternativas

Si alguna fuente presenta problemas, se puede:

- Limitar el análisis al periodo 2023–2026.  
- Complementar con datos externos (festivos, clima).  
- Ajustar el modelo a variables disponibles.

En conjunto, el proyecto es sólido, realista y alineado con una necesidad clara del negocio: **comprender y mejorar la fidelización de sus clientas**.