# Entrega 09 - Construcción del warehouse (SQLite)

**Máster en Data Science & AI**
**Proyecto:** Beauty Girl Studio Smart Data Suite
**Paso del roadmap:** 5 de 13
**Rige bajo:** `docs/architecture/contrato_analitico.md`
**Código:** `src/warehouse/build_warehouse.py`
**Entradas:** `docs/entregas/07_resolucion_identidad.md`, `docs/entregas/08_limpieza_normalizacion.md`

---

## 0. Objetivo

Construir `beauty_studio.db` (SQLite) a partir de la capa `processed/` y de `dim_cliente_anon.parquet`, con claves primarias, claves foráneas activas y verificaciones de integridad — para que ningún dato inconsistente pueda llegar a la capa gold en silencio.

---

## 1. Esquema final

| Tabla | Tipo | Clave primaria | FK |
|---|---|---|---|
| `dim_cliente_anon` | Dimensión | `id_cliente_anon` | — |
| `dim_servicio` | Dimensión | `id_servicio` (id original del catálogo) | — |
| `fact_ventas` | Hecho | `id_venta` | `id_cliente_anon` → `dim_cliente_anon` |
| `fact_items` | Hecho | `id_item` (autoincremental) | `clave_venta` → `fact_ventas` |
| `fact_transacciones` | Hecho | `id_transaccion` (autoincremental) | `clave_venta` → `fact_ventas` (nullable) |
| `fact_reservas` | Hecho | `id_reserva` (autoincremental) | `id_cliente_anon` → `dim_cliente_anon` (nullable) |

### Decisiones de diseño y por qué

1. **`fact_items` no repite `id_cliente_anon`.** Antes de decidirlo, se verificó que `items_clean` y `ventas_clean` — que calculan la identidad de forma independiente — coinciden al **100%** para una misma `clave_venta` (0 filas inconsistentes de 6.556). Con esa garantía, la identidad del cliente vive solo en `fact_ventas` y `fact_items` se conecta por `clave_venta`. Evita que el dato pueda divergir por un futuro error de mantenimiento (una sola fuente de verdad).

2. **`fact_items` no tiene FK estricta hacia `dim_servicio`.** Se verificó que `items."Nombre item"` coincide con `servicios.Nombre` solo en el **94%** de los casos (incluye texto libre como "por Elsi" o variantes de promociones), mientras que `items.Categoría` coincide con `servicios."Categoría de servicio"` en el **100%**. `dim_servicio` queda como catálogo de referencia consultable por categoría (precio, duración), no como llave obligatoria fila a fila — forzar esa FK habría exigido descartar o adivinar el 6% restante sin necesidad real para el MVP (`categoria_servicio` es el campo que realmente pide `gold_cliente_snapshot`, no el ítem exacto).

3. **`fact_transacciones.clave_venta` es nullable.** El 30.7% de las transacciones no tiene `ID Venta` y no existe forma fiable de construir un fallback (ver `08_limpieza_normalizacion.md` §3.2). Se conservan esas filas con `clave_venta = NULL` en vez de descartarlas, para no perder información de ingresos/métodos de pago agregados.

4. **`PRAGMA foreign_keys = ON`** en toda la construcción: cualquier fila que intente referenciar una clave inexistente hace fallar la carga en vez de insertarse silenciosamente. Esto ya demostró su valor en la práctica (§2).

---

## 2. Un problema real que este paso mostró: colisión de `clave_venta`

Al cargar `fact_ventas` con la restricción `UNIQUE(clave_venta)`, la carga falló con `IntegrityError`. La causa: 2 pares de ventas (4 filas del total, 0.08%) comparten exactamente `Cliente + Fecha` en la clave de fallback.

**Investigación:** se confirmó contra `ventas.xlsx` que el sistema de origen registra la fecha con precisión de **minuto, sin segundos** (ej. `01/10/2023 09:35`) — no hay forma de distinguir dos ventas del mismo cliente en el mismo minuto con más detalle, porque el dato de origen simplemente no lo tiene.

**Decisión:** en ambos casos, mismo cliente + mismo minuto + `ID` de venta distinto se interpreta como **la misma visita, registrada en dos cobros** (no como un error de captura ni como dos visitas reales). Es coherente con la propia definición de `gold_visitas`: "una fila por visita realizada" (`03_modelo_datos.md` §4.1) — una visita, no un cobro. Se fusionan en una sola fila de `fact_ventas` sumando `monto_venta`/`monto_a_pagar`/`monto_pendiente` y se conservan ambos `ID` originales en `ids_venta_originales` (`n_ventas_fusionadas = 2`) para que la decisión sea auditable y reversible si en el futuro se determina lo contrario junto con la propietaria del negocio.

Esto obligó a corregir `clean_normalize.py` (paso 4): la agregación por `clave_venta` se aplica a **todas** las ventas (no solo a las que colisionan), de forma que el caso general (grupo de tamaño 1) no cambia y el caso de colisión se resuelve automáticamente.

**Resultado:** `ventas_clean.parquet` pasa de 5.292 a 5.290 filas. 0 colisiones restantes.

---

## 3. Verificación de integridad ejecutada contra los datos reales

```
dim_cliente_anon:   681 filas
dim_servicio:        54 filas
fact_ventas:       5.290 filas
fact_items:        6.556 filas
fact_transacciones: 6.020 filas
fact_reservas:    12.197 filas

Violaciones de integridad referencial (PRAGMA foreign_key_check): 0
```

### 3.1 Huérfanos esperados en `dim_cliente_anon`

```
Identidades en dim_cliente_anon sin ninguna venta asociada: 49
```

Esto **no es un error**: de las 681 identidades resueltas en la Entrega 07, solo 632 corresponden a nombres normalizados distintos (cada uno con exactamente una identidad canónica usada en `fact_ventas`, ver `08_limpieza_normalizacion.md` §2). Las 49 restantes son las identidades "alternativas" de los 46 nombres ambiguos que se colapsaron en una sola identidad canónica para el cruce transaccional — se conservan en `dim_cliente_anon` por trazabilidad, pero por diseño nunca aparecerán en `fact_ventas`. `681 − 632 = 49`, cuadra exactamente.

### 3.2 Cobertura de unión `fact_items` → `fact_ventas`

```
items sin venta asociada: 0
```

Confirma, ya a nivel de base de datos relacional (no solo en los parquet), que la unión en dos pasos (`ID interno`/`ID Venta` + fallback) funciona sin filas huérfanas.

### 3.3 Validación de la alerta de pago (profiling §6.2)

```
ventas con al menos una transacción vinculada: 70.6%
ventas con monto_pendiente = 0:                98.8%
```

Confirma empíricamente, con la base ya construida, la decisión tomada desde el profiling: usar `ventas.monto_pendiente == 0` como señal de "venta pagada" cubre casi 30 puntos porcentuales más que exigir una transacción vinculada. `transacciones` se mantiene como fuente complementaria (método de pago, propina), no como filtro obligatorio.

---

## 4. Verificación de privacidad (lección del paso 4 aplicada aquí)

En el paso 4 se detectó que `clave_venta` filtraba nombres de clientas en texto plano porque la revisión original solo miraba **nombres de columna**, no **contenido**. Aquí se aplica la verificación reforzada directamente sobre la base de datos construida: se recorren todas las columnas de tipo `TEXT` de las seis tablas y se comparan sus valores distintos contra los 632 nombres normalizados de clientas reales.

```
Hallazgos de PII en el warehouse: 0
```

---

## 5. Próximo paso

Con el warehouse construido y verificado, el siguiente paso del roadmap es la **construcción de la capa gold**: `gold_visitas` (una fila por visita, uniendo `fact_ventas` + `fact_items` filtrando por `monto_pendiente == 0`) y `gold_cliente_snapshot` (snapshots por cliente y fecha de referencia, con la variable objetivo `retorna_en_90_dias` respetando la regla de los 90 días completos del contrato analítico).