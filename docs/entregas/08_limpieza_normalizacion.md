# Entrega 08 - Limpieza y normalización

**Máster en Data Science & AI**
**Proyecto:** Beauty Girl Studio Smart Data Suite
**Paso del roadmap:** 4 de 13
**Rige bajo:** `docs/architecture/contrato_analitico.md`
**Código:** `src/cleaning/clean_normalize.py`
**Entradas:** `docs/entregas/06_data_profiling.md`, `docs/entregas/07_resolucion_identidad.md`

---

## 0. Objetivo

Construir la capa `processed/` aplicando, de forma reproducible y auditable, todas las decisiones de limpieza anticipadas en `03_modelo_datos.md` §8 y las reglas confirmadas en el profiling (`06_data_profiling.md`). Al salir de este paso, ningún archivo contiene datos personales: la identidad de cliente ya viaja exclusivamente como `id_cliente_anon`.

**Cambio de alcance respecto al diseño original:** `03_modelo_datos.md` preveía un `clientes_clean.parquet` en `processed/`. Se decide no generarlo: `dim_cliente_anon.parquet` (Entrega 07) ya cubre esa función sin exponer PII, y mantener un `clientes_clean.parquet` con nombre/email/teléfono en `processed/` sería inconsistente con la regla más estricta fijada en la Entrega 07 (§6): el único artefacto con datos personales fuera de los Excel originales es `id_bridge_local.parquet` y ese vive solo en el paso de identidad, no en `processed/`.

---

## 1. Qué se hizo con cada fuente

| Fuente | Filas raw → clean | Columnas descartadas | Anonimización |
|---|---|---|---|
| `reservas.xlsx` | 12.309 → 12.197 (112 duplicados exactos eliminados) | `N° de Cliente`, `RUT`, `E-mail`, `Teléfono`, `Nº de sesión`, `Sesiones Totales`, `Comentario interno`, `Notas compartidas con cliente` (texto legal genérico, sin valor analítico), `Responsable creación`/`Responsable última modificación` (email de la propietaria/staff), `Local` (constante) | `Nombre`+`Apellido` → `id_cliente_anon` |
| `ventas.xlsx` | 5.292 → 5.290 (0 duplicados exactos; 2 pares de ventas fusionados por colisión de minuto, ver §3.3bis) | `Nota` (100% nula), `Creado por`, `Local` (constante) | `Cliente` → `id_cliente_anon` |
| `items.xlsx` | 6.559 → 6.556 (3 duplicados exactos eliminados) | `Local` (constante) | `Cliente` → `id_cliente_anon` |
| `transacciones.xlsx` | 6.020 → 6.020 (0 duplicados) | `Comprobante`, `Cuotas` (100% nula), `Comisión`, `Fecha de transferencia`, `Estado de pago` (no fiable, ver §3) | No aplica (esta fuente no tiene columna de cliente) |
| `servicios.xlsx` | 54 → 54 | Ninguna | No aplica (catálogo, sin PII) |
| `clientes.xlsx` | — | — | **No se genera `clientes_clean.parquet`** (ver §0). Su función la cumple `dim_cliente_anon.parquet` |

---

## 2. Anonimización: de nombre a `id_cliente_anon`

`reservas`, `ventas` e `items` traían un nombre de cliente en texto libre. Cada uno se normaliza (mismo procedimiento que en `resolve_identity.py`: minúsculas, sin acentos, espacios colapsados) y se cruza contra el mapa `nombre_norm → id_cliente_anon` construido en la Entrega 07.

### Hallazgo que obliga a ajustar la Entrega 07: ventas/items no tienen teléfono ni email

`ventas.xlsx` e `items.xlsx` solo traen el nombre del cliente — no hay columna de teléfono ni email. Esto es un problema para los **46 nombres** que en la Entrega 07 se resolvieron como **2 o más personas distintas** (usando teléfono/email de `clientes.xlsx`): en `ventas`/`items` no existe esa señal, así que **no se puede saber a cuál de esas personas pertenece cada venta**.

**Decisión adoptada:** para el cruce con datos transaccionales, esos 46 nombres se colapsan en una única identidad canónica (la de mayor evidencia en `clientes.xlsx`: más registros de contacto coincidentes, y en empate, la de alta más antigua), marcada con la bandera `identidad_ambigua_transaccional = True`. Esta bandera es distinta de la `identidad_ambigua` general de la Entrega 07 (que incluye también casos ya resueltos con confianza) — aquí solo marca los casos donde **de verdad no se puede garantizar que todas las ventas pertenezcan a la misma persona**.

**Impacto medido:**

```
ventas afectadas por identidad_ambigua_transaccional: 9.6%  (509 / 5.292)
items afectados:                                       8.7%  (571 / 6.559)
```

**Consideración para el modelado (paso 9 del roadmap):** al construir `gold_cliente_snapshot`, se reportará el RFM también excluyendo estas clientas, para verificar que el modelo no depende de forma desproporcionada de identidades con menor confianza. No se excluyen por defecto — 9.6% es un volumen demasiado grande para descartarlo sin evaluar el impacto real.

### Cobertura de la anonimización

```
reservas: 12.0% de filas sin id_cliente_anon
ventas:    0.0% de filas sin id_cliente_anon
items:     0.0% de filas sin id_cliente_anon
```

El 12.0% de `reservas` sin `id_cliente_anon` es **esperado y correcto**: `reservas` incluye contactos que nunca llegaron a comprar (referidos, reservas canceladas antes de pagar, contactos informales) y el universo de `id_cliente_anon` se construyó únicamente a partir de quien compró (`ventas`/`items`), tal como se decidió en la Entrega 07 §2. Estas filas no se descartan de `reservas_clean.parquet` — se conservan con `id_cliente_anon = null` porque `reservas` puede seguir usándose como contexto cualitativo (no entra al MVP de predicción) y descartarlas aquí sería una pérdida de información sin necesidad.

---

## 3. Unión ventas ↔ items ↔ transacciones

### 3.1 `clave_venta` para ventas e items

Se implementa la unión en dos pasos ya documentada en el profiling:

1. **Primaria:** `ventas."ID interno"` = `items."ID Venta"` (match exacto, ~70% de las filas).
2. **Fallback:** para el resto (ventas anteriores a abril de 2024, sin `ID interno`), `clave_venta` se construye como `Cliente normalizado + Fecha (a nivel de minuto)`.

```
ventas con clave_venta por fallback: 29.4%
items con clave_venta por fallback:  30.4%
```

**Validación de la unión:** con esta lógica aplicada de forma idéntica en `ventas_clean` e `items_clean`, la cobertura de unión `items → ventas` por `clave_venta` es del **100%** — ninguna fila de `items` queda huérfana.

### 3.2 `transacciones` — vinculación más limitada y por qué

A diferencia de `ventas`/`items`, **`transacciones.xlsx` no tiene columna de cliente**. Esto significa que no se puede construir el mismo fallback (`Cliente + Fecha`) para el 30.7% de transacciones sin `ID Venta`: no hay nombre con el que emparejar.

**Decisión adoptada:** `transacciones_clean.parquet` solo vincula por `ID Venta` exacto. El 30.7% sin match queda con `clave_venta = null` y se conserva en el archivo (no se descarta), pero no participará en los joins de `gold_visitas`.

**Esto no bloquea el MVP** porque, según la alerta ya identificada en el profiling (§6.2 de `06_data_profiling.md`), el campo fiable para determinar si una venta está pagada no es `transacciones."Estado de pago"` (mayoritariamente vacío) sino `ventas."Monto pendiente" == 0`. `transacciones` se usa como fuente complementaria (por ejemplo, para reportar método de pago), no como filtro obligatorio de venta pagada.

---

## 3.3 Corrección de privacidad detectada durante la validación: `clave_venta` no debe llevar el nombre en texto plano

Durante la revisión del archivo generado se detectó que `clave_venta` para las filas de fallback (§3.1) se había construido como `"FB|{nombre_normalizado}|{fecha}"` — por ejemplo `"FB|nombre apellido|2023-02-23 05:36"`. **Normalizar un nombre (minúsculas, sin acentos) no lo anonimiza**: sigue siendo el nombre real y legible de una clienta y ese campo vivía en `ventas_clean.parquet` e `items_clean.parquet`, los archivos que se supone que ya no contienen PII.

**Causa raíz:** la verificación de privacidad original (§4 más abajo) solo inspeccionó los *nombres de columna* buscando patrones como `nombre`/`cliente`/`email`, no el *contenido* de las celdas. Una columna con nombre neutro (`clave_venta`) puede filtrar PII en sus valores sin que ese chequeo lo detecte.

**Corrección aplicada:** `clave_fallback()` ahora hashea la clave (`sha256(salt + "FB" + nombre_norm + fecha_minuto)`, igual que `id_cliente_anon`), en vez de concatenar el nombre en texto plano. La clave sigue siendo determinista (mismo nombre + misma fecha → mismo hash en `ventas` e `items`, preservando la unión), pero deja de ser legible.

**Verificación reforzada:** se repitió la validación de privacidad, esta vez comparando el *contenido* de cada columna de tipo texto contra la lista completa de nombres normalizados de `clientes.xlsx` (632 clientas reales), en los cinco archivos de salida. Resultado: ningún nombre aparece en ninguna celda de ningún archivo. La cobertura de unión `items → ventas` se re-verificó tras el cambio y se mantiene en 100%.

**Lección para el resto del pipeline:** En adelante, cualquier verificación de "sin PII" se revisará valores, no solo encabezados de columna — se deja como paso explícito en el checklist de la capa warehouse (paso 5).

---

## 4. Reporte de ejecución (validado contra los datos reales)

```
reservas:        12.309 -> 12.197 filas   (12.0% sin id_cliente_anon, esperado)
ventas:           5.292 ->  5.290 filas   (0.0% sin id_cliente_anon; 29.4% clave por fallback; 9.6% identidad_ambigua_transaccional; 2 pares fusionados por colisión de minuto, ver §3.3bis)
items:             6.559 ->  6.556 filas   (0.0% sin id_cliente_anon; 30.4% clave por fallback)
transacciones:    6.020 ->  6.020 filas   (30.7% sin clave_venta, documentado y aceptado)
servicios:           54 ->     54 filas
```

**Verificación de privacidad (por contenido, no solo por nombre de columna — ver §3.3):** se comparó el valor de cada celda de texto de los cinco archivos de salida contra los 632 nombres normalizados de clientas reales. Ninguna celda de ningún archivo contiene un nombre de clienta. El único campo `"Nombre"` que aparece es en `servicios_clean.parquet` y corresponde al nombre del servicio del catálogo (ej. *"Esmaltado permanente de Pies"*), no a una persona.

---

## 5. Próximo paso

Con `processed/` construido, el siguiente paso del roadmap es la **construcción del warehouse (SQLite)**: crear `dim_cliente_anon`, `dim_servicio`, `fact_reservas`, `fact_ventas`, `fact_items`, `fact_transacciones` a partir de estos parquet, estableciendo las claves primarias/foráneas ya definidas en `03_modelo_datos.md` §5 y usando `clave_venta` como clave real de unión entre `fact_ventas`, `fact_items` y `fact_transacciones` (no `ID` ni `ID Venta` crudos).