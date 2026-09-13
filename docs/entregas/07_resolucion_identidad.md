# Entrega 07 - Resolución de identidad y anonimización

**Máster en Data Science & AI**
**Proyecto:** Beauty Girl Studio Smart Data Suite
**Paso del roadmap:** 3 de 13
**Rige bajo:** `docs/architecture/contrato_analitico.md` (§10 — Trazabilidad y privacidad)
**Código:** `src/identity/resolve_identity.py`
**Entrada:** `docs/entregas/06_data_profiling.md`

---

## 0. Objetivo

Este paso resuelve el problema central de anonimización de los datos sensibles como: nombres, apellidos por ejemplo. Antes de construir `processed/`, el warehouse o la capa gold, se define y valida el procedimiento que convierte identidades con datos personales en un `id_cliente_anon` seguro, sin que ningún dato personal cruce esa frontera.

---

## 1. Decisión de diseño más importante: dos identificadores, no uno

El profiling de la Entrega 06 y el mockup de la Entrega 05 usan un identificador de 4 dígitos (`Clienta #8491`). Si ese código estético de 4 dígitos se usara también como clave real de unión en el warehouse, habría un problema estadístico:

> Con ~680 clientas y un espacio de solo 10.000 combinaciones de 4 dígitos, la probabilidad de que **al menos dos clientas distintas** terminen con el mismo código (colisión, por el problema del cumpleaños) es prácticamente del 100%.

**Por eso se usan dos identificadores con funciones distintas:**

| Identificador | Qué es | Dónde se usa | Garantía |
|---|---|---|---|
| `id_cliente_anon` | Hash largo (16 caracteres hexadecimales) | Clave real de unión en warehouse, gold y modelo | Colisión prácticamente imposible al volumen del negocio |
| `codigo_display` | Número de 4 dígitos (`#8491`) | Solo para mostrarlo en el dashboard, nunca para unir tablas | Se verifica que sea único dentro del dataset actual; si dos hashes generan el mismo número, se reasigna de forma determinista |

Esto no cambia nada de lo ya diseñado en `05_diseno_frontal.md` — el dashboard sigue mostrando `#8491` (por ejemplo) exactamente como en el mockup — pero evita que ese número corto se use por error como clave técnica.

---

## 2. Regla de "quién es una clienta real"

Confirmado en el profiling de la Entrega 06: `clientes.xlsx` mezcla clientas reales con contactos informales ("Amigo de Fátima", "Vecina 705", etc.). La regla adoptada:

> **Solo se considera clienta real quien aparece al menos una vez como comprador en `ventas.xlsx` o `items.xlsx`.**

`clientes.xlsx` se usa únicamente como fuente de **enriquecimiento** (teléfono, email, fecha de alta) para las clientas que ya están confirmadas como reales por haber comprado — nunca como el punto de partida.

---

## 3. Procedimiento de resolución (implementado en `resolve_identity.py`)

```
1. Construir el universo de "clientas reales":
   nombres normalizados únicos en ventas.Cliente ∪ items.Cliente

2. Para cada clienta real, buscar sus registros candidatos en clientes.xlsx
   (match por nombre normalizado)

3. Desambiguar dentro de cada grupo de nombre repetido:
   a. Si hay teléfono (señal más confiable: 96.4% de completitud),
      sub-agrupar por teléfono normalizado (solo dígitos)
   b. Si no hay teléfono pero sí email (75.1% de completitud),
      sub-agrupar por email normalizado
   c. Si no hay ninguna señal, se colapsa en una única identidad
      "residual" (no hay forma de distinguir personas sin ningún dato)
   d. Si el nombre normalizado tiene más de un registro en clientes.xlsx,
      la identidad resultante se marca identidad_ambigua = True para
      trazabilidad, tanto si converge en una sola persona como si se
      divide en varias

4. Generar id_cliente_anon = sha256(salt + nombre_norm + telefono + email)[:16]

5. Generar codigo_display = hash % 9000 + 1000, resolviendo colisiones
   de forma determinista dentro del dataset

6. Exportar dos tablas:
   - id_bridge_local.parquet   -> CONTIENE datos personales, NO se versiona
   - dim_cliente_anon.parquet  -> SIN datos personales, esta sí va al warehouse
```

### Normalización aplicada

- **Nombre:** minúsculas, sin acentos (`unicodedata.normalize("NFKD")`), espacios múltiples colapsados a uno, sin espacios en los extremos. Esto captura casos como `"Marve Matos"` vs `"Marve  Matos"` (doble espacio) detectados en el profiling.
- **Teléfono:** solo dígitos (se eliminan `+`, espacios, guiones).
- **Email:** minúsculas, sin espacios en los extremos.

---

## 4. Resultados de la validación (ejecutado contra los datos reales)

```
Clientas reales (compraron al menos una vez): 632
Identidades resueltas (dim_cliente_anon):      681
Identidades marcadas como ambiguas:            187
  -> convergieron en una sola identidad (mismo tel/email): 92
  -> se dividieron en 2+ identidades distintas: 95 (en 46 nombres)
Colisiones en id_cliente_anon: 0
Colisiones en codigo_display:  0
Clientas reales sin ningún registro en clientes.xlsx: 0
```

**Lectura de estos números:**

- El universo de clientas reales (632) es algo menor que el conteo de nombres distintos detectado en el profiling anterior (683), porque la normalización ahora también quita acentos, lo que fusiona variantes que antes se contaban como personas diferentes.
- De los 187 casos con más de un registro en `clientes.xlsx`, la mayoría (92, el 49%) se debían simplemente a que la misma persona tenía varias filas de contacto (por ejemplo, alta manual y alta online) — el algoritmo las fusiona correctamente en una sola identidad.
- El resto (95 identidades repartidas en 46 nombres, es decir, el 7.3% de los nombres) se mantiene deliberadamente **separado**, porque el teléfono o el email difieren de forma clara: son, con alta probabilidad, personas distintas que comparten nombre y apellido (frecuente con nombres comunes como "Ana González" o "Francys Peña"). Fusionarlas habría sido el error contrario: mezclar el historial de dos clientas distintas en un mismo `id_cliente_anon`, contaminando el RFM.
- No hubo ninguna colisión de `id_cliente_anon` ni de `codigo_display` al volumen actual del negocio, lo que confirma que el diseño de dos identificadores (§1) es correcto y no genera fricción en la práctica.
- Ninguna clienta que compró queda sin registro de origen en `clientes.xlsx`, consistente con el 100% de match por nombre ya detectado en el profiling.

---

## 5. Qué campos viajan a cada capa

| Campo | `id_bridge_local.parquet` (LOCAL, con PII) | `dim_cliente_anon.parquet` (warehouse/gold, sin PII) |
|---|---|---|
| `id_cliente_anon` | ✅ | ✅ |
| `codigo_display` | ✅ | ✅ |
| `nombre_norm`, `telefono_norm`, `email_norm` | ✅ | ❌ nunca |
| `fecha_creacion_declarada` | ✅ | ✅ (no es dato personal, es útil para `antiguedad_dias` como respaldo si falta la primera visita) |
| `identidad_ambigua` | ✅ | ✅ (bandera de calidad, sin PII) |

`id_bridge_local.parquet` es la única pieza del proyecto que contiene datos personales fuera de los Excel originales. Vive exclusivamente en el entorno local de procesamiento.

---

## 6. Medidas de protección obligatorias

1. **`id_bridge_local.parquet` nunca se versiona.** Añadido a `.gitignore`:
   ```
   data/local/id_bridge_local.parquet
   data/raw/*.xlsx
   ```
   (los `.xlsx` originales tampoco se subirán al repositorio público, por el mismo motivo — solo se versiona el código que los procesa).

2. **El `SALT` del script no quedará hardcodeado en el repositorio final.** En `resolve_identity.py` se leerá de una variable de entorno o de un archivo de configuración local no versionado, por ejemplo:
   ```python
   import os
   SALT = os.environ["ID_SALT"]
   ```
   Esto evita que alguien con acceso al código (pero no al salt) pueda intentar fuerza bruta sobre nombres conocidos para reidentificar a una clienta a partir de un `id_cliente_anon` filtrado.

3. **Ningún notebook de EDA, modelado o dashboard debe importar `id_bridge_local.parquet`.** Todo consumo posterior (warehouse, gold, modelo, frontal) parte únicamente de `dim_cliente_anon.parquet`.

4. **Casos con `identidad_ambigua = True` no se ocultan**, se documentan. En el EDA (paso 7 del roadmap) conviene reportar qué proporción del negocio corresponde a identidades ambiguas para dimensionar el riesgo de error residual (por ejemplo, si dos personas distintas quedaron fusionadas por error porque ninguna tenía teléfono ni email registrados).

---

## 7. Próximo paso

Con la identidad resuelta y validada, el siguiente paso del roadmap es **limpieza y normalización → capa `processed/`**, que:

- Consume `dim_cliente_anon.parquet` (nunca `clientes.xlsx` directamente) para cualquier referencia a cliente.
- Aplica la unión en dos pasos de `ventas`/`items`/`transacciones` documentada en `06_data_profiling.md` §3 (`ID interno` + fallback `Cliente + Fecha`).
- Descarta las columnas no usables identificadas en el profiling (§2 de ese documento).