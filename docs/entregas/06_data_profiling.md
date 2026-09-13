# Entrega 06 - Data Profiling

**Máster en Data Science & AI**
**Proyecto:** Beauty Girl Studio Smart Data Suite
**Paso del roadmap:** 2 de 13 (ver `README.md` → Roadmap)
**Rige bajo:** `docs/architecture/contrato_analitico.md`

---

## 0. Objetivo de este documento

Antes de construir `processed/`, el warehouse y la capa gold, se audita el contenido real de las seis fuentes `raw/` (`clientes.xlsx`, `reservas.xlsx`, `ventas.xlsx`, `items.xlsx`, `servicios.xlsx`, `transacciones.xlsx`): volumen, completitud, rangos temporales, claves de unión reales y problemas de calidad. Este perfilado determina las decisiones de limpieza (`07_limpieza_normalizacion.md`, siguiente paso) y confirma o corrige los supuestos de `02_datos_necesarios.md` y `03_modelo_datos.md`.

**Método:** perfilado programático (`pandas`) sobre los seis ficheros originales, sin ninguna transformación previa.

---

## 1. Inventario general

| Fuente | Filas | Columnas | Rango temporal (campo fecha principal) |
|---|---|---|---|
| `clientes.xlsx` | 1.317 | 16 | Alta: 2022-04-03 → 2026-09-09 |
| `reservas.xlsx` | 12.309 | 26 | Realización: 2022-03-30 → 2026-08-31 |
| `ventas.xlsx` | 5.292 | 10 | 2023-02-19 → 2026-08-31 |
| `items.xlsx` | 6.559 | 13 | 2023-02-19 → 2026-08-31 |
| `servicios.xlsx` | 54 | 16 | — (catálogo estático) |
| `transacciones.xlsx` | 6.020 | 11 | 2023-02-19 → 2026-08-31 |

**Lectura inicial:** `reservas` arranca en marzo de 2022, pero `ventas`, `items` y `transacciones` (la base real del comportamiento de compra) solo tienen datos desde febrero de 2023. Esto confirma que el histórico útil y explotable con garantías empieza en **2023**, no en 2022. El periodo 2022 en `reservas` puede usarse como contexto cualitativo, pero no debe alimentar `gold_visitas` (que se construye desde `ventas`/`items`, no desde `reservas`, según `03_modelo_datos.md`).

Con ~3,5 años de histórico de ventas (feb-2023 a ago-2026) hay margen suficiente para varios cortes trimestrales de `fecha_referencia` con horizonte de 90 días ya completado (ver §5 del contrato analítico).

---

## 2. Completitud por fuente (% de nulos)

### 2.1 `clientes.xlsx`

| Campo | % nulos | Decisión anticipada |
|---|---|---|
| `Nombres` | 0.0 | Se usa para resolución de identidad |
| `Apellidos` | 0.2 | Se usa para resolución de identidad |
| `Email` | 24.9 | Señal secundaria de deduplicación |
| `Teléfono` | 3.6 | Señal secundaria de deduplicación |
| `Fecha de creación.` | 0.0 | Útil para `antiguedad_dias` como fallback |
| `Número de cliente` | 97.2 | **No usable** como clave |
| `RUT` | 99.6 | **No usable**, además dato sensible |
| `Teléfono secundario` | 100.0 | **Descartar columna completa** |
| `Dirección` / `comuna` / `Ciudad` | 99.8–99.9 | **Descartar**, no aporta y es dato sensible |
| `Edad` | 93.2 | **No usable** |
| `Día/Mes/Año de nacimiento` | ~92.3–92.4 | **No usable**; confirma la decisión ya tomada en E4 de no usar fecha de nacimiento |

**Conclusión:** de las 16 columnas, solo `Nombres`, `Apellidos`, `Email`, `Teléfono` y `Fecha de creación` tienen completitud suficiente para ser útiles. El resto se descarta por volumen de nulos, y varias de ellas (RUT, dirección, fecha de nacimiento) son además datos personales que el contrato analítico prohíbe llevar más allá de `raw/` (§4 y §10 de `contrato_analitico.md`).

### 2.2 `reservas.xlsx`

| Campo | % nulos | Nota |
|---|---|---|
| `N° de Cliente` | 99.4 | **No usable como clave de cliente** (contradice el supuesto de un identificador estable) |
| `RUT` | 99.9 | No usable |
| `Nº de sesión` / `Sesiones Totales` | 100.0 | Columnas vacías, descartar |
| `Comentario interno` | 99.7 | Descartar |
| `E-mail` | 20.5 | Señal secundaria |
| `Teléfono` | 1.0 | Buena señal secundaria |
| `Fecha pago` / `ID pago` | 23.9 | Coherente con el 23.9% de reservas con `Estado de pago = No pagada` |
| Resto de campos (`Nombre`, `Apellido`, `Servicio`, `Precio real`, `Estado`, `Prestador`, `Origen`...) | 0.0 | Completos |

**Hallazgo crítico:** el campo pensado en `02_datos_necesarios.md` como identificador de cliente en reservas (`N° de Cliente`) está vacío en el 99.4% de los casos. La identidad de la clienta en `reservas` solo puede reconstruirse por `Nombre` + `Apellido` (+ email/teléfono como desambiguador), igual que en `ventas`/`items`.

`Estado` (12.309 filas): `Asiste` 9.335 · `Cancelado` 1.670 · `Reservado` 740 · `Confirmado` 379 · `No Asiste` 167 · `Pendiente` 18.
`Estado de pago`: `Pago asociado` 7.563 · `No pagada` 2.885 · `Pagada en línea` 1.852 · `Pagada` 9.
`Origen`: `Manual` 9.525 · `Online` 2.784.

### 2.3 `ventas.xlsx`

| Campo | % nulos | Nota |
|---|---|---|
| `ID interno` | 29.4 | **Ver §3 — afecta la clave de unión con `items`/`transacciones`** |
| `Nota` | 100.0 | Descartar |
| `Creado por` | 53.1 | No crítico para el modelo |
| Resto (`ID`, `Fecha`, `Monto venta`, `Cliente`...) | 0.0 | Completos |

### 2.4 `items.xlsx`

| Campo | % nulos | Nota |
|---|---|---|
| `ID Venta` | 30.4 | Mismo patrón que `ventas.ID interno` — ver §3 |
| `Fecha reserva` | 4.1 | No crítico |
| `Prestador` | 0.7 | No crítico |
| Resto (`Cliente`, `Categoría`, `Total`...) | 0.0 | Completos |

`Tipo item`: 100% de las filas son `Servicio` (no hay ítems de bisutería/producto en esta exportación, a pesar de que el negocio también vende bisutería, indicado por la propietaria no es el fuerte del negocio — **ver alerta en §6**).

`Categoría` (top): `MANICURA RUSA` 4.094 · `PEDICURE` 1.326 · `MANICURE PERMANENTE` 378 · `CEJAS Y PESTAÑAS` 283 · `EXTENSIÓN DE UÑAS` 253 · `PROMOCIONES` 110 · `Otros` 88 · resto <20.

### 2.5 `servicios.xlsx`

Catálogo pequeño (54 filas) y de buena calidad. Únicos nulos relevantes: `Descripción` (22.2%) y `Capacidad de grupo` (22.2%, coherente con servicios no grupales). No requiere limpieza mayor.

### 2.6 `transacciones.xlsx`

| Campo | % nulos | Nota |
|---|---|---|
| `ID Venta` | 30.7 | Mismo patrón que en `items` — ver §3 |
| `Comprobante` | 82.9 | No crítico |
| `Cuotas` | 100.0 | Descartar |
| `Comisión` / `Fecha de transferencia` | 98.1 | Descartar, no aporta al MVP |
| Resto (`ID`, `Fecha`, `Monto`, `Método de Pago`) | 0.0 | Completos |

`Método de Pago`: `Tarjeta de Débito` 3.167 · `Transferencia Bancaria` 1.341 · `Online` 1.031 · `Efectivo` 308 · `Tarjeta de Crédito` 173.
`Estado de pago`: mayoritariamente `-` (5.908) y `Pagado` (112) — este campo no es fiable como filtro de "venta pagada"; **el estado de pago fiable a usar es el de `reservas.Estado de pago` combinado con `ventas.Monto pendiente` (§4.2)**.

---

## 3. Claves de unión reales (hallazgo técnico central de este perfilado)

El diseño original en `03_modelo_datos.md` asumía que `fact_ventas.id_venta` uniría directamente con `items`/`transacciones`. El perfilado muestra que la clave real es distinta:

| Unión asumida | Unión real verificada |
|---|---|
| `ventas.ID` ↔ `items.ID Venta` | ❌ 0% de coincidencia |
| `ventas."ID interno"` ↔ `items."ID Venta"` | ✅ **100% de coincidencia** quando ambos campos están presentes |
| `ventas."ID interno"` ↔ `transacciones."ID Venta"` | ✅ Mismo patrón que items |

**Ejemplo:** `ventas.ID = 1418239` (numérico interno de la plataforma) no aparece en `items`; en cambio `ventas."ID interno" = "#4436"` sí coincide exactamente con `items."ID Venta" = "#4436"`.

### 3.1 El problema del 29-31% de nulos en la clave de unión

`ventas."ID interno"` está vacío en 1.558 de 5.292 ventas (29.4%), y el mismo patrón aparece en `items."ID Venta"` (30.4%) y `transacciones."ID Venta"` (30.7%). Al perfilar por fecha, se confirma que **no es aleatorio**:

- Ventas/items/transacciones **sin** `ID interno`: concentradas entre **2023-02-23 y 2024-04-16**.
- Ventas/items/transacciones **con** `ID interno`: desde 2023-02-19 en adelante, cubriendo todo el resto del histórico.

Es decir, el sistema de origen empezó a generar el código `#interno` a partir de abril de 2024; antes de esa fecha, ese campo simplemente no existía.

**Solución de unión (fallback) para el periodo sin `ID interno`:** se verificó que la combinación `Cliente + Fecha` (con precisión de minuto) es prácticamente única dentro de las ventas sin `ID interno`: solo 4 de 1.558 filas (0.3%) comparten esa combinación. Por tanto, el pipeline de construcción del warehouse debe implementar una unión en dos pasos:

1. **Unión primaria:** `ventas."ID interno"` = `items."ID Venta"` = `transacciones."ID Venta"` (cubre ~70% de las filas, con match exacto).
2. **Unión de respaldo:** para las filas sin `ID interno` (típicamente ventas anteriores a abril de 2024), unir por `Cliente` (nombre normalizado) + `Fecha` a nivel de minuto. Las filas que ni siquiera con este fallback logren emparejarse (duplicados de la tabla anterior, <5 filas) se excluyen de `gold_visitas` y se documentan como pérdida controlada.

Este hallazgo es el que más cambia respecto al diseño de `03_modelo_datos.md` y debe incorporarse como nota en ese documento antes de escribir el pipeline de la capa gold.

---

## 4. Resolución de identidad de cliente

### 4.1 `clientes.xlsx` no es una lista limpia de clientas

Al perfilar los nombres, se detectan registros que no corresponden a clientas reales sino a contactos o referidos informales, por ejemplo: *"Amigo de Fátima"*, *"Vecina 705"*, *"Mamá Jenniffer Abarca"*, *"Tía María Eugenia Albarran"*, *"Hija de Abigail"*. Una búsqueda simple por patrones (`amig`, `vecin`, `mamá`, `hija`, `tía`...) ya detecta 25 registros de este tipo; es probable que existan más con otras variantes de redacción libre.

**Implicación:** `clientes.xlsx` no puede tratarse como maestro de identidad por sí solo. La regla de identidad de cliente debe basarse en quién **efectivamente compró** (aparece en `ventas`/`items`), no en quién está en la lista de contactos.

### 4.2 Cobertura de match nombre-normalizado

Se normalizó el nombre completo (minúsculas, espacios colapsados, sin acentos duplicados) y se comparó:

- **100% de los 683 clientes únicos que aparecen en `ventas.Cliente`** tienen coincidencia exacta por nombre normalizado en `clientes.xlsx`.
- `reservas` tiene 1.208 combinaciones únicas de `Nombre` + `Apellido` — más del doble que los clientes con venta real, lo que es coherente con que `reservas` incluye reservas canceladas, no-shows y contactos que nunca llegaron a comprar.

### 4.3 Duplicados de identidad dentro de `clientes.xlsx`

168 grupos de nombre normalizado duplicado, afectando a 377 filas (28.6% de la tabla). Ejemplos: "Mirna Molina" (5 registros), "Francys Peña" (5), "Yarleni Andrade" (4), "Estefania Molina" (4). Esto puede deberse a:

- La misma persona registrada varias veces (por ejemplo, distintas cuentas de reserva online vs. manual).
- Personas distintas que comparten nombre y apellido (más improbable dado el tamaño de la base, pero no descartable sin revisar teléfono/email).

**Regla de deduplicación propuesta para el paso de limpieza (§7 del roadmap):** agrupar candidatos a la misma persona por nombre normalizado, y dentro de cada grupo, confirmar identidad única si coinciden también teléfono o email; si no coinciden, tratar como personas distintas y dejarlo señalado para revisión manual si el volumen de casos ambiguos es bajo.

### 4.4 Regla de construcción de `id_cliente_anon`

En línea con `contrato_analitico.md` §10:

1. Se considera "clienta" solo a quien tiene al menos una fila en `ventas.xlsx`/`items.xlsx` (evita anonimizar y arrastrar contactos informales de `clientes.xlsx` que nunca compraron).
2. La clave de agrupación es el nombre normalizado, desambiguado por teléfono/email cuando haya duplicados (§4.3).
3. Se genera un hash irreversible (`id_cliente_anon`) a partir de esa clave, en una tabla puente que **no se versiona en el repositorio público** (vive solo en el entorno local de procesamiento).
4. Ningún campo personal (nombre, email, teléfono, RUT, dirección, fecha de nacimiento) pasa de `raw/` hacia `processed/`, el warehouse o `gold/`.

---

## 5. Consistencia entre fuentes

- Los rangos de fecha de `ventas`, `items` y `transacciones` coinciden exactamente (2023-02-19 → 2026-08-31), lo cual es esperable porque las tres provienen del mismo evento de venta.
- `reservas` cubre un rango más amplio (desde 2022-03) pero, como no puede unirse a `ventas` mediante un identificador estable (§2.2), su rol en la capa gold se limita a: (a) contexto para EDA de comportamiento de reservas/cancelaciones (fuera del MVP de predicción, ver contrato §9) y (b) enriquecer `gold_cliente_snapshot` con `prestador_habitual` si se logra vincular de forma razonable por nombre+fecha+servicio.
- Filas exactamente duplicadas: `clientes` 2, `reservas` 112, `items` 3, `ventas` 0, `transacciones` 0. Se eliminarán en el paso de limpieza.

---

## 6. Alertas para revisión con el negocio (Beauty Girl Studio)

1. **`items.Tipo item` es 100% "Servicio".** La descripción del proyecto menciona venta de bisutería como parte del negocio, pero no aparece ningún ítem de producto en esta exportación. Antes de dar por cerrado el alcance de datos, conviene confirmar con la propietaria si la bisutería se vende por otro canal/sistema no incluido en esta exportación, o reafirmar si simplemente no es un volumen relevante. No bloquea el MVP (que se centra en servicios de uñas/RFM), pero es una limitación a documentar en `02_datos_necesarios.md`.
2. **El campo `transacciones."Estado de pago"` no es fiable** como filtro de venta pagada (mayoritariamente vacío/"-"). Para `gold_visitas`, el estado de pago se determinará combinando `ventas."Monto pendiente" == 0` con la existencia de al menos una transacción asociada y no con este campo.
3. **`reservas.xlsx` no debe usarse como fuente de identidad de cliente** en ningún pipeline futuro; solo `ventas`/`items` tienen trazabilidad suficiente.

---

## 7. Decisiones que este profiling confirma o corrige respecto a entregas previas

| Documento previo | Supuesto original | Corrección tras profiling |
|---|---|---|
| `02_datos_necesarios.md` | Histórico disponible desde 2022 | Histórico de compra explotable real: **desde 2023-02** |
| `03_modelo_datos.md` §5.1 | Unión `ventas.id_venta` ↔ `items`/`transacciones` | Unión real es `ventas."ID interno"` ↔ `items/transacciones."ID Venta"`, con fallback por `Cliente + Fecha` para el 29-31% de filas anteriores a abril de 2024 |
| `03_modelo_datos.md` §5.1 | `reservas` como fuente de vínculo cliente-visita | Confirmado que `reservas."N° de Cliente"` es inutilizable (99.4% nulo); se mantiene el criterio ya adoptado de construir `gold_visitas` desde `ventas`/`items`, no desde `reservas` |
| `03_modelo_datos.md` §8 | Anonimización mediante `id_cliente_anon` | Confirmado y detallado el procedimiento de resolución de identidad (§4 de este documento) |

---

## 8. Próximo paso

Con este perfilado cerrado, el siguiente paso del roadmap es **§4 — Limpieza y normalización → capa `processed/`**, que implementará directamente las reglas descritas aquí: descarte de columnas no usables, normalización de nombres/fechas, deduplicación de `clientes` y la unión en dos pasos (`ID interno` + fallback `Cliente+Fecha`) para construir la base de `gold_visitas`.