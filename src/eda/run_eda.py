"""
run_eda.py
===========

Paso 7 del roadmap: EDA orientado a riesgo de no retorno.

Consume:
  - data/gold/gold_visitas.parquet
  - data/gold/gold_cliente_snapshot.parquet

Produce:
  - docs/assets/eda/*.png   (gráficos referenciados desde docs/entregas/11_eda.md)
  - Imprime en consola las estadísticas usadas para redactar el análisis

Orientación (contrato analítico §2): todo el análisis compara "retorna"
(1) vs. "no retorna" (0), pero el foco de negocio es identificar patrones
de NO retorno -- las conclusiones se redactan en esa dirección.

Solo se usan snapshots con horizonte_completo = True para cualquier
análisis que involucre la variable objetivo (evita conclusiones basadas
en filas todavía no etiquetables).
"""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from scipy import stats

sns.set_style("whitegrid")
PALETA = {"retorna": "#2a9d8f", "no_retorna": "#e76f51"}


def cargar_datos(gold_dir: Path):
    visitas = pd.read_parquet(gold_dir / "gold_visitas.parquet")
    snapshot = pd.read_parquet(gold_dir / "gold_cliente_snapshot.parquet")
    etiquetable = snapshot[snapshot["horizonte_completo"]].copy()
    etiquetable["retorna_en_90_dias"] = etiquetable["retorna_en_90_dias"].astype(bool)
    return visitas, snapshot, etiquetable


# ---------------------------------------------------------------------------
# 1. Evolución temporal de la variable objetivo (estabilidad del problema)
# ---------------------------------------------------------------------------

def graf_evolucion_retorno(etiquetable: pd.DataFrame, out_dir: Path):
    tasa_por_corte = (
        etiquetable.groupby("fecha_referencia")["retorna_en_90_dias"]
        .mean()
        .reset_index()
    )
    n_por_corte = (
        etiquetable.groupby("fecha_referencia").size().reset_index(name="n_clientas")
    )

    fig, ax1 = plt.subplots(figsize=(9, 4.5))
    ax1.plot(tasa_por_corte["fecha_referencia"], tasa_por_corte["retorna_en_90_dias"] * 100,
             marker="o", color=PALETA["retorna"], label="% que retorna en 90 días")
    ax1.set_ylabel("% que retorna en 90 días")
    ax1.set_xlabel("Fecha de referencia (corte trimestral)")
    ax1.set_title("Evolución de la tasa de retorno por corte")
    ax1.tick_params(axis="x", rotation=45)

    ax2 = ax1.twinx()
    ax2.bar(n_por_corte["fecha_referencia"], n_por_corte["n_clientas"], alpha=0.15, color="gray", width=20)
    ax2.set_ylabel("N.º de clientas activas en el corte")

    fig.tight_layout()
    fig.savefig(out_dir / "01_evolucion_retorno.png", dpi=130)
    plt.close(fig)
    return tasa_por_corte, n_por_corte


# ---------------------------------------------------------------------------
# 2. Distribuciones RFM
# ---------------------------------------------------------------------------

def graf_distribuciones_rfm(etiquetable: pd.DataFrame, out_dir: Path):
    fig, axes = plt.subplots(2, 2, figsize=(10, 7))
    variables = [
        ("recency_dias", "Recency (días desde última visita)"),
        ("frequency_visitas", "Frequency (n.º de visitas)"),
        ("monetary_total", "Monetary (gasto acumulado, CLP)"),
        ("ticket_medio", "Ticket medio (CLP)"),
    ]
    for ax, (col, titulo) in zip(axes.flat, variables):
        sns.histplot(etiquetable[col], bins=40, ax=ax, color="#457b9d")
        ax.set_title(titulo)
        ax.set_xlabel("")
    fig.suptitle("Distribución de variables RFM (snapshots con horizonte completo)")
    fig.tight_layout()
    fig.savefig(out_dir / "02_distribuciones_rfm.png", dpi=130)
    plt.close(fig)


# ---------------------------------------------------------------------------
# 3. Comparación retorna vs. no retorna (boxplots + test estadístico)
# ---------------------------------------------------------------------------

def graf_comparacion_retorno(etiquetable: pd.DataFrame, out_dir: Path) -> dict:
    fig, axes = plt.subplots(1, 4, figsize=(14, 4.5))
    variables = ["recency_dias", "frequency_visitas", "monetary_total", "ticket_medio"]
    resultados = {}

    for ax, col in zip(axes, variables):
        sns.boxplot(
            data=etiquetable, x="retorna_en_90_dias", y=col, hue="retorna_en_90_dias", ax=ax,
            palette=[PALETA["no_retorna"], PALETA["retorna"]], showfliers=False, legend=False,
        )
        ax.set_xticks([0, 1])
        ax.set_xticklabels(["No retorna", "Retorna"])
        ax.set_xlabel("")
        ax.set_title(col)

        grupo_si = etiquetable.loc[etiquetable["retorna_en_90_dias"], col]
        grupo_no = etiquetable.loc[~etiquetable["retorna_en_90_dias"], col]
        u_stat, p_valor = stats.mannwhitneyu(grupo_si, grupo_no, alternative="two-sided")
        resultados[col] = {
            "mediana_retorna": grupo_si.median(),
            "mediana_no_retorna": grupo_no.median(),
            "p_valor_mannwhitney": p_valor,
        }

    fig.suptitle("Retorna vs. no retorna: comparación de variables RFM")
    fig.tight_layout()
    fig.savefig(out_dir / "03_comparacion_retorno.png", dpi=130)
    plt.close(fig)
    return resultados


# ---------------------------------------------------------------------------
# 4. Retorno por categoría favorita
# ---------------------------------------------------------------------------

def graf_retorno_por_categoria(etiquetable: pd.DataFrame, out_dir: Path, min_n=30):
    resumen = (
        etiquetable.groupby("categoria_favorita")
        .agg(n=("retorna_en_90_dias", "size"), tasa_retorno=("retorna_en_90_dias", "mean"))
        .query("n >= @min_n")
        .sort_values("tasa_retorno")
    )
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(resumen.index, resumen["tasa_retorno"] * 100, color="#f4a261")
    ax.set_xlabel("% que retorna en 90 días")
    ax.set_title(f"Tasa de retorno por categoría favorita (n ≥ {min_n})")
    fig.tight_layout()
    fig.savefig(out_dir / "04_retorno_por_categoria.png", dpi=130)
    plt.close(fig)
    return resumen


# ---------------------------------------------------------------------------
# 5. Retorno por segmento RFM
# ---------------------------------------------------------------------------

def graf_retorno_por_segmento(etiquetable: pd.DataFrame, out_dir: Path):
    resumen = (
        etiquetable[etiquetable["segmento_rfm"] != "Sin_segmentar"]
        .groupby("segmento_rfm")
        .agg(n=("retorna_en_90_dias", "size"), tasa_retorno=("retorna_en_90_dias", "mean"))
    )
    orden = ["Inactivas", "En_riesgo", "Leales", "Campeonas"]
    resumen = resumen.reindex(orden)

    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.bar(resumen.index, resumen["tasa_retorno"] * 100,
           color=["#e76f51", "#f4a261", "#2a9d8f", "#264653"])
    ax.set_ylabel("% que retorna en 90 días")
    ax.set_title("Tasa de retorno por segmento RFM")
    for i, v in enumerate(resumen["tasa_retorno"] * 100):
        ax.text(i, v + 1, f"{v:.0f}%", ha="center")
    fig.tight_layout()
    fig.savefig(out_dir / "05_retorno_por_segmento.png", dpi=130)
    plt.close(fig)
    return resumen


# ---------------------------------------------------------------------------
# 6. Correlación entre variables numéricas
# ---------------------------------------------------------------------------

def graf_correlacion(etiquetable: pd.DataFrame, out_dir: Path):
    cols = ["recency_dias", "frequency_visitas", "monetary_total", "ticket_medio",
            "antiguedad_dias", "retorna_en_90_dias"]
    corr = etiquetable[cols].astype(float).corr()

    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="RdBu_r", center=0, ax=ax, vmin=-1, vmax=1)
    ax.set_title("Correlación entre variables (incluida la variable objetivo)")
    fig.tight_layout()
    fig.savefig(out_dir / "06_correlacion.png", dpi=130)
    plt.close(fig)
    return corr


# ---------------------------------------------------------------------------
# 7. Evolución temporal del volumen de visitas (contexto del negocio)
# ---------------------------------------------------------------------------

def graf_visitas_mensuales(visitas: pd.DataFrame, out_dir: Path):
    mensual = (
        visitas.set_index("fecha_visita")
        .resample("ME")["id_visita"]
        .count()
    )
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(mensual.index, mensual.values, marker="o", color="#2a9d8f", markersize=3)
    ax.set_ylabel("N.º de visitas")
    ax.set_title("Volumen de visitas pagadas por mes")
    fig.tight_layout()
    fig.savefig(out_dir / "07_visitas_mensuales.png", dpi=130)
    plt.close(fig)
    return mensual


# ---------------------------------------------------------------------------
# 8. Impacto de identidad_ambigua_transaccional (QA heredado del paso 4)
# ---------------------------------------------------------------------------

def comparar_identidad_ambigua(etiquetable: pd.DataFrame) -> dict:
    resumen = etiquetable.groupby("identidad_ambigua_transaccional").agg(
        n=("retorna_en_90_dias", "size"),
        tasa_retorno=("retorna_en_90_dias", "mean"),
        recency_media=("recency_dias", "mean"),
        frequency_media=("frequency_visitas", "mean"),
        monetary_media=("monetary_total", "mean"),
    )
    return resumen


# ---------------------------------------------------------------------------
# Orquestación
# ---------------------------------------------------------------------------

def ejecutar(gold_dir: Path, out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    visitas, snapshot, etiquetable = cargar_datos(gold_dir)

    tasa_por_corte, n_por_corte = graf_evolucion_retorno(etiquetable, out_dir)
    graf_distribuciones_rfm(etiquetable, out_dir)
    comparacion = graf_comparacion_retorno(etiquetable, out_dir)
    retorno_categoria = graf_retorno_por_categoria(etiquetable, out_dir)
    retorno_segmento = graf_retorno_por_segmento(etiquetable, out_dir)
    corr = graf_correlacion(etiquetable, out_dir)
    visitas_mensuales = graf_visitas_mensuales(visitas, out_dir)
    identidad_ambigua = comparar_identidad_ambigua(etiquetable)

    return {
        "n_snapshots_etiquetables": len(etiquetable),
        "n_clientas_unicas_etiquetables": etiquetable["id_cliente_anon"].nunique(),
        "tasa_retorno_global": etiquetable["retorna_en_90_dias"].mean(),
        "tasa_retorno_por_corte": tasa_por_corte,
        "comparacion_rfm": comparacion,
        "retorno_por_categoria": retorno_categoria,
        "retorno_por_segmento": retorno_segmento,
        "correlacion": corr,
        "identidad_ambigua": identidad_ambigua,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gold-dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True,
                         help="Carpeta donde guardar los gráficos, ej. docs/assets/eda")
    args = parser.parse_args()

    reporte = ejecutar(args.gold_dir, args.out_dir)

    print("=== Reporte de EDA ===")
    print(f"Snapshots etiquetables: {reporte['n_snapshots_etiquetables']}")
    print(f"Clientas únicas: {reporte['n_clientas_unicas_etiquetables']}")
    print(f"Tasa de retorno global: {reporte['tasa_retorno_global']*100:.1f}%")
    print()
    print("Comparación retorna vs. no retorna (mediana, p-valor Mann-Whitney):")
    for var, res in reporte["comparacion_rfm"].items():
        print(f"  {var}: retorna={res['mediana_retorna']:.1f} | no_retorna={res['mediana_no_retorna']:.1f} | p={res['p_valor_mannwhitney']:.2e}")
    print()
    print("Retorno por segmento RFM:")
    print(reporte["retorno_por_segmento"])
    print()
    print("Impacto de identidad_ambigua_transaccional:")
    print(reporte["identidad_ambigua"])


if __name__ == "__main__":
    main()