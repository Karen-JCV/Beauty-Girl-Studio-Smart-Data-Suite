# Entrega 12 - Feature engineering

**Máster en Data Science & AI**
**Proyecto:** Beauty Girl Studio Smart Data Suite
**Paso del roadmap:** 8 de 13
**Rige bajo:** `docs/architecture/contrato_analitico.md`
**Código:** `src/features/build_features.py`
**Entrada:** `docs/entregas/11_eda.md`

---

## 0. Objetivo

Dejar `gold_cliente_snapshot` con la columna `split` (train/val/test) que su propio esquema exige y producir una matriz de variables ya codificada (`model_input.parquet`) lista para entrenar en el paso 9 sin transformaciones adicionales — aplicando el split temporal con margen de 90 días que el EDA confirmó como imprescindible, no opcional.

---

## 1. Un problema de calidad detectado al construir las dummies

Al generar las variables dummy de `categoria_favorita` apareció `"PROMOCIONES "` (con espacio final) como categoría — no duplicaba ninguna versión sin espacio (es el único valor así en los datos), pero es exactamente el tipo de fallo silencioso que más adelante sí puede fragmentar una categoría real si aparece una variante "limpia". Se corrigió en el origen: `clean_normalize.py` (paso 4) ahora aplica `.strip()` a `Categoría`, `Nombre item`, `Tipo item` y `Prestador` de `items.xlsx`, no solo al campo que causó el hallazgo. Se repropagó el cambio por limpieza → warehouse → gold → features; todos los conteos de los pasos anteriores se mantuvieron idénticos, confirmando que la corrección no tuvo efectos colaterales.

---

## 2. Split temporal train / val / test

### 2.1 Cortes excluidos antes de repartir

- **`2023-03-31`** (n = 3): ruido estadístico ya identificado en el EDA (`11_eda.md` §1), no una fecha de referencia representativa.
- **Snapshots con `horizonte_completo = False`** (1.242 filas): no tienen `retorna_en_90_dias` observable — quedan con `split = None`, disponibles para scoring en producción (el dashboard los usará), pero nunca para entrenar/validar/testear.

### 2.2 Asignación de cortes

| Split | Cortes | n | % retorno |
|---|---|---|---|
| **train** | 2023-06-30 → 2025-03-31 (8 cortes) | 2.906 | 39.3% |
| **val** | 2025-06-30, 2025-09-30 | 1.088 | 24.2% |
| **test** | 2025-12-31, 2026-03-31 | 1.195 | 21.6% |

**El % de retorno cae de train a test (39.3% → 21.6%) por diseño, no por error.** Es la deriva temporal documentada en el EDA (`11_eda.md` §1): la tasa base de retorno del negocio ha ido bajando con el tiempo y un split temporal correcto tiene que reflejar eso — si val/test tuvieran la misma tasa que train, sería señal de que el split no está realmente separado en el tiempo. Esto es exactamente lo que hace que la calibración del modelo (paso 9) tenga que revisarse por separado en cada split y no solo de forma agregada.

### 2.3 Verificación programática del margen de 90 días

El script no solo respeta el margen al elegir los cortes — lo **verifica en tiempo de ejecución** y falla si algún cambio futuro en `CORTES_TRAIN`/`CORTES_VAL`/`CORTES_TEST` lo rompe, en vez de generar un split contaminado en silencio:

```
Margen train -> val: 91 días
Margen val -> test:  92 días
```

Ambos por encima del mínimo de 90 días exigido por el contrato analítico §5.

---

## 3. Variables incluidas y codificación

Solo las variables permitidas por el contrato analítico §4:

| Variable | Tratamiento |
|---|---|
| `recency_dias`, `frequency_visitas`, `monetary_total`, `ticket_medio`, `antiguedad_dias` | Numéricas, sin transformar (los modelos de árbol no lo necesitan; si el paso 9 prueba regresión logística con regularización fuerte, se evaluará escalado ahí, no aquí) |
| `usa_promociones` | Booleana → 0/1 |
| `categoria_favorita` | One-hot (9 columnas) |
| `segmento_rfm` | One-hot (5 columnas, incluye `Sin_segmentar`) |
| `retorna_en_90_dias` | Variable objetivo → 0/1 (con `NA` explícito donde no hay horizonte completo, nunca 0 por defecto) |

**No entran** (aunque existan en `gold_cliente_snapshot` para análisis o dashboard): `prestador_habitual`, `origen_reserva`, `identidad_ambigua_transaccional` como feature del modelo (se mantiene solo para trazabilidad/QA, no como variable predictiva).

**Recordatorio para el paso 9** (hallazgo del EDA, `11_eda.md` §5): `frequency_visitas` y `monetary_total` tienen correlación 0.96. `model_input.parquet` conserva ambas — la decisión de probar la regresión logística con y sin una de las dos se toma en el momento de entrenar, no aquí.

---

## 4. Validación ejecutada

```
model_input.parquet: 6.434 filas, 25 columnas
Nulos en 'split':                1.245  (= 1.242 sin horizonte completo + 3 del corte excluido)
Nulos en 'retorna_en_90_dias':   1.242  (exactamente las filas sin horizonte completo -- nunca se rellenó con 0)
```

Se confirmó que `gold_cliente_snapshot.parquet` (actualizado in place) y `model_input.parquet` reportan el mismo conteo de `split` por categoría — no hay divergencia entre la tabla gold y la matriz derivada.

---

## 5. Próximo paso

Con `model_input.parquet` listo, el siguiente paso del roadmap es el **modelado** (paso 9): baseline trivial, baseline RFM (`recency_dias <= 45` y `frequency_visitas >= 1`), regresión logística y Random Forest, evaluados sobre la clase "no retorna" y comparando calibración entre val y test dada la deriva temporal ya documentada.