# Entrega 10 - Construcción de la capa gold

**Máster en Data Science & AI**
**Proyecto:** Beauty Girl Studio Smart Data Suite
**Paso del roadmap:** 6 de 13
**Rige bajo:** `docs/architecture/contrato_analitico.md`
**Código:** `src/gold/build_gold.py`
**Entrada:** `docs/entregas/09_warehouse.md`

---

## 0. Objetivo

Construir `gold_visitas.parquet` y `gold_cliente_snapshot.parquet` a partir del warehouse, aplicando sin excepciones las reglas temporales del contrato analítico: cada snapshot solo puede usar información disponible hasta su `fecha_referencia` y la variable objetivo solo se etiqueta cuando el horizonte de 90 días ya se completó.

---

## 1. `gold_visitas`

Una fila por **visita pagada** (`fact_ventas.monto_pendiente = 0`), no por venta ni por ítem. Cuando una visita incluyó más de un servicio, se toma como "servicio principal" el ítem de mayor importe dentro de esa venta y se guarda `n_items` para no perder la señal de que hubo más de uno.

**Cambio respecto al diseño original de `03_modelo_datos.md`:** no se incluyen `origen_reserva` ni `estado_pago` a nivel de reserva. No existe una unión fiable venta↔reserva (confirmado en el profiling, `06_data_profiling.md` §2.2 y §5: `reservas."N° de Cliente"` es 99.4% nulo) y el estado de pago de la visita ya queda resuelto en el filtro `monto_pendiente = 0` aplicado en etapas previas del pipeline. Mantener esos campos habría exigido inventar una unión que los datos no sostienen.

```
gold_visitas: 5.229 filas, 623 clientas únicas
nulos en 'prestador': 11 (0.2%, coherente con el 0.7% de nulos ya detectado en items.Prestador)
```

**Nota:** 623 clientas con visita pagada, no 632 (el total de clientas reales de la Entrega 07). 9 clientas tienen únicamente ventas con saldo pendiente y por tanto ninguna visita "pagada" que entre en `gold_visitas`. No es un error — es coherente con la definición de visita del contrato.

---

## 2. `gold_cliente_snapshot`

Una fila por `(id_cliente_anon, fecha_referencia)`. Se generan **15 cortes**: uno por cada fin de trimestre dentro del rango de datos (2023-03-31 a 2026-06-30) más un corte final en la última fecha disponible (2026-08-31), que sirve como snapshot "actual" para producción/dashboard.

### 2.1 Variables calculadas (todas con datos ≤ `fecha_referencia`)

| Variable | Cómo se calcula |
|---|---|
| `recency_dias` | `fecha_referencia − última visita ≤ fecha_referencia` |
| `frequency_visitas` | conteo de visitas `≤ fecha_referencia` |
| `monetary_total` | suma de `importe_total` de esas visitas |
| `ticket_medio` | `monetary_total / frequency_visitas` |
| `antiguedad_dias` | `fecha_referencia − primera visita` |
| `categoria_favorita` | categoría más frecuente entre esas visitas |
| `usa_promociones` | si alguna visita tuvo `categoria_servicio = "PROMOCIONES"` |
| `segmento_rfm` | ver §2.2 |
| `retorna_en_90_dias` | ver §2.3 |

### 2.2 `segmento_rfm`: heurístico transversal, no histórico

Se calcula por **cuartiles dentro de cada `fecha_referencia`**: cada clienta se compara contra sus pares que estaban activas en ese mismo corte, no contra el histórico completo del negocio. Es la forma metodológicamente correcta de hacer RFM (una clienta "Top" en 2023 con un negocio pequeño no es comparable a una "Top" en 2026 con más volumen). Etiquetas resultantes: `Campeonas`, `Leales`, `En_riesgo`, `Inactivas` (más `Sin_segmentar` en los 3 cortes más antiguos, cuando aún había menos de 4 clientas activas para formar cuartiles).

**Se documenta como heurístico de partida**, no como definitivo: los puntos de corte (cuartiles → 4 categorías) se revisarán en el EDA (paso 7) contra el comportamiento real observado.

### 2.3 `retorna_en_90_dias`: la regla que más importa del contrato

```python
horizonte_completo = (fecha_referencia + 90 días) <= fecha_max_datos_disponibles
```

- Si `horizonte_completo = True`: se etiqueta observando si hay alguna visita estrictamente posterior a `fecha_referencia` y dentro de los 90 días siguientes.
- Si `horizonte_completo = False`: `retorna_en_90_dias = NULL`. **No se etiqueta como 0.**

```
Filas con horizonte completo (válidas para entrenar/validar/testear): 5.192
Filas sin horizonte completo (solo para scoring en producción):        1.242
% de retorno positivo entre las etiquetables:                          32.1%
```

**Por qué se conservan también las filas sin horizonte completo:** son exactamente las que necesita el dashboard para mostrar el riesgo de las clientas *ahora*, incluida la última clienta que compró la semana pasada. La misma tabla `gold_cliente_snapshot` sirve para dos propósitos —entrenar el modelo (filtrando `horizonte_completo = True`) y alimentar el scoring en vivo (usando el corte más reciente, `horizonte_completo = False`)— sin duplicar lógica ni tablas.

---

## 3. Validaciones ejecutadas contra los datos reales

### 3.1 Consistencia interna (sin fuga de información)

Se tomó una muestra de 50 snapshots y se recalculó manualmente `frequency_visitas` y `monetary_total` filtrando `gold_visitas` por `fecha_visita <= fecha_referencia`, comparando contra lo que produjo el pipeline:

```
Errores de consistencia: 0 / 50
```

Se repitió el mismo ejercicio para `retorna_en_90_dias` sobre 30 snapshots con horizonte completo, verificando manualmente que solo se usaron visitas **estrictamente posteriores** a `fecha_referencia` y dentro de los 90 días siguientes:

```
Errores en variable objetivo: 0 / 30
```

### 3.2 Integridad estructural

```
Filas duplicadas en (id_cliente_anon, fecha_referencia): 0
recency_dias negativo:                                   0
antiguedad_dias negativo:                                 0
antiguedad_dias < recency_dias (imposible por definición): 0
```

### 3.3 Corrección aplicada durante la validación

La primera versión de `fecha_referencia` heredaba la hora exacta de la primera venta del dataset (`19:06:00` en vez de medianoche), porque `pd.date_range(..., freq="QE")` conserva la hora del punto de partida si no se normaliza. Se corrigió añadiendo `normalize=True`: `fecha_referencia` es conceptualmente un día de corte, no un instante arbitrario y dejarlo así habría sido confuso para cualquiera que consultara la tabla más adelante (incluida la propietaria, si algún reporte llega a mostrar esa fecha).

---

## 4. Próximo paso

Con la capa gold construida y validada, el siguiente paso del roadmap es el **EDA orientado a riesgo de no retorno** (paso 7): analizar la distribución de RFM, comparar clientas que retornan vs. no retornan, revisar el balance de clases de `retorna_en_90_dias` (32.1% de positivos — no está muy desbalanceado, pero se documentará su evolución por corte) y decidir si el heurístico de `segmento_rfm` (§2.2) necesita ajuste antes de pasar al modelado.