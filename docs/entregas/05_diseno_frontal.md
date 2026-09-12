# Entrega 5 - Diseño del frontal y experiencia de usuario  

**Máster en Data Science & AI**  
**Tarea:** Entrega 5 - Diseño del frontal y experiencia de usuario del producto  
**Proyecto:** Beauty Girl Studio Smart Data Suite  
**Fecha de entrega:** 23 de Agosto de 2026  

---

# 1. Resumen de la solución y del usuario

El proyecto aborda un problema crítico del negocio: **identificar qué clientas están en riesgo de no volver** y **estimar su probabilidad de retorno en los próximos 90 días**, permitiendo a Beauty Girl Studio tomar decisiones de fidelización basadas en datos.

El frontal se diseña alineado con el contrato analítico definido en la Entrega 4:

- La salida principal del modelo es:  
  - `prob_retorno_90d` (probabilidad de retorno en 90 días).  
  - `prob_no_retorno_90d = 1 - prob_retorno_90d`.  
  - `score_riesgo = prob_no_retorno_90d * 100`.  
  - `prediccion` (retorna / no retorna).  
  - Factores del modelo (coeficientes o SHAP).  

Las probabilidades se mostrarán en el frontal **solo si el modelo está calibrado**.  
Los umbrales de riesgo (bajo / medio / alto) se consideran **provisionales** y se ajustarán tras la validación con datos reales.

## Usuario principal

La usuaria principal es **la propietaria del estudio**, quien gestiona citas, promociones y comunicación con las clientas. No es experta en analítica, por lo que necesita un frontal claro, simple y accionable.

## Necesidad del usuario

- Saber **qué clientas tienen mayor riesgo de no retorno**.  
- Priorizar acciones de fidelización (recordatorios, promociones, mensajes personalizados).  
- Comprender por qué una clienta aparece como de alto riesgo.  

## Tipo de producto

El producto diseñado es un **dashboard predictor y explorador de clientas**, que integra:

- Ranking de clientas ordenado por **riesgo de no retorno**.  
- Segmentación RFM.  
- Score de riesgo (0–100).  
- Probabilidad de retorno calibrada.  
- Antigüedad de la clienta.  
- Historial de visitas.  
- Factores del modelo (explicación).  
- Gráfico de tendencia de riesgo y retorno.  
- Filtros avanzados.

## Resultado principal que obtiene el usuario

- **Score de riesgo de no retorno** (0–100).  
- **Probabilidad de retorno calibrada**.  
- **Etiqueta de riesgo (Bajo / Medio / Alto)**.  
- **Explicación de los factores que influyen en el riesgo**.  
- **Base para decidir qué acciones comerciales ejecutar**.

---

# 2. Imagen mockup del frontal

La imagen se encuentra en:

`assets/05_mockup_frontal.png`

![Mockup del frontal](../assets/05_mockup_frontal.png)

El mockup refleja:

- Un ranking con **una fila por clienta anonimizada**, sin IDs repetidos.  
- Columnas coherentes con la salida del modelo: score de riesgo, probabilidad de retorno, días desde última visita, etiqueta de riesgo.  
- Un panel de detalle que muestra la información de una única clienta seleccionada.  

---

# 3. Justificación del diseño

El diseño del frontal se justifica desde tres perspectivas: utilidad, flujo de usuario y experiencia de usuario, estando explícitamente alineado con el contrato analítico del modelo.

---

## 3.1. Utilidad y valor de la solución

El frontal permite resolver la tarea más importante del negocio: **localizar clientas con alto riesgo de no retorno y actuar a tiempo**.

### Valor aportado

- Reduce el riesgo de abandono al identificar clientas prioritarias.  
- Ahorra tiempo al evitar revisar manualmente el historial de cada clienta.  
- Facilita decisiones basadas en datos, no solo en intuición.  
- Permite medir cuántas acciones comerciales útiles se generan a partir del ranking.

### Información esencial mostrada

- **Score de riesgo de no retorno (0–100)**.  
- **Probabilidad de retorno calibrada**.  
- **Etiqueta de riesgo (Bajo / Medio / Alto)**.  
- Segmento RFM.  
- Recency, Frequency, Monetary.  
- Antigüedad de la clienta.  
- Categoría favorita.  
- Prestador habitual.  
- Historial de visitas.  
- Tendencia de riesgo y retorno.  
- Factores del modelo (coeficientes o SHAP).

### Información que se decidió no mostrar

- Datos personales (nombre, email, teléfono).  
- Información técnica del modelo.   
- Métricas técnicas internas avanzadas (AUC, F1, etc.) que no son necesarias para la propietaria.

### Conversión del análisis en acción

El frontal incluye botones para:

- Exportar informe.  
- Exportar caso.  
- Descargar CSV.

El panel de detalle muestra los factores principales del modelo para que la propietaria pueda decidir qué acción comercial tiene más sentido.

---

## 3.2. Flujo de usuario

El flujo principal está diseñado para que la propietaria obtenga valor en menos de 30 segundos.

### 1. Punto de entrada

Al acceder al dashboard, la usuaria ve:

- KPIs principales del periodo (por ejemplo, % de clientas en alto riesgo, retorno esperado).   
- Filtros avanzados.  
- Ranking de clientas ordenado por **score de riesgo de no retorno** (de mayor a menor) por defecto.

### 2. Selecciones

Filtros disponibles:

- Rango de fechas de referencia.  
- Segmento RFM.  
- Nivel de riesgo (Bajo / Medio / Alto).  
- Categoría favorita.  
- Prestador habitual.  
- Antigüedad de la clienta.  
- Ticket promedio.  
- Frecuencia de visitas.  
- Opción para mostrar solo clientas con suficiente histórico.

### 3. Procesamiento

Cuando la usuaria ajusta filtros o selecciona una clienta:

- El sistema consulta el snapshot correspondiente en la capa gold.  
- Recupera `prob_retorno_90d` calibrada.  
- Calcula el **score de riesgo** = `(1 - prob_retorno_90d) * 100`.  
- Asigna la etiqueta de riesgo según umbrales provisionales (por ejemplo, Alto ≥ 70, Medio 40–69, Bajo < 40), que se ajustarán tras la validación.  
- Actualiza el panel de detalle y el gráfico inferior de tendencia.

### 4. Resultado

La usuaria recibe:

- Ranking ordenado por riesgo de no retorno.  
- Score, probabilidad, etiqueta de riesgo, días desde última visita.  
- Panel de detalle con RFM, antigüedad, categoría favorita, prestador habitual, historial de visitas y factores del modelo.  
- Gráfico inferior con tendencia de retorno y riesgo en los últimos 180 días.

### 5. Acción

La usuaria puede:

- Exportar informe general del periodo.  
- Exportar el caso de una clienta concreta para seguimiento.  
- Descargar CSV para análisis adicional.  
- Priorizar clientas de alto riesgo para campañas o recordatorios.  

### 6. Excepciones

- Historial insuficiente → mensaje claro.  
- Probabilidad no calibrada → aviso de interpretación cuidadosa.  
- Error técnico → mensaje comprensible y sin términos excesivamente técnicos.

### 7. Gestión de clientas excluidas del panel

El frontal incorpora un mecanismo para gestionar casos en los que una clienta **ya no debe aparecer en el ranking**, porque su situación no representa un riesgo comercial real.

En el panel de detalle se incluye el botón:

`[ Excluir del panel ]`

Al seleccionarlo, se despliega un menú con los siguientes motivos:

- Se mudó de ciudad
- No desea ser contactada
- Cliente inactiva por motivos personales
- Ya no pertenece al público objetivo
- Otro motivo

Al elegir una opción:

- La clienta se marca como **excluida del panel**.
- Se oculta del ranking, KPIs y filtros.
- No afecta su historial ni los datos del modelo.
- No modifica la capa gold ni la variable objetivo.
- Puede revertirse desde: **Configuración → Clientas excluidas**

Este mecanismo evita ruido en el análisis y mejora la interpretación del riesgo real.

---

## 3.3. Experiencia de usuario

El diseño se basa en claridad, simplicidad y confianza, con una estética cálida y profesional.

### Jerarquía visual

- KPIs arriba.  
- Ranking de clientas en el centro, con **una fila por clienta**.
- Panel de detalle a la derecha, mostrando la información de la clienta seleccionada. 
- Gráfico inferior ocupando todo el ancho.- Gráfico inferior ocupando todo el ancho para visualizar la tendencia de riesgo y retorno.
  
### Simplicidad

- Solo se muestran variables relevantes para la decisión de fidelización.  
- Filtros agrupados y claramente etiquetados.  
- Paneles laterales colapsables para disponer de pantalla completa cuando se necesite.  
- Etiquetas claras: “Riesgo alto”, “Riesgo medio”, “Riesgo bajo”.

### Legibilidad y consistencia

- Paleta de colores cálidos y otoñales:  
  - Fucsia profundo como color insignia de la marca para elementos clave.  
  - Dorado suave para acentos y resaltados.  
  - Rosa pálido y cremas para fondos.  
  - Terracota claro para la navegación lateral.  
- Tipografía legible y consistente.  
- Iconos lineales minimalistas para navegación y acciones.

### Contexto y confianza

- Score derivado de probabilidad calibrada.  
- Factores del modelo explicados en lenguaje de negocio.  
- Umbrales provisionales ajustables tras validación.

### Control del usuario

- Paneles colapsables.  
- Filtros avanzados.  
- Acciones manuales (exportar, revisar, priorizar).

### Feedback del sistema

- Indicador de carga al recalcular el ranking o los gráficos. 
- Alertas claras.  
- Mensajes de confirmación al exportar informes o casos.

### Gestión de exclusión de clientas

El panel de detalle incluye un botón visible y claro:

`[ Excluir del panel ]`

Al pulsarlo, aparece un menú desplegable con motivos de exclusión.

El diseño sigue los principios del frontal:

- Botón con color neutro (terracota claro).
- Menú desplegable con opciones claras y no técnicas.
- Mensaje de confirmación:
  - “La clienta ha sido excluida del panel. Puedes revertir esta acción desde Configuración → Clientas excluidas.”

Esta funcionalidad:

- Evita que clientas no recuperables aparezcan como “alto riesgo”.
- Mejora la confianza de la propietaria en el dashboard.
- Mantiene la coherencia del modelo sin alterar datos históricos.

---

# 4. Presentación de resultados y explicabilidad

## Resultado principal

- **Score de riesgo de no retorno (0–100)**.  
- **Probabilidad de retorno calibrada**.  
- **Etiqueta de riesgo (Bajo / Medio / Alto)**.  
- **Segmento RFM**.

## Información adicional

- Recency (días desde la última visita).  
- Frequency (número total de visitas).  
- Monetary (gasto acumulado).  
- Antigüedad de la clienta.  
- Categoría favorita.  
- Prestador habitual.  
- Historial de visitas.  
- Tendencia de retorno y riesgo en el tiempo.  
- Factores del modelo.

## Evitar certezas

- No se presenta una “confianza del modelo” que no esté definida analíticamente.  
- Se explica que la probabilidad depende de calibración.  
- Se aclara que los umbrales se ajustarán con datos reales.

## Vista de detalle

La pantalla principal muestra solo lo esencial para priorizar clientas.  
La vista de detalle incluye:

- Variables completas de la clienta seleccionada.  
- Gráfico de visitas y comportamiento temporal.   
- Factores del modelo.

## Exclusión de clientas del panel

El panel de detalle incorpora la opción:

`[ Excluir del panel ]` → **menú de motivos**

Esta acción:

- No borra datos históricos.
- No afecta la capa gold.
- No afecta el modelo entrenado.
- Solo modifica la visualización del dashboard.

Se utiliza para casos como:

- Mudanza
- Solicitud explícita de no contacto
- Inactividad prolongada por motivos personales
- Cambio de país
- No pertenecer al público objetivo

La exclusión evita interpretaciones erróneas del riesgo y mantiene la utilidad del ranking.

---

# IA generativa (fuera del MVP)

La IA generativa está **fuera del MVP**.  
Por ello:

- Se elimina del menú.  
- No se muestra como funcional en el frontal.  
- Se mantiene en mención solo como mejora futura.

---

# 5. Alcance del MVP

El MVP incluirá:

- Dashboard funcional en Streamlit.  
- Filtros avanzados.  
- KPIs principales del periodo.  
- Ranking de clientas por score de riesgo.  
- Panel de detalle por clienta.
- Gráfico inferior de tendencia de retorno y riesgo. 
- Exportación de informes y casos (CSV / EXCEL / PDF).
- Botón Excluir del panel (Manual, con menú desplegable. No incluye: Automatización de exclusión ni reglas automáticas basadas en comportamiento)

Elementos solo mockup:

- Acciones automatizadas (envío directo de campañas).    
- Integración con WhatsApp o email.

Tecnologías previstas:

- Python.  
- Pandas.  
- Scikit-learn.  
- Streamlit.  
- Plotly.  

---
