# Entrega 5 - Diseño del frontal y experiencia de usuario  

**Máster en Data Science & AI**  
**Tarea:** Entrega 5 - Diseño del frontal y experiencia de usuario del producto
**Proyecto:** Beauty Girl Studio Smart Data Suite  
**Fecha de entrega:** 23 de Agosto de 2026
---

# 1. Resumen de la solución y del usuario

El proyecto aborda un problema crítico del negocio: **identificar qué clientas están en riesgo de no volver** y **predecir su probabilidad de retorno en los próximos 90 días**, permitiendo a Beauty Girl Studio tomar decisiones de fidelización basadas en datos.

## Usuario principal

La usuaria principal es **la propietaria del estudio**, quien gestiona citas, promociones y comunicación con las clientas. No es experta en analítica, por lo que necesita un frontal claro, simple y accionable.

## Necesidad del usuario

- Saber **qué clientas requieren atención inmediata**.  
- Priorizar acciones de fidelización (recordatorios, promociones, mensajes personalizados).  
- Comprender por qué una clienta está en riesgo.  

## Tipo de producto

El producto diseñado es un **dashboard predictor y explorador de clientas**, que integra:

- Un ranking de clientas en riesgo
- Segmentación RFM  
- Score de retorno  
- Confianza del modelo  
- Antigüedad del cliente  
- Historial de visitas  
- Factores del modelo  
- Gráfico de tendencia  
- Filtros avanzados  

## Resultado principal que obtiene el usuario es:

- **Probabilidad de retorno**  
- **Etiqueta de riesgo (Bajo / Medio / Alto)**  
- **Explicación del modelo**  
- **Acciones sugeridas**  

---

# 2. Imagen mockup del frontal

A continuación se integra el mockup principal del frontal.  
La imagen se encuentra en:

assets/05_mockup_frontal.png

Y se muestra embebida:

![Mockup del frontal](../assets/05_mockup_frontal.png)

---

# 3. Justificación del diseño

El diseño del frontal se justifica desde tres perspectivas: utilidad, flujo de usuario y experiencia de usuario.

---

## 3.1. Utilidad y valor de la solución

El frontal permite resolver la tarea más importante del negocio: **identificar clientas en riesgo y actuar a tiempo**.

### Valor aportado

- Reduce el riesgo de abandono.  
- Ahorra tiempo al evitar revisar manualmente el historial de cada clienta.  
- Facilita decisiones basadas en datos, no en intuición.  
- Permite priorizar acciones comerciales.  

### Información esencial mostrada

- Score de retorno  
- Confianza del modelo  
- Segmento RFM  
- Recency, Frequency, Monetary  
- Categoría favorita  
- Prestador habitual  
- Historial de visitas  
- Tendencia de retorno y riesgo  

### Información que se decidió no mostrar

- Datos personales (nombre, email, teléfono).  
- Información técnica del modelo.  
- Métricas avanzadas no necesarias para la propietaria.  

### Conversión del análisis en acción

El frontal incluye botones para:

- Exportar informe  
- Exportar caso  
- Descargar CSV  

Además, el panel de detalle sugiere acciones basadas en los factores del modelo.

---

## 3.2. Flujo de usuario

El flujo principal es simple y está diseñado para que la propietaria obtenga valor en menos de 30 segundos.

### 1. Punto de entrada

La usuaria accede al dashboard y ve:

- KPIs principales  
- Filtros avanzados  
- Ranking de clientas en riesgo  

### 2. Selecciones

Filtros disponibles:

- Rango de fechas  
- Segmento RFM  
- Nivel de riesgo  
- Categoría favorita  
- Prestador habitual  
- Antigüedad del cliente  
- Ticket promedio  
- Frecuencia  
- Mostrar solo clientas con historial completo  

### 3. Procesamiento

El sistema ejecuta:

- Cálculo de RFM  
- Consulta del snapshot del cliente  
- Predicción del modelo  
- Explicación del modelo  
- Actualización del gráfico inferior  

### 4. Resultado

La usuaria recibe:

- Score  
- Confianza  
- Riesgo  
- Historial  
- Factores del modelo  
- Tendencia de retorno  

### 5. Acción

La usuaria puede:

- Exportar informe  
- Exportar caso  
- Descargar CSV  
- Revisar historial  
- Priorizar clientas  

### 6. Excepciones

- Historial insuficiente → mensaje claro  
- Predicción incierta → etiqueta de baja confianza  
- Error → mensaje comprensible  

---

## 3.3. Experiencia de usuario

El diseño se basa en principios de claridad, simplicidad y confianza.

### Jerarquía visual

- KPIs arriba  
- Ranking al centro  
- Panel de detalle a la derecha  
- Gráfico inferior ocupando todo el ancho  

### Simplicidad

- Variables relevantes únicamente  
- Filtros organizados y visibles  
- Paneles colapsables  
- Se utilizan etiquetas claras: “Riesgo alto”, “Riesgo medio”, “Riesgo bajo”. 

### Legibilidad y consistencia

- Colores otoñales cálidos  
- Fucsia profundo para elementos clave (color insignia de la empresa)
- Dorado para acentos  
- Terracota claro para navegación  
- Iconos lineales minimalistas  

### Contexto y confianza

- Score + confianza del modelo  
- Factores del modelo  
- Tendencia temporal  

### Control del usuario

- Paneles colapsables  
- Filtros avanzados  
- Acciones manuales  

### Feedback del sistema

- Indicador de carga al recalcular.  
- Alertas claras si faltan datos.  
- Mensajes de confirmación al registrar acciones.    

---

# 4. Presentación de resultados y explicabilidad

El frontal evita mostrar solo una cifra. Cada predicción se acompaña de contexto y explicación.

## Resultado principal

- **Score de retorno**  
- **Confianza del modelo**  
- **Etiqueta de riesgo**  
- **Segmento RFM**  
  
## Información adicional

- Recency  
- Frequency  
- Monetary  
- Antigüedad del cliente
- Categoría favorita  
- Prestador habitual  
- Historial de visitas  
- Tendencia de retorno y riesgo  

## Evitar certezas

- Se muestra un indicador de confianza.  
- Se explica que la predicción es una estimación, no una garantía.  
- Se incluyen limitaciones del modelo.  

## Vista de detalle

La pantalla principal muestra solo lo esencial.  
La vista de detalle incluye:

- Variables completas  
- Gráficos de visitas  
- Factores del modelo  

---

# IA generativa como capa de explicación (opcional)

El MVP **no incluye IA generativa**, pero se plantea como mejora futura.

Si se incorpora, su función será:

- Resumir el estado de la clienta.  
- Explicar la predicción en lenguaje natural.  
- Sugerir acciones basadas en los datos.  

Nunca sustituirá al modelo ni inventará causas.

---

# 5. Alcance del MVP

El MVP incluirá:

- Dashboard funcional en Streamlit.  
- Filtros avanzados  
- KPIs principales  
- Ranking de clientas  
- Panel de detalle  
- Gráfico inferior  
- Exportación de informes

Elementos que serán solo mockup:

- Acciones automatizadas.  
- Panel de IA generativa.  
- Integración con WhatsApp o email.  

Tecnologías previstas:

- Python  
- Pandas  
- Scikit-learn  
- Streamlit  
- Plotly  

---


