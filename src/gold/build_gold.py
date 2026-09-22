"""
build_gold.py
==============

Paso 6 del roadmap: construcción de la capa gold.

Consume:
  - data/warehouse/beauty_studio.db (fact_ventas, fact_items)

Produce:
  - data/gold/gold_visitas.parquet
  - data/gold/gold_cliente_snapshot.parquet

Reglas aplicadas (ver docs/architecture/contrato_analitico.md):

  - gold_visitas: una fila por VISITA (venta pagada, monto_pendiente = 0),
    no por venta ni por ítem. El servicio/categoría/prestador de la visita
    es el del ítem de mayor importe dentro de esa venta (servicio
    "principal"); se guarda también n_items para no perder la información
    de si hubo más de un servicio en la misma visita.

  - gold_cliente_snapshot: una fila por (id_cliente_anon, fecha_referencia).
    Todas las variables se calculan usando SOLO visitas con
    fecha_visita <= fecha_referencia (sin fuga de información).

  - retorna_en_90_dias es NULL cuando fecha_referencia + horizonte_dias
    aún no ha ocurrido en los datos disponibles (no se etiqueta como 0
    solo porque "todavía no volvió"). La columna `horizonte_completo`
    marca explícitamente qué filas son válidas para entrenar/validar/
    testear y cuáles son solo para scoring en producción (snapshot más
    reciente, usado por el dashboard).

  - segmento_rfm se calcula de forma transversal: dentro de cada
    fecha_referencia, se compara a cada cliente contra el resto de
    clientes activos en ese mismo corte (cuartiles de R/F/M), no contra
    el histórico completo del negocio. Es un heurístico de partida para
    el MVP; se puede refinar en el EDA (paso 7).

  - origen_reserva y estado_pago (a nivel de reserva) NO se incluyen en
    gold_visitas: no existe una unión fiable venta<->reserva (ver
    docs/entregas/06_data_profiling.md §2.2 y §5) y el estado de pago ya
    se resuelve en el filtro monto_pendiente = 0 de fact_ventas.
"""

import argparse
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# gold_visitas
# ---------------------------------------------------------------------------

def construir_gold_visitas(conn: sqlite3.Connection) -> pd.DataFrame:
    ventas = pd.read_sql(
        """
        SELECT id_venta, clave_venta, id_cliente_anon, identidad_ambigua_transaccional,
               fecha AS fecha_visita, monto_venta AS importe_total
        FROM fact_ventas
        WHERE monto_pendiente = 0
        """,
        conn,
    )
    items = pd.read_sql(
        "SELECT clave_venta, categoria, prestador, total FROM fact_items", conn
    )

    # servicio "principal" de la visita = el ítem de mayor importe dentro
    # de esa venta. n_items se guarda aparte para no perder la señal de
    # visitas con varios servicios.
    items_ordenados = items.sort_values("total", ascending=False)
    principal = items_ordenados.groupby("clave_venta", as_index=False).first()
    n_items = items.groupby("clave_venta", as_index=False).size().rename(columns={"size": "n_items"})

    gold_visitas = (
        ventas.merge(principal, on="clave_venta", how="left")
        .merge(n_items, on="clave_venta", how="left")
        .rename(columns={"categoria": "categoria_servicio"})
    )

    gold_visitas["fecha_visita"] = pd.to_datetime(gold_visitas["fecha_visita"])
    gold_visitas["id_visita"] = gold_visitas["id_venta"]

    columnas_finales = [
        "id_visita",
        "id_cliente_anon",
        "identidad_ambigua_transaccional",
        "fecha_visita",
        "importe_total",
        "categoria_servicio",
        "prestador",
        "n_items",
    ]
    return gold_visitas[columnas_finales].sort_values(["id_cliente_anon", "fecha_visita"])


# ---------------------------------------------------------------------------
# gold_cliente_snapshot
# ---------------------------------------------------------------------------

def generar_fechas_referencia(fecha_min: pd.Timestamp, fecha_max: pd.Timestamp) -> list[pd.Timestamp]:
    """Cortes trimestrales dentro del rango de datos, más un corte final
    en la última fecha disponible (snapshot 'actual' para producción).
    Se normalizan a medianoche: fecha_referencia es un día de corte, no
    un instante con la hora arbitraria de la primera venta del dataset."""
    cortes = pd.date_range(start=fecha_min, end=fecha_max, freq="QE", normalize=True).tolist()
    fecha_max_norm = fecha_max.normalize()
    if fecha_max_norm not in cortes:
        cortes.append(fecha_max_norm)
    return sorted(set(cortes))


def _segmento_rfm(grupo: pd.DataFrame) -> pd.Series:
    """RFM transversal: cuartiles calculados DENTRO de cada fecha_referencia
    (cada cliente se compara contra sus pares activos en ese mismo corte)."""
    n = len(grupo)
    if n < 4:
        # Muy pocos clientes activos en este corte para cuartiles con sentido
        return pd.Series(["Sin_segmentar"] * n, index=grupo.index)

    r_score = pd.qcut(grupo["recency_dias"].rank(method="first"), 4, labels=[4, 3, 2, 1]).astype(int)
    f_score = pd.qcut(grupo["frequency_visitas"].rank(method="first"), 4, labels=[1, 2, 3, 4]).astype(int)
    m_score = pd.qcut(grupo["monetary_total"].rank(method="first"), 4, labels=[1, 2, 3, 4]).astype(int)
    total = r_score + f_score + m_score

    etiquetas = pd.cut(
        total,
        bins=[2, 4, 7, 10, 12],
        labels=["Inactivas", "En_riesgo", "Leales", "Campeonas"],
    )
    return etiquetas.astype(str)


def construir_gold_cliente_snapshot(
    gold_visitas: pd.DataFrame, horizonte_dias: int = 90
) -> pd.DataFrame:
    fecha_min = gold_visitas["fecha_visita"].min()
    fecha_max = gold_visitas["fecha_visita"].max()
    fechas_referencia = generar_fechas_referencia(fecha_min, fecha_max)

    filas = []
    for fecha_ref in fechas_referencia:
        hasta_corte = gold_visitas[gold_visitas["fecha_visita"] <= fecha_ref]
        if hasta_corte.empty:
            continue

        agg = hasta_corte.groupby("id_cliente_anon").agg(
            ultima_visita=("fecha_visita", "max"),
            primera_visita=("fecha_visita", "min"),
            frequency_visitas=("id_visita", "count"),
            monetary_total=("importe_total", "sum"),
            identidad_ambigua_transaccional=("identidad_ambigua_transaccional", "max"),
        ).reset_index()

        agg["fecha_referencia"] = fecha_ref
        agg["recency_dias"] = (fecha_ref - agg["ultima_visita"]).dt.days
        agg["antiguedad_dias"] = (fecha_ref - agg["primera_visita"]).dt.days
        agg["ticket_medio"] = agg["monetary_total"] / agg["frequency_visitas"]

        # categoría favorita y uso de promociones (moda entre las visitas hasta el corte)
        cat_favorita = (
            hasta_corte.groupby(["id_cliente_anon", "categoria_servicio"])
            .size()
            .reset_index(name="n")
            .sort_values("n", ascending=False)
            .groupby("id_cliente_anon")
            .first()["categoria_servicio"]
        )
        agg = agg.merge(cat_favorita.rename("categoria_favorita"), on="id_cliente_anon", how="left")

        # prestador habitual (moda entre las visitas hasta el corte). Se
        # conserva SOLO para mostrar en el frontal (mockup de la Entrega 05:
        # "Prestador habitual"); el contrato analítico §4 lo excluye
        # explícitamente como variable del modelo.
        prestador_habitual = (
            hasta_corte.dropna(subset=["prestador"])
            .groupby(["id_cliente_anon", "prestador"])
            .size()
            .reset_index(name="n")
            .sort_values("n", ascending=False)
            .groupby("id_cliente_anon")
            .first()["prestador"]
        )
        agg = agg.merge(prestador_habitual.rename("prestador_habitual"), on="id_cliente_anon", how="left")

        usa_promo = (
            hasta_corte.groupby("id_cliente_anon")["categoria_servicio"]
            .apply(lambda s: bool((s == "PROMOCIONES").any()))
            .rename("usa_promociones")
        )
        agg = agg.merge(usa_promo, on="id_cliente_anon", how="left")

        # variable objetivo: solo si el horizonte de 90 días ya se completó
        horizonte_completo = (fecha_ref + pd.Timedelta(days=horizonte_dias)) <= fecha_max
        if horizonte_completo:
            futuro = gold_visitas[
                (gold_visitas["fecha_visita"] > fecha_ref)
                & (gold_visitas["fecha_visita"] <= fecha_ref + pd.Timedelta(days=horizonte_dias))
            ]
            clientes_que_vuelven = set(futuro["id_cliente_anon"].unique())
            agg["retorna_en_90_dias"] = agg["id_cliente_anon"].isin(clientes_que_vuelven)
        else:
            agg["retorna_en_90_dias"] = np.nan
        agg["horizonte_completo"] = horizonte_completo

        agg["segmento_rfm"] = _segmento_rfm(agg)

        filas.append(agg)

    snapshot = pd.concat(filas, ignore_index=True)

    columnas_finales = [
        "id_cliente_anon",
        "fecha_referencia",
        "recency_dias",
        "frequency_visitas",
        "monetary_total",
        "ticket_medio",
        "primera_visita",
        "antiguedad_dias",
        "usa_promociones",
        "categoria_favorita",
        "prestador_habitual",
        "segmento_rfm",
        "identidad_ambigua_transaccional",
        "retorna_en_90_dias",
        "horizonte_completo",
    ]
    return snapshot[columnas_finales].sort_values(["fecha_referencia", "id_cliente_anon"])


# ---------------------------------------------------------------------------
# Orquestación
# ---------------------------------------------------------------------------

def ejecutar(db_path: Path, gold_dir: Path, horizonte_dias: int = 90) -> dict:
    conn = sqlite3.connect(db_path)
    gold_visitas = construir_gold_visitas(conn)
    conn.close()

    gold_snapshot = construir_gold_cliente_snapshot(gold_visitas, horizonte_dias=horizonte_dias)

    gold_dir.mkdir(parents=True, exist_ok=True)
    gold_visitas.to_parquet(gold_dir / "gold_visitas.parquet", index=False)
    gold_snapshot.to_parquet(gold_dir / "gold_cliente_snapshot.parquet", index=False)

    reporte = {
        "gold_visitas_filas": len(gold_visitas),
        "gold_visitas_clientes_unicos": gold_visitas["id_cliente_anon"].nunique(),
        "gold_snapshot_filas": len(gold_snapshot),
        "gold_snapshot_fechas_referencia": gold_snapshot["fecha_referencia"].nunique(),
        "gold_snapshot_filas_horizonte_completo": int(gold_snapshot["horizonte_completo"].sum()),
        "gold_snapshot_filas_sin_horizonte_completo": int((~gold_snapshot["horizonte_completo"]).sum()),
        "gold_snapshot_pct_retorna_1_entre_etiquetables": round(
            gold_snapshot.loc[gold_snapshot["horizonte_completo"], "retorna_en_90_dias"].mean() * 100, 1
        ),
    }
    return reporte


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", type=Path, required=True)
    parser.add_argument("--gold-dir", type=Path, required=True)
    parser.add_argument("--horizonte-dias", type=int, default=90)
    args = parser.parse_args()

    reporte = ejecutar(args.db_path, args.gold_dir, args.horizonte_dias)

    print("=== Reporte de construcción de la capa gold ===")
    for k, v in reporte.items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()