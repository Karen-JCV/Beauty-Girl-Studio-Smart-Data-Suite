"""
Beauty Girl Studio Smart Data Suite
Dashboard Streamlit - versión visual renovada

Principios:
- Mantiene intacta la capa analítica: scoring_actual.parquet + gold_visitas.parquet
  + gold_cliente_snapshot.parquet.
- No reentrena ni toca el modelo.
- Respeta model_meta.json como fuente de umbrales.
- La navegación lateral es funcional y reutiliza los mismos datos Gold.
- Las vistas adicionales son exploratorias y no introducen nuevas métricas de modelo.

Ejecutar:
    streamlit run dashboard/app.py
"""

from __future__ import annotations

import io
import json
import os
import base64
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.offsetbox import OffsetImage, AnnotationBbox


# =============================================================================
# CONFIGURACIÓN
# =============================================================================

st.set_page_config(
    page_title="Beauty Girl Studio · Smart Data Suite",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Paleta basada en el mockup / Entrega 5
FUCHSIA = "#C9184A"
FUCHSIA_DARK = "#8F1538"
GOLD = "#D7A12B"
TERRACOTTA = "#F3A188"
TERRACOTTA_DARK = "#E4876A"
CREAM = "#FFF8F4"
CREAM_2 = "#FFF1EA"
WHITE = "#FFFFFF"
TEXT = "#2F2B2A"
MUTED = "#817773"
BORDER = "#EBD7CC"
HIGH = "#D62839"
MEDIUM = "#F0A202"
LOW = "#55A630"
RISK_HIGH_AUTUMN = "#C96B5B"
RISK_MEDIUM_AUTUMN = "#D8A13B"
RISK_LOW_AUTUMN = "#8A9A62"
AXIS_TEXT = "#625A56"
TABLE_HEADER = "#4E4845"
GREEN_BG = "#EAF6E6"
RED_BG = "#FDEBED"
YELLOW_BG = "#FFF5D9"

GOLD_DIR = Path(os.environ.get("GOLD_DATA_DIR", "data/gold"))
MODELS_DIR = GOLD_DIR.parent / "models"


# =============================================================================
# CSS
# =============================================================================

st.markdown(
    f"""
<style>
    /* ---------- Base ---------- */
    .stApp {{
        background: {CREAM};
        color: {TEXT};
    }}

    .main .block-container {{
        max-width: 1500px;
        padding: 1.2rem 2rem 2rem 2rem;
    }}

    html, body, [class*="css"] {{
        font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        color: {TEXT};
    }}

    p, span, label, div {{
        color: inherit;
    }}

    /* ---------- Sidebar ---------- */
    section[data-testid="stSidebar"] {{
        background: {TERRACOTTA};
        border-right: 1px solid rgba(120,60,40,.12);
    }}

    section[data-testid="stSidebar"] > div {{
        padding-top: 1rem;
    }}

    section[data-testid="stSidebar"] * {{
        color: #fff !important;
    }}

    .brand {{
        padding: 0.25rem 0.3rem 1rem 0.3rem;
    }}

    .brand-mark {{
        width: 98px;
        height: 98px;
        border-radius: 50%;
        margin: 0 auto 0.75rem auto;
        background: #FFE8DF;
        border: 3px solid rgba(255,255,255,.8);
        display: flex;
        align-items: center;
        justify-content: center;
        color: {FUCHSIA} !important;
        font-weight: 800;
        font-size: 13px;
        text-align: center;
        line-height: 1.05;
        box-shadow: 0 4px 14px rgba(120,60,40,.12);
    }}

    .brand-title {{
        font-size: 0.88rem;
        font-weight: 750;
        line-height: 1.2;
        text-align: left;
        color: #fff !important;
    }}

    .nav-caption {{
        margin: .9rem .2rem .35rem .2rem;
        font-size: .68rem;
        text-transform: uppercase;
        letter-spacing: .11em;
        opacity: .75;
        color: #fff !important;
    }}

    /* Sidebar radio navigation */
    section[data-testid="stSidebar"] div[data-testid="stRadio"] > label {{
        display: none;
    }}

    section[data-testid="stSidebar"] div[role="radiogroup"] {{
        gap: 0.2rem;
    }}

    section[data-testid="stSidebar"] div[role="radiogroup"] > label {{
        border-radius: 9px;
        padding: .48rem .65rem;
        min-height: 37px;
        background: transparent;
        transition: background .15s ease;
    }}

    section[data-testid="stSidebar"] div[role="radiogroup"] > label:hover {{
        background: rgba(255,255,255,.12);
    }}

    section[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) {{
        background: {FUCHSIA_DARK};
        box-shadow: inset 4px 0 0 #fff;
    }}

    section[data-testid="stSidebar"] div[role="radiogroup"] > label > div:first-child {{
        display: none;
    }}

    section[data-testid="stSidebar"] div[role="radiogroup"] p {{
        color: #fff !important;
        font-size: .84rem;
        font-weight: 600;
        margin: 0;
    }}

    .sidebar-divider {{
        border-top: 1px solid rgba(255,255,255,.25);
        margin: .85rem 0;
    }}

    section[data-testid="stSidebar"] .stSelectbox label,
    section[data-testid="stSidebar"] .stMultiSelect label,
    section[data-testid="stSidebar"] .stCheckbox label,
    section[data-testid="stSidebar"] .stSlider label,
    section[data-testid="stSidebar"] .stToggle label {{
        font-size: .68rem !important;
        text-transform: uppercase;
        letter-spacing: .06em;
        font-weight: 750 !important;
    }}

    section[data-testid="stSidebar"] .stSelectbox > div > div,
    section[data-testid="stSidebar"] .stMultiSelect > div > div {{
        background: rgba(255,255,255,.94);
        border: 1px solid rgba(120,60,40,.15);
        border-radius: 8px;
        color: {TEXT};
    }}

    section[data-testid="stSidebar"] .stSelectbox *,
    section[data-testid="stSidebar"] .stMultiSelect * {{
        color: {TEXT} !important;
    }}

    /* ---------- Header ---------- */
    .page-header {{
        background: {WHITE};
        border-radius: 0 0 12px 12px;
        border-bottom: 4px solid {GOLD};
        padding: 1rem 1.25rem .9rem 1.25rem;
        margin-bottom: 1rem;
        box-shadow: 0 1px 4px rgba(80,40,20,.05);
    }}

    .page-title {{
        font-size: 1.75rem;
        line-height: 1.1;
        font-weight: 800;
        margin: 0;
        color: {TEXT};
    }}

    .page-subtitle {{
        margin: .35rem 0 0 0;
        color: {MUTED};
        font-size: .92rem;
    }}

    .suite-badge {{
        display: inline-block;
        background: #F8DCE5;
        color: {FUCHSIA} !important;
        padding: .38rem .8rem;
        border-radius: 999px;
        font-size: .72rem;
        font-weight: 750;
        white-space: nowrap;
    }}

    /* ---------- Cards ---------- */
    .card {{
        background: {WHITE};
        border: 1px solid {BORDER};
        border-radius: 12px;
        padding: 1rem 1.1rem;
        box-shadow: 0 1px 4px rgba(80,40,20,.04);
    }}

    .card-title {{
        color: {FUCHSIA};
        font-size: 1rem;
        font-weight: 800;
        margin-bottom: .15rem;
    }}

    .card-caption {{
        color: {MUTED};
        font-size: .73rem;
        margin-bottom: .7rem;
    }}

    .kpi {{
        background: {WHITE};
        border: 1px solid {BORDER};
        border-radius: 11px;
        padding: .95rem 1rem .85rem 1rem;
        min-height: 108px;
    }}

    .kpi-label {{
        color: #625A56;
        font-size: .74rem;
        font-weight: 650;
    }}

    .kpi-value {{
        color: {FUCHSIA};
        font-size: 1.85rem;
        line-height: 1.05;
        font-weight: 850;
        margin-top: .4rem;
    }}

    .kpi-help {{
        color: {MUTED};
        font-size: .67rem;
        margin-top: .28rem;
    }}

    /* ---------- Ranking rows ---------- */
    .ranking-head {{
        display: grid;
        grid-template-columns: 1.25fr .9fr .95fr .55fr .7fr;
        gap: .65rem;
        color: {MUTED};
        font-size: .67rem;
        font-weight: 750;
        text-transform: uppercase;
        letter-spacing: .03em;
        padding: .1rem .25rem .45rem .25rem;
    }}

    .client-row {{
        border-top: 1px solid #F0E0D7;
        padding: .6rem .15rem;
    }}

    .client-id {{
        font-weight: 750;
        color: {TEXT};
        font-size: .86rem;
    }}

    .client-muted {{
        color: {MUTED};
        font-size: .68rem;
    }}

    .score {{
        font-weight: 800;
        font-size: .82rem;
    }}

    .riskbar {{
        height: 5px;
        background: #E9DDD5;
        border-radius: 999px;
        overflow: hidden;
        margin-top: .28rem;
        width: 100%;
    }}

    .riskbar > div {{
        height: 100%;
        border-radius: 999px;
    }}

    .badge {{
        display: inline-block;
        padding: .22rem .5rem;
        border-radius: 999px;
        font-size: .64rem;
        font-weight: 800;
        letter-spacing: .03em;
    }}

    .badge-high {{ background: {RED_BG}; color: {HIGH} !important; }}
    .badge-medium {{ background: {YELLOW_BG}; color: #B56C00 !important; }}
    .badge-low {{ background: {GREEN_BG}; color: #3F7D20 !important; }}

    /* ---------- Streamlit buttons ---------- */
    div.stButton > button {{
        border: 1px solid {BORDER};
        background: {WHITE};
        color: {TEXT};
        border-radius: 8px;
        font-weight: 650;
        min-height: 36px;
    }}

    div.stButton > button:hover {{
        border-color: {FUCHSIA};
        color: {FUCHSIA};
    }}

    .primary-action button {{
        background: {FUCHSIA} !important;
        border-color: {FUCHSIA} !important;
        color: #fff !important;
    }}

    .gold-action button {{
        background: {GOLD} !important;
        border-color: {GOLD} !important;
        color: #fff !important;
    }}

    /* ---------- Tables / dataframe ---------- */
    [data-testid="stDataFrame"] {{
        border: 1px solid {BORDER};
        border-radius: 10px;
    }}

    /* Tables: gris carbón suave, evitando el negro puro */
    [data-testid="stDataFrame"] [role="columnheader"] {{
        background: #4E4845 !important;
        color: #FFFFFF !important;
    }}

    [data-testid="stDataFrame"] [role="gridcell"] {{
        color: #4A4441 !important;
    }}

    /* ---------- Download buttons ---------- */
    [data-testid="stDownloadButton"] button {{
        background: #3F3A38 !important;
        border: 1px solid #3F3A38 !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        border-radius: 8px !important;
    }}

    [data-testid="stDownloadButton"] button:hover {{
        background: {FUCHSIA} !important;
        border-color: {FUCHSIA} !important;
        color: #FFFFFF !important;
    }}

    [data-testid="stDownloadButton"] button * {{
        color: #FFFFFF !important;
    }}

    /* ---------- Info blocks ---------- */
    .note {{
        background: {CREAM_2};
        border-left: 4px solid {GOLD};
        border-radius: 6px;
        padding: .7rem .85rem;
        color: #625A56;
        font-size: .76rem;
        line-height: 1.4;
    }}

    .metric-small {{
        font-size: .72rem;
        color: {MUTED};
    }}

    .section-space {{
        margin-top: .85rem;
    }}

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{
        gap: .3rem;
    }}

    .stTabs [data-baseweb="tab"] {{
        border-radius: 7px 7px 0 0;
    }}

    /* Hide Streamlit chrome that does not belong to product */
    #MainMenu {{ visibility: hidden; }}
    footer {{ visibility: hidden; }}
    header[data-testid="stHeader"] {{ background: transparent; }}
</style>
""",
    unsafe_allow_html=True,
)


# =============================================================================
# DATA
# =============================================================================

@st.cache_data(show_spinner=False)
def cargar_datos():
    scoring = pd.read_parquet(GOLD_DIR / "scoring_actual.parquet")
    visitas = pd.read_parquet(GOLD_DIR / "gold_visitas.parquet")
    snapshot_hist = pd.read_parquet(GOLD_DIR / "gold_cliente_snapshot.parquet")

    scoring["fecha_referencia"] = pd.to_datetime(scoring["fecha_referencia"])
    visitas["fecha_visita"] = pd.to_datetime(visitas["fecha_visita"])
    snapshot_hist["fecha_referencia"] = pd.to_datetime(snapshot_hist["fecha_referencia"])
    return scoring, visitas, snapshot_hist


@st.cache_data(show_spinner=False)
def cargar_umbrales():
    with open(MODELS_DIR / "model_meta.json", encoding="utf-8") as f:
        return json.load(f)


try:
    scoring, visitas, snapshot_hist = cargar_datos()
    meta = cargar_umbrales()
except FileNotFoundError as exc:
    st.error(
        "No se encuentran los artefactos necesarios del dashboard. "
        "Ejecuta primero el pipeline de scoring según docs/entregas/15_dashboard.md."
    )
    st.exception(exc)
    st.stop()


if "excluidas" not in st.session_state:
    st.session_state.excluidas = {}


# =============================================================================
# HELPERS
# =============================================================================

def riesgo_badge(banda: str) -> str:
    cls = {"Alto": "badge-high", "Medio": "badge-medium", "Bajo": "badge-low"}.get(
        banda, "badge-medium"
    )
    return f'<span class="badge {cls}">{str(banda).upper()}</span>'


def risk_color(banda: str) -> str:
    return {"Alto": HIGH, "Medio": MEDIUM, "Bajo": LOW}.get(banda, GOLD)


def risk_bar(score: float, banda: str) -> str:
    width = max(0, min(100, float(score)))
    return (
        f'<div class="riskbar"><div style="width:{width:.0f}%;'
        f'background:{risk_color(banda)};"></div></div>'
    )


def fmt_money(value) -> str:
    if pd.isna(value):
        return "—"
    return f"${float(value):,.2f}"


def fmt_pct(value) -> str:
    if pd.isna(value):
        return "—"
    return f"{float(value) * 100:.2f}%"


def fmt_num2(value) -> str:
    if pd.isna(value):
        return "—"
    return f"{float(value):,.2f}"


def dark_table_style(df: pd.DataFrame):
    """Tabla oscura suave para las vistas RFM, evitando el negro puro."""
    return (
        df.style
        .set_properties(**{
            "background-color": "#5A5451",
            "color": "#FFFFFF",
            "border-color": "#746C68",
        })
        .set_table_styles([
            {
                "selector": "th",
                "props": [
                    ("background-color", "#4E4845"),
                    ("color", "#FFFFFF"),
                    ("font-weight", "700"),
                    ("border-color", "#746C68"),
                ],
            },
        ])
    )


def logo_data_uri() -> str | None:
    """Devuelve el logo como data URI para que el dashboard sea autónomo."""
    candidates = [
        Path(__file__).resolve().parent / "assets" / "BGS.jpg",
        Path(__file__).resolve().parent / "BGS.jpg",
        Path("assets") / "BGS.jpg",
    ]
    for path in candidates:
        if path.exists():
            encoded = base64.b64encode(path.read_bytes()).decode("ascii")
            return f"data:image/jpeg;base64,{encoded}"
    return None


def add_pdf_logo(ax):
    """Añade el logo de Beauty Girl Studio a los informes PDF."""
    candidates = [
        Path(__file__).resolve().parent / "assets" / "BGS.jpg",
        Path(__file__).resolve().parent / "BGS.jpg",
        Path("assets") / "BGS.jpg",
    ]
    for path in candidates:
        if path.exists():
            try:
                img = mpimg.imread(path)
                imagebox = OffsetImage(img, zoom=0.12)
                ab = AnnotationBbox(imagebox, (0.90, 0.82), xycoords="axes fraction", frameon=False)
                ax.add_artist(ab)
            except Exception:
                pass
            break


def page_header(title: str, subtitle: str):
    c1, c2 = st.columns([5, 1])
    with c1:
        st.markdown(
            f"""
            <div class="page-header">
                <div class="page-title">{title}</div>
                <div class="page-subtitle">{subtitle}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            '<div style="text-align:right;padding-top:1.05rem;">'
            '<span class="suite-badge">● Smart Data Suite</span></div>',
            unsafe_allow_html=True,
        )


def kpi_card(label: str, value: str, help_text: str = ""):
    st.markdown(
        f"""
        <div class="kpi">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-help">{help_text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def apply_risk_filters(base: pd.DataFrame):
    """Filtros del panel principal. La fecha se muestra como corte porque
    producción solo contiene un snapshot actual, tal como documenta E15."""
    with st.sidebar:
        st.markdown('<div class="nav-caption">Filtros</div>', unsafe_allow_html=True)

        fecha_ref = pd.to_datetime(base["fecha_referencia"].max())
        st.caption(f"Corte de referencia · {fecha_ref:%d/%m/%Y}")

        segmentos = sorted(base["segmento_rfm"].dropna().astype(str).unique())
        segmento = st.selectbox(
            "Segmento RFM",
            ["Todos los segmentos"] + segmentos,
            index=0,
        )

        st.markdown("**Nivel de riesgo**")
        f_alto = st.checkbox("Alto riesgo", value=True)
        f_medio = st.checkbox("Medio riesgo", value=True)
        f_bajo = st.checkbox("Bajo riesgo", value=False)

        categorias = sorted(base["categoria_favorita"].dropna().astype(str).unique())
        categoria = st.selectbox(
            "Categoría favorita",
            ["Todas las categorías"] + categorias,
            index=0,
        )

        prestadores = sorted(base["prestador_habitual"].dropna().astype(str).unique())
        prestador = st.selectbox(
            "Prestador habitual",
            ["Todos los prestadores"] + prestadores,
            index=0,
        )

        antig_max = int(max(1, base["antiguedad_dias"].max()))
        antig = st.slider("Antigüedad (días)", 0, antig_max, (0, antig_max))

        ticket_max = float(max(1, base["ticket_medio"].max()))
        ticket = st.slider("Ticket promedio ($)", 0.0, ticket_max, (0.0, ticket_max))

        freq_max = int(max(1, base["frequency_visitas"].max()))
        frecuencia = st.slider("Frecuencia de visitas", 1, freq_max, (1, freq_max))

        historial = st.toggle(
            "Solo historial suficiente (≥3 visitas)",
            value=False,
        )

    bandas = [
        b
        for b, activo in [
            ("Alto", f_alto),
            ("Medio", f_medio),
            ("Bajo", f_bajo),
        ]
        if activo
    ]

    df = base[
        base["banda_riesgo"].isin(bandas)
        & base["antiguedad_dias"].between(*antig)
        & base["ticket_medio"].between(*ticket)
        & base["frequency_visitas"].between(*frecuencia)
        & (~base["id_cliente_anon"].isin(st.session_state.excluidas))
    ].copy()

    if segmento != "Todos los segmentos":
        df = df[df["segmento_rfm"].astype(str) == segmento]
    if categoria != "Todas las categorías":
        df = df[df["categoria_favorita"].astype(str) == categoria]
    if prestador != "Todos los prestadores":
        df = df[df["prestador_habitual"].astype(str) == prestador]
    if historial:
        df = df[df["frequency_visitas"] >= 3]

    return df, fecha_ref


def render_kpis(df: pd.DataFrame, base: pd.DataFrame):
    # Los KPIs representan el conjunto actualmente filtrado; si no hay filas,
    # se conserva el contexto global para evitar tarjetas vacías.
    kpi_df = df if not df.empty else base
    c1, c2, c3, c4 = st.columns(4)

    pct_alto = (kpi_df["banda_riesgo"] == "Alto").mean() * 100
    prob_media = kpi_df["prob_retorno_90d"].mean() * 100
    ticket = kpi_df["ticket_medio"].mean()
    visitas_media = kpi_df["frequency_visitas"].mean()

    with c1:
        kpi_card("% de clientas en riesgo", f"{pct_alto:.2f}%", "Clientas en banda de riesgo alto")
    with c2:
        kpi_card("Probabilidad de retorno", f"{prob_media:.2f}%", "Probabilidad media para los próximos 90 días")
    with c3:
        kpi_card("Ticket promedio", fmt_money(ticket), "Gasto medio por visita")
    with c4:
        kpi_card("Visitas promedio", f"{visitas_media:.0f}", "Número medio de visitas registradas")


def chart_layout(fig, height=280):
    """Estilo común de gráficos: ejes legibles en gris oscuro, no negro."""
    fig.update_layout(
        height=height,
        margin=dict(l=8, r=8, t=18, b=8),
        paper_bgcolor=WHITE,
        plot_bgcolor=WHITE,
        font=dict(color=AXIS_TEXT, family="Inter, Arial, sans-serif", size=11),
        legend=dict(orientation="h", yanchor="bottom", y=1.01, x=0, font=dict(color=AXIS_TEXT)),
        xaxis=dict(
            showgrid=False, zeroline=False,
            tickfont=dict(color=AXIS_TEXT, size=11),
            title_font=dict(color=AXIS_TEXT, size=11),
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="#E9DDD5",
            zeroline=False,
            tickfont=dict(color=AXIS_TEXT, size=11),
            title_font=dict(color=AXIS_TEXT, size=11),
        ),
        hovermode="x unified",
    )
    return fig


def plot_visitas_historial(hist: pd.DataFrame, height=330, line_width=3, marker_size=7):
    """Gráfico de visitas robusto para historiales cortos."""
    fig = go.Figure()
    if len(hist) == 1:
        amount = float(hist["importe_total"].iloc[0])
        label = pd.to_datetime(hist["fecha_visita"].iloc[0]).strftime("%d/%m/%Y")
        fig.add_trace(
            go.Scatter(
                x=["Única visita"],
                y=[amount],
                mode="markers+text",
                text=[fmt_money(amount)],
                textposition="top center",
                marker=dict(color=GOLD, size=10),
                name="Visita",
                hovertemplate=f"Fecha: {label}<br>Importe: {fmt_money(amount)}<extra></extra>",
            )
        )
        lower = max(0, amount * 0.70)
        upper = max(amount * 1.30, amount + 1)
        fig.update_yaxes(range=[lower, upper], tickprefix="$", tickformat=",.2f", title="Importe")
        fig.update_xaxes(title=None)
        chart_layout(fig, height)
        return fig

    fig.add_trace(
        go.Scatter(
            x=hist["fecha_visita"],
            y=hist["importe_total"],
            mode="lines+markers",
            line=dict(color=FUCHSIA, width=line_width),
            marker=dict(color=GOLD, size=marker_size),
            name="Importe",
        )
    )
    fig.update_yaxes(title="Importe", tickprefix="$", tickformat=",.2f")
    chart_layout(fig, height)
    return fig


def historial_cliente(cliente, fecha_ref):
    return visitas[
        (visitas["id_cliente_anon"] == cliente["id_cliente_anon"])
        & (visitas["fecha_visita"] >= fecha_ref - pd.Timedelta(days=180))
        & (visitas["fecha_visita"] <= fecha_ref)
    ].sort_values("fecha_visita")


def render_cliente_detail(fila, fecha_ref, compact=False):
    st.markdown(
        f"""
        <div class="card">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <div class="card-title">Detalle de Clienta</div>
                {riesgo_badge(fila["banda_riesgo"])}
            </div>
            <div style="font-weight:750;margin:.25rem 0 .65rem 0;">
                ID Cliente: #{int(fila["codigo_display"])}
            </div>
        """,
        unsafe_allow_html=True,
    )

    rows = [
        ("Segmento RFM", fila["segmento_rfm"]),
        ("Días desde la última visita", f'{int(fila["recency_dias"])} días atrás'),
        ("Visitas registradas", f'{int(fila["frequency_visitas"])} visitas'),
        ("Gasto acumulado", fmt_money(fila["monetary_total"])),
        ("Categoría favorita", fila["categoria_favorita"]),
        ("Prestador habitual", fila["prestador_habitual"]),
        ("Antigüedad", f'{int(fila["antiguedad_dias"])} días'),
        ("Probabilidad de retorno", fmt_pct(fila["prob_retorno_90d"])),
    ]

    for label, value in rows:
        st.markdown(
            f"""
            <div style="display:flex;justify-content:space-between;gap:.8rem;
                        padding:.27rem 0;border-bottom:1px solid #F5EAE4;">
                <span style="color:{MUTED};font-size:.72rem;">{label}</span>
                <strong style="font-size:.73rem;text-align:right;">{value}</strong>
            </div>
            """,
            unsafe_allow_html=True,
        )

    hist = historial_cliente(fila, fecha_ref)
    if not hist.empty:
        st.markdown(
            '<div class="card-caption" style="margin-top:.75rem;">HISTORIAL DE VISITAS · 180 DÍAS</div>',
            unsafe_allow_html=True,
        )
        fig = plot_visitas_historial(hist, height=190, line_width=2, marker_size=6)
        if len(hist) == 1:
            st.caption("Solo hay una visita registrada; se muestra como un único punto para que la escala no resulte engañosa.")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    st.markdown(
        '<div class="card-caption" style="margin-top:.35rem;">FACTORES DEL MODELO</div>',
        unsafe_allow_html=True,
    )
    factors = [fila.get("factor_1", ""), fila.get("factor_2", ""), fila.get("factor_3", "")]
    for factor in factors:
        if factor:
            st.markdown(
                f'<div style="font-size:.75rem;padding:.25rem 0;">'
                f'<span style="color:{GOLD};font-weight:800;">◆</span> {factor}</div>',
                unsafe_allow_html=True,
            )

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div style="height:.45rem;"></div>', unsafe_allow_html=True)

    with st.expander("Excluir del panel"):
        motivo = st.selectbox(
            "Motivo",
            [
                "Se mudó de ciudad",
                "No desea ser contactada",
                "Cliente inactiva por motivos personales",
                "Ya no pertenece al público objetivo",
                "Otro motivo",
            ],
            key=f"motivo_{fila['id_cliente_anon']}",
        )
        if st.button(
            "Confirmar exclusión",
            key=f"excluir_{fila['id_cliente_anon']}",
            use_container_width=True,
        ):
            st.session_state.excluidas[fila["id_cliente_anon"]] = motivo
            st.success(
                "La clienta ha sido excluida del panel. "
                "Puedes revertirla desde Configuración → Clientas excluidas."
            )
            st.rerun()


def render_risk_ranking(df: pd.DataFrame, fecha_ref):
    st.markdown(
        """
        <div class="card">
            <div class="card-title">Clientas en Riesgo de Fuga</div>
            <div class="card-caption">Ordenadas según el criterio elegido · se muestran 8 clientas por página</div>
        """,
        unsafe_allow_html=True,
    )

    if df.empty:
        st.info("Ninguna clienta cumple los filtros seleccionados.")
        st.markdown("</div>", unsafe_allow_html=True)
        return None

    sort_option = st.selectbox(
        "Ordenar",
        ["Mayor riesgo", "Menor riesgo", "Menor probabilidad de retorno", "Más días sin visitar"],
        label_visibility="collapsed",
        key="orden_riesgo",
    )

    if sort_option == "Menor riesgo":
        work = df.sort_values("score_riesgo", ascending=True).reset_index(drop=True)
    elif sort_option == "Menor probabilidad de retorno":
        work = df.sort_values("prob_retorno_90d", ascending=True).reset_index(drop=True)
    elif sort_option == "Más días sin visitar":
        work = df.sort_values("recency_dias", ascending=False).reset_index(drop=True)
    else:
        work = df.sort_values("score_riesgo", ascending=False).reset_index(drop=True)

    # Si cambian filtros u orden, la selección pasa automáticamente a la primera clienta del nuevo conjunto.
    signature = "|".join(work["id_cliente_anon"].astype(str).tolist()) + f"::{sort_option}"
    if st.session_state.get("risk_list_signature") != signature:
        st.session_state.risk_list_signature = signature
        st.session_state.risk_page = 1
        st.session_state.selected_client_id = work.iloc[0]["id_cliente_anon"]

    page_size = 8
    total_pages = max(1, (len(work) + page_size - 1) // page_size)
    current_page = int(st.session_state.get("risk_page", 1))
    current_page = min(max(current_page, 1), total_pages)

    if total_pages > 1:
        current_page = st.selectbox(
            "Página",
            list(range(1, total_pages + 1)),
            index=current_page - 1,
            format_func=lambda n: f"Página {n} de {total_pages}",
            key="risk_page_selector",
        )
        st.session_state.risk_page = current_page
    else:
        st.session_state.risk_page = 1
        st.caption(f"{len(work)} clientas")

    start_row = (current_page - 1) * page_size
    page_df = work.iloc[start_row:start_row + page_size]

    st.markdown(
        """
        <div class="ranking-head">
            <span>CLIENTA</span><span>RIESGO</span><span>RETORNO</span>
            <span>BANDA</span><span>RECENCY</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    selected_id = st.session_state.get("selected_client_id")
    page_ids = set(page_df["id_cliente_anon"])

    for _, fila in page_df.iterrows():
        cid = fila["id_cliente_anon"]
        cols = st.columns([1.25, .9, .95, .55, .7], gap="small")
        with cols[0]:
            if st.button(
                f"◆  Cliente #{int(fila['codigo_display'])}",
                key=f"sel_{cid}",
                use_container_width=True,
            ):
                st.session_state.selected_client_id = cid
                st.rerun()
            st.markdown(
                f'<div class="client-muted">RFM · {fila["segmento_rfm"]}</div>',
                unsafe_allow_html=True,
            )

        with cols[1]:
            st.markdown(
                f'<div class="score">{float(fila["score_riesgo"]):.0f}/100</div>'
                f'{risk_bar(fila["score_riesgo"], fila["banda_riesgo"])}',
                unsafe_allow_html=True,
            )

        with cols[2]:
            st.markdown(
                f'<div class="score">{fmt_pct(fila["prob_retorno_90d"])}</div>'
                f'<div class="client-muted">Prob. retorno</div>',
                unsafe_allow_html=True,
            )

        with cols[3]:
            st.markdown(riesgo_badge(fila["banda_riesgo"]), unsafe_allow_html=True)

        with cols[4]:
            st.markdown(
                f'<div class="score">{int(fila["recency_dias"])} d</div>'
                f'<div class="client-muted">sin visita</div>',
                unsafe_allow_html=True,
            )

        st.markdown('<div class="client-row"></div>', unsafe_allow_html=True)

    # Si el cambio de página deja fuera la selección, seleccionamos la primera de esa página.
    if selected_id not in page_ids and not page_df.empty:
        st.session_state.selected_client_id = page_df.iloc[0]["id_cliente_anon"]
        selected_id = st.session_state.selected_client_id

    st.markdown("</div>", unsafe_allow_html=True)
    return selected_id


def render_historical_trend(snapshot_hist, end_date=None, months=3):
    data = snapshot_hist[snapshot_hist["horizonte_completo"] == True].copy()  # noqa: E712
    if end_date is not None:
        end_date = pd.to_datetime(end_date)
        start_date = end_date - pd.DateOffset(months=months)
        data = data[data["fecha_referencia"].between(start_date, end_date)]

    tendencia = (
        data.groupby("fecha_referencia")["retorna_en_90_dias"]
        .mean()
        .reset_index()
        .sort_values("fecha_referencia")
    )

    fig = go.Figure()
    if not tendencia.empty:
        fig.add_trace(
            go.Scatter(
                x=tendencia["fecha_referencia"],
                y=tendencia["retorna_en_90_dias"] * 100,
                mode="lines+markers",
                line=dict(color=FUCHSIA, width=3),
                marker=dict(color=GOLD, size=7),
                name="Retorno observado",
            )
        )
    fig.update_yaxes(title="% que regresa en 90 días", range=[0, 100])
    fig.update_xaxes(title=None)
    chart_layout(fig, 270)
    return fig, tendencia


# =============================================================================
# SIDEBAR NAVIGATION
# =============================================================================

_logo_uri = logo_data_uri()
logo_html = (
    f'<div style="width:110px;height:110px;border-radius:50%;overflow:hidden;margin:0 auto .75rem auto;'
    f'border:3px solid rgba(255,255,255,.9);box-shadow:0 4px 14px rgba(120,60,40,.16);">'
    f'<img src="{_logo_uri}" style="width:100%;height:100%;object-fit:cover;display:block;" />'
    f'</div>' if _logo_uri else
    '<div class="brand-mark">BEAUTY<br>GIRL<br><span style="font-size:9px;">STUDIO</span></div>'
)

with st.sidebar:
    st.markdown(
        f"""
        <div class="brand">
            {logo_html}
            <div class="brand-title">Beauty Girl Studio<br>Smart Data Suite</div>
        </div>
        <div class="sidebar-divider"></div>
        <div class="nav-caption">Navegación</div>
        """,
        unsafe_allow_html=True,
    )

    NAV = {
        "⌂  Inicio": "Inicio",
        "♙  Clientas en riesgo": "Clientas en riesgo",
        "◔  Segmentos RFM": "Segmentos RFM",
        "▥  Métricas por prestador": "Métricas por prestador",
        "▣  Historial de visitas": "Historial de visitas",
        "〽  Modelo de retorno": "Modelo de retorno",
        "▤  Reportes": "Reportes",
        "⚙  Configuración": "Configuración",
    }

    selected_label = st.radio(
        "Navegación",
        list(NAV.keys()),
        label_visibility="collapsed",
        key="navigation",
    )
    page = NAV[selected_label]


# =============================================================================
# INICIO
# =============================================================================

if page == "Inicio":
    page_header(
        "Visión general del negocio",
        "Resumen de fidelización, riesgo y retorno de clientas",
    )

    base = scoring[~scoring["id_cliente_anon"].isin(st.session_state.excluidas)].copy()
    render_kpis(base, scoring)

    st.markdown('<div class="section-space"></div>', unsafe_allow_html=True)
    c1, c2 = st.columns([1.1, 1])

    with c1:
        st.markdown(
            '<div class="card"><div class="card-title">Distribución del riesgo</div>'
            '<div class="card-caption">Clientas del snapshot de producción</div></div>',
            unsafe_allow_html=True,
        )
        dist = base["banda_riesgo"].value_counts().reindex(["Alto", "Medio", "Bajo"], fill_value=0)
        fig = go.Figure(
            go.Bar(
                x=dist.index,
                y=dist.values,
                marker_color=[RISK_HIGH_AUTUMN, RISK_MEDIUM_AUTUMN, RISK_LOW_AUTUMN],
                text=dist.values,
                textposition="outside",
            )
        )
        fig.update_yaxes(title="Clientas")
        chart_layout(fig, 280)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with c2:
        st.markdown(
            '<div class="card"><div class="card-title">Segmentación RFM</div>'
            '<div class="card-caption">Distribución del snapshot actual</div></div>',
            unsafe_allow_html=True,
        )
        rfm = base["segmento_rfm"].value_counts().sort_values(ascending=True)
        fig = go.Figure(
            go.Bar(
                x=rfm.values,
                y=rfm.index,
                orientation="h",
                marker_color=FUCHSIA,
                text=rfm.values,
                textposition="outside",
            )
        )
        fig.update_xaxes(title="Clientas")
        chart_layout(fig, 280)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    st.markdown('<div class="section-space"></div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="card"><div class="card-title">Tendencia histórica de retorno</div>'
        '<div class="card-caption">Cortes históricos con horizonte de 90 días completo</div></div>',
        unsafe_allow_html=True,
    )
    fig, tendencia = render_historical_trend(snapshot_hist)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    st.markdown(
        '<div class="note">La línea muestra cómo ha cambiado el porcentaje de clientas que regresan, usando las fechas históricas que realmente tiene el negocio. No se inventan datos para rellenar días que no existen.</div>',
        unsafe_allow_html=True,
    )


# =============================================================================
# CLIENTAS EN RIESGO
# =============================================================================

elif page == "Clientas en riesgo":
    df, fecha_ref = apply_risk_filters(scoring)

    page_header(
        "Panel de Fidelización y Retorno",
        f"Probabilidad de retorno en 90 días · corte al {fecha_ref:%d/%m/%Y}",
    )

    render_kpis(df, scoring)

    st.markdown('<div class="section-space"></div>', unsafe_allow_html=True)
    c_rank, c_detail = st.columns([1.65, 1], gap="large")

    with c_rank:
        selected_id = render_risk_ranking(df, fecha_ref)

    with c_detail:
        if df.empty or selected_id is None:
            st.info("Selecciona una clienta del ranking para ver su detalle.")
        else:
            fila = df[df["id_cliente_anon"] == selected_id].iloc[0]
            render_cliente_detail(fila, fecha_ref)

    st.markdown('<div class="section-space"></div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)

    filtered_csv = df.to_csv(index=False).encode("utf-8")
    with c1:
        st.download_button(
            "Descargar CSV",
            filtered_csv,
            file_name="clientas_en_riesgo.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with c2:
        buffer = io.BytesIO()
        df.to_excel(buffer, index=False, engine="xlsxwriter")
        st.download_button(
            "Exportar Excel",
            buffer.getvalue(),
            file_name="clientas_en_riesgo.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    with c3:
        # PDF ejecutivo de una página, generado con matplotlib.
        pdf_buffer = io.BytesIO()
        with PdfPages(pdf_buffer) as pdf:
            fig_pdf, ax = plt.subplots(figsize=(11.69, 8.27))
            ax.axis("off")
            add_pdf_logo(ax)
            ax.text(
                0.04, 0.92,
                "Beauty Girl Studio · Informe de Fidelización y Retorno",
                fontsize=18, fontweight="bold", color=FUCHSIA,
            )
            ax.text(
                0.04, 0.87,
                f"Corte: {fecha_ref:%d/%m/%Y} · Clientas filtradas: {len(df)}",
                fontsize=10, color="#666666",
            )
            lines = [
                f"Clientas en alto riesgo: {(df['banda_riesgo'] == 'Alto').sum()}",
                f"Probabilidad media de retorno: {df['prob_retorno_90d'].mean() * 100:.2f}%",
                f"Ticket promedio: ${df['ticket_medio'].mean():,.2f}",
                f"Visitas promedio: {df['frequency_visitas'].mean():.0f}",
            ]
            y = 0.76
            for line in lines:
                ax.text(0.06, y, line, fontsize=13, color=TEXT)
                y -= 0.08
            ax.text(
                0.04, 0.38,
                "Nota: las probabilidades y puntuaciones que aparecen en este informe son las calculadas por el sistema "
                "a partir del historial disponible. El informe solo resume la información; no cambia los datos del negocio.",
                fontsize=9, color="#666666", wrap=True,
            )
            pdf.savefig(fig_pdf, bbox_inches="tight")
            plt.close(fig_pdf)

        st.download_button(
            "Exportar informe PDF",
            pdf_buffer.getvalue(),
            file_name="informe_fidelizacion.pdf",
            mime="application/pdf",
            use_container_width=True,
        )


# =============================================================================
# SEGMENTOS RFM
# =============================================================================

elif page == "Segmentos RFM":
    page_header(
        "Segmentos RFM",
        "Distribución y comportamiento de las clientas por segmento",
    )

    base = scoring[~scoring["id_cliente_anon"].isin(st.session_state.excluidas)].copy()

    rfm_order = ["Campeonas", "Leales", "En_riesgo", "Inactivas", "Sin_segmentar"]
    summary = (
        base.groupby("segmento_rfm", dropna=False)
        .agg(
            clientas=("id_cliente_anon", "nunique"),
            score_riesgo=("score_riesgo", "mean"),
            prob_retorno=("prob_retorno_90d", "mean"),
            ticket=("ticket_medio", "mean"),
            visitas=("frequency_visitas", "mean"),
            recency=("recency_dias", "mean"),
        )
        .reindex(rfm_order)
        .dropna(how="all")
        .reset_index()
    )

    c1, c2 = st.columns([1.2, 1])
    with c1:
        st.markdown(
            '<div class="card"><div class="card-title">Resumen por segmento</div>'
            '<div class="card-caption">Resumen de cómo se comportan las clientas de cada grupo</div></div>',
            unsafe_allow_html=True,
        )
        display = summary.rename(
            columns={
                "segmento_rfm": "Segmento",
                "clientas": "Clientas",
                "score_riesgo": "Score riesgo medio",
                "prob_retorno": "Retorno medio",
                "ticket": "Ticket medio",
                "visitas": "Visitas medias",
                "recency": "Recency medio",
            }
        )
        display["Clientas"] = display["Clientas"].fillna(0).astype(int).astype(str)
        display["Score riesgo medio"] = display["Score riesgo medio"].map(lambda x: f"{x:.2f}" if pd.notna(x) else "—")
        display["Retorno medio"] = display["Retorno medio"].map(lambda x: f"{x * 100:.2f}%" if pd.notna(x) else "—")
        display["Ticket medio"] = display["Ticket medio"].map(lambda x: f"${x:,.2f}" if pd.notna(x) else "—")
        display["Visitas medias"] = display["Visitas medias"].map(lambda x: f"{x:.2f}" if pd.notna(x) else "—")
        display["Recency medio"] = display["Recency medio"].map(lambda x: f"{x:.0f} d" if pd.notna(x) else "—")
        st.dataframe(dark_table_style(display), hide_index=True, use_container_width=True)

    with c2:
        fig = go.Figure(
            go.Bar(
                x=summary["segmento_rfm"],
                y=summary["prob_retorno"] * 100,
                marker_color=FUCHSIA,
                text=(summary["prob_retorno"] * 100).round(0).astype(int).astype(str) + "%",
                textposition="outside",
            )
        )
        fig.update_yaxes(title="% probabilidad media de retorno", range=[0, 100])
        chart_layout(fig, 300)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    st.markdown('<div class="section-space"></div>', unsafe_allow_html=True)
    selected_segment = st.selectbox("Explorar segmento", rfm_order)
    seg = base[base["segmento_rfm"] == selected_segment].sort_values("score_riesgo", ascending=False)

    st.markdown(
        f'<div class="card"><div class="card-title">Clientas · {selected_segment}</div>'
        f'<div class="card-caption">{len(seg)} clientas en el snapshot actual</div></div>',
        unsafe_allow_html=True,
    )
    detalle_rfm = (
        seg[
            [
                "codigo_display",
                "score_riesgo",
                "prob_retorno_90d",
                "recency_dias",
                "frequency_visitas",
                "ticket_medio",
                "banda_riesgo",
            ]
        ]
        .rename(
            columns={
                "codigo_display": "Cliente",
                "score_riesgo": "Score riesgo",
                "prob_retorno_90d": "Prob. retorno",
                "recency_dias": "Recency",
                "frequency_visitas": "Visitas",
                "ticket_medio": "Ticket",
                "banda_riesgo": "Riesgo",
            }
        )
    )
    detalle_rfm["Score riesgo"] = detalle_rfm["Score riesgo"].map(lambda x: f"{x:.2f}" if pd.notna(x) else "—")
    detalle_rfm["Prob. retorno"] = detalle_rfm["Prob. retorno"].map(lambda x: f"{x * 100:.2f}%" if pd.notna(x) else "—")
    detalle_rfm["Ticket"] = detalle_rfm["Ticket"].map(lambda x: f"${x:,.2f}" if pd.notna(x) else "—")
    detalle_rfm["Visitas"] = detalle_rfm["Visitas"].map(lambda x: f"{x:.2f}" if pd.notna(x) else "—")
    st.dataframe(dark_table_style(detalle_rfm), hide_index=True, use_container_width=True)


# =============================================================================
# MÉTRICAS POR PRESTADOR
# =============================================================================

elif page == "Métricas por prestador":
    page_header(
        "Métricas por prestador",
        "Comportamiento agregado de las clientas según su prestador habitual",
    )

    base = scoring[~scoring["id_cliente_anon"].isin(st.session_state.excluidas)].copy()
    base["prestador_habitual"] = base["prestador_habitual"].fillna("Sin informar")
    base = base[base["prestador_habitual"] != "Sin informar"].copy()

    provider = (
        base.groupby("prestador_habitual")
        .agg(
            clientas=("id_cliente_anon", "nunique"),
            riesgo_medio=("score_riesgo", "mean"),
            retorno_medio=("prob_retorno_90d", "mean"),
            ticket_medio=("ticket_medio", "mean"),
            visitas_medias=("frequency_visitas", "mean"),
            recency_media=("recency_dias", "mean"),
        )
        .sort_values("riesgo_medio", ascending=False)
        .reset_index()
    )

    c1, c2 = st.columns([1.15, 1])
    with c1:
        st.markdown(
            '<div class="card"><div class="card-title">Resumen por prestador</div>'
            '<div class="card-caption">Aquí puedes ver, de forma resumida, el comportamiento de las clientas que suelen acudir a cada prestador, es decir, sirve para conocer el perfil de la cartera por prestador.</div></div>',
            unsafe_allow_html=True,
        )
        view = provider.rename(
            columns={
                "prestador_habitual": "Prestador",
                "clientas": "Clientas",
                "riesgo_medio": "Score riesgo medio",
                "retorno_medio": "Retorno medio",
                "ticket_medio": "Ticket medio",
                "visitas_medias": "Visitas medias",
                "recency_media": "Recency medio",
            }
        )
        view["Clientas"] = view["Clientas"].fillna(0).astype(int).astype(str)
        view["Score riesgo medio"] = view["Score riesgo medio"].map(lambda x: f"{x:.2f}" if pd.notna(x) else "—")
        view["Retorno medio"] = view["Retorno medio"].map(lambda x: f"{x * 100:.2f}%" if pd.notna(x) else "—")
        view["Ticket medio"] = view["Ticket medio"].map(lambda x: f"${x:,.2f}" if pd.notna(x) else "—")
        view["Visitas medias"] = view["Visitas medias"].map(lambda x: f"{x:.2f}" if pd.notna(x) else "—")
        view["Recency medio"] = view["Recency medio"].map(lambda x: f"{x:.0f} d" if pd.notna(x) else "—")
        st.dataframe(dark_table_style(view), hide_index=True, use_container_width=True)
        st.markdown(
            """<div class="card-caption" style="margin-top:.6rem;line-height:1.55;">
                <b>Qué significa cada dato:</b> <b>Prestador</b>: nombre del prestador del servicio ·
                <b>Clientas</b>: número de clientas de su cartera · <b>Score riesgo medio</b>: nivel medio de riesgo de esas clientas (0 a 100) ·
                <b>Retorno medio</b>: porcentaje medio de clientas que se espera que vuelva en 90 días ·
                <b>Ticket medio</b>: gasto medio por visita · <b>Visitas medias</b>: número medio de visitas registradas ·
                <b>Recency medio</b>: días medios desde la última visita.
            </div>""",
            unsafe_allow_html=True,
        )

    with c2:
        fig = go.Figure(
            go.Bar(
                x=provider["riesgo_medio"],
                y=provider["prestador_habitual"],
                orientation="h",
                marker_color=GOLD,
            )
        )
        fig.update_xaxes(title="Score de riesgo medio")
        chart_layout(fig, 320)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    st.markdown('<div class="note">El prestador habitual se muestra para dar contexto sobre las clientas. No se utiliza para decidir el nivel de riesgo de una clienta.</div>', unsafe_allow_html=True)


# =============================================================================
# HISTORIAL DE VISITAS
# =============================================================================

elif page == "Historial de visitas":
    page_header(
        "Historial de visitas",
        "Exploración del comportamiento real registrado en la capa Gold",
    )

    clientes = scoring.sort_values("codigo_display")[
        ["id_cliente_anon", "codigo_display"]
    ].drop_duplicates()
    cliente_code = st.selectbox(
        "Selecciona una clienta",
        clientes["codigo_display"].astype(int).tolist(),
    )
    cid = clientes.loc[clientes["codigo_display"].astype(int) == cliente_code, "id_cliente_anon"].iloc[0]
    hist = visitas[visitas["id_cliente_anon"] == cid].sort_values("fecha_visita")

    if hist.empty:
        st.info("No hay visitas registradas para esta clienta.")
    else:
        total = hist["importe_total"].sum()
        visitas_n = len(hist)
        ticket = hist["importe_total"].mean()

        c1, c2, c3 = st.columns(3)
        with c1:
            kpi_card("Visitas registradas", f"{visitas_n}", "Historial disponible")
        with c2:
            kpi_card("Gasto acumulado", f"${total:,.2f}", "Importe de visitas")
        with c3:
            kpi_card("Ticket medio", f"${ticket:,.2f}", "Promedio por visita")

        st.markdown('<div class="section-space"></div>', unsafe_allow_html=True)
        fig = plot_visitas_historial(hist, height=330, line_width=3, marker_size=7)
        if len(hist) == 1:
            st.caption("Esta clienta tiene una sola visita registrada. El gráfico muestra ese único registro sin inventar una escala temporal.")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        c1, c2 = st.columns(2)
        with c1:
            cat = hist["categoria_servicio"].value_counts().head(8)
            fig = go.Figure(go.Bar(x=cat.values, y=cat.index, orientation="h", marker_color=FUCHSIA))
            fig.update_xaxes(title="Visitas")
            chart_layout(fig, 300)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        with c2:
            hist_table = hist[
                ["fecha_visita", "importe_total", "categoria_servicio", "prestador", "n_items"]
            ].rename(
                columns={
                    "fecha_visita": "Fecha",
                    "importe_total": "Importe",
                    "categoria_servicio": "Categoría",
                    "prestador": "Prestador",
                    "n_items": "N.º servicios",
                }
            ).copy()
            hist_table["Fecha"] = pd.to_datetime(hist_table["Fecha"]).dt.strftime("%d/%m/%Y")
            hist_table["Importe"] = hist_table["Importe"].map(fmt_money)
            st.dataframe(hist_table, hide_index=True, use_container_width=True)


# =============================================================================
# MODELO DE RETORNO
# =============================================================================

elif page == "Modelo de retorno":
    page_header(
        "Cómo se calcula el riesgo",
        "Una explicación sencilla de las señales que utiliza el sistema",
    )

    st.markdown(
        """
        <div class="note">
            Esta pantalla sirve para entender de dónde sale el nivel de riesgo que ves en el dashboard.
            El sistema analiza el historial de visitas y otros datos del negocio y calcula qué tan probable es
            que una clienta vuelva en los próximos 90 días. No necesitas conocer el funcionamiento técnico del modelo para utilizar el panel.
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        kpi_card(
            "Punto de decisión",
            f"{meta['umbral_decision'] * 100:.2f}%",
            "Por debajo de este porcentaje, el modelo considera que no es probable el retorno",
        )
    with c2:
        kpi_card(
            "Riesgo bajo hasta",
            f"{meta['umbral_bajo']:.2f}",
            "Puntuación de riesgo sobre 100",
        )
    with c3:
        kpi_card(
            "Riesgo alto desde",
            f"{meta['umbral_alto']:.2f}",
            "Puntuación de riesgo sobre 100",
        )

    st.markdown('<div class="section-space"></div>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="card">
            <div class="card-title">¿Cómo leer estos números?</div>
            <div style="font-size:.78rem;line-height:1.65;color:{TEXT};">
                <b>1.</b> El sistema calcula una probabilidad de que la clienta regrese durante los próximos 90 días.<br>
                <b>2.</b> Esa probabilidad se convierte en una puntuación de riesgo de 0 a 100: cuanto más alta, mayor es el riesgo de que no regrese.<br>
                <b>3.</b> Con los valores actuales, hasta <b>{meta['umbral_bajo']:.2f}</b> se muestra como <b>Bajo riesgo</b>, desde <b>{meta['umbral_alto']:.2f}</b> como <b>Alto riesgo</b> y entre ambos valores como <b>Riesgo medio</b>.<br>
                <b>4.</b> Los factores que aparecen en cada clienta ayudan a explicar qué señales del historial han pesado más en su resultado.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="section-space"></div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)

    with c1:
        st.markdown(
            '<div class="card"><div class="card-title">¿Cómo se reparten los niveles de riesgo?</div>'
            '<div class="card-caption">Permite ver cuántas clientas quedan en cada nivel en el corte actual.</div></div>',
            unsafe_allow_html=True,
        )
        fig = go.Figure(
            go.Histogram(
                x=scoring["score_riesgo"],
                nbinsx=20,
                marker_color=FUCHSIA,
                opacity=.85,
            )
        )
        fig.update_xaxes(title="Puntuación de riesgo", range=[0, 100])
        fig.update_yaxes(title="Clientas")
        chart_layout(fig, 320)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with c2:
        st.markdown(
            '<div class="card"><div class="card-title">¿Qué señales aparecen con más frecuencia?</div>'
            '<div class="card-caption">Son las principales señales que el sistema utiliza para explicar los resultados de las clientas.</div></div>',
            unsafe_allow_html=True,
        )
        factors = (
            pd.concat(
                [
                    scoring["factor_1"].rename("factor"),
                    scoring["factor_2"].rename("factor"),
                    scoring["factor_3"].rename("factor"),
                ]
            )
            .dropna()
            .astype(str)
            .value_counts()
            .head(8)
        )
        fig2 = go.Figure(
            go.Bar(
                x=factors.values,
                y=factors.index,
                orientation="h",
                marker_color=GOLD,
            )
        )
        fig2.update_xaxes(title="Veces que aparece entre las principales señales")
        chart_layout(fig2, 320)
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

    fecha_modelo = pd.to_datetime(meta.get("fecha_entrenamiento"), errors="coerce")
    fecha_texto = fecha_modelo.strftime("%d/%m/%Y") if not pd.isna(fecha_modelo) else "—"
    st.markdown(
        f"""
        <div class="note">
            <b>Transparencia:</b> el modelo ya está preparado antes de abrir el dashboard; esta pantalla no lo vuelve a entrenar.
            La última actualización registrada es del <b>{fecha_texto}</b>. Las explicaciones de las clientas proceden de las
            señales calculadas por el propio modelo, no de texto inventado por una IA.
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("Ver qué datos tiene en cuenta el sistema"):
        features = pd.DataFrame({"Dato utilizado": meta.get("feature_cols", [])})
        st.dataframe(features, hide_index=True, use_container_width=True, height=280)
        st.caption("Esta lista es la definición técnica del proyecto; se deja desplegada para quien necesite revisar la trazabilidad académica.")


# =============================================================================
# REPORTES
# =============================================================================

elif page == "Reportes":
    page_header(
        "Reportes",
        "Exporta resultados del snapshot actual para seguimiento y documentación",
    )

    base = scoring[~scoring["id_cliente_anon"].isin(st.session_state.excluidas)].copy()

    st.markdown(
        f"""
        <div class="card">
            <div class="card-title">Informe ejecutivo</div>
            <div class="card-caption">Resumen de {len(base)} clientas visibles en el snapshot actual.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)

    with c1:
        st.download_button(
            "Descargar CSV",
            base.to_csv(index=False).encode("utf-8"),
            file_name="beauty_girl_scoring.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with c2:
        buffer = io.BytesIO()
        base.to_excel(buffer, index=False, engine="xlsxwriter")
        st.download_button(
            "Descargar Excel",
            buffer.getvalue(),
            file_name="beauty_girl_scoring.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    with c3:
        pdf_buffer = io.BytesIO()
        fecha_ref = pd.to_datetime(base["fecha_referencia"].max())
        with PdfPages(pdf_buffer) as pdf:
            fig, ax = plt.subplots(figsize=(11.69, 8.27))
            ax.axis("off")
            add_pdf_logo(ax)
            ax.text(0.05, 0.90, "Beauty Girl Studio", fontsize=24, fontweight="bold", color=FUCHSIA)
            ax.text(0.05, 0.84, "Smart Data Suite · Informe ejecutivo", fontsize=15, color=TEXT)
            ax.text(0.05, 0.78, f"Corte: {fecha_ref:%d/%m/%Y}", fontsize=10, color="#666")
            items = [
                ("Clientas visibles", len(base)),
                ("Alto riesgo", int((base["banda_riesgo"] == "Alto").sum())),
                ("Retorno medio", f"{base['prob_retorno_90d'].mean() * 100:.2f}%"),
                ("Ticket medio", f"${base['ticket_medio'].mean():,.2f}"),
                ("Visitas medias", f"{base['frequency_visitas'].mean():.0f}"),
            ]
            y = 0.65
            for label, value in items:
                ax.text(0.08, y, label, fontsize=12, color="#666")
                ax.text(0.45, y, str(value), fontsize=14, fontweight="bold", color=FUCHSIA)
                y -= 0.09
            ax.text(
                0.05, 0.12,
                "Este informe resume la información visible en el panel. Las cifras se calculan con el historial disponible y el informe no cambia los datos del negocio.",
                fontsize=9, color="#777", wrap=True,
            )
            pdf.savefig(fig, bbox_inches="tight")
            plt.close(fig)

        st.download_button(
            "Exportar PDF",
            pdf_buffer.getvalue(),
            file_name="beauty_girl_informe.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

    st.markdown('<div class="section-space"></div>', unsafe_allow_html=True)
    provider_detail = base[
        [
            "codigo_display",
            "score_riesgo",
            "prob_retorno_90d",
            "banda_riesgo",
            "segmento_rfm",
            "recency_dias",
            "frequency_visitas",
            "ticket_medio",
        ]
    ].rename(
        columns={
            "codigo_display": "Cliente",
            "score_riesgo": "Score",
            "prob_retorno_90d": "Prob. retorno",
            "banda_riesgo": "Riesgo",
            "segmento_rfm": "RFM",
            "recency_dias": "Recency",
            "frequency_visitas": "Visitas",
            "ticket_medio": "Ticket",
        }
    )
    provider_detail["Cliente"] = provider_detail["Cliente"].astype(int).astype(str)
    provider_detail["Score"] = provider_detail["Score"].map(lambda x: f"{x:.2f}" if pd.notna(x) else "—")
    provider_detail["Prob. retorno"] = provider_detail["Prob. retorno"].map(lambda x: f"{x * 100:.2f}%" if pd.notna(x) else "—")
    provider_detail["Ticket"] = provider_detail["Ticket"].map(lambda x: f"${x:,.2f}" if pd.notna(x) else "—")
    provider_detail["Visitas"] = provider_detail["Visitas"].map(lambda x: f"{x:.2f}" if pd.notna(x) else "—")
    provider_detail["Recency"] = provider_detail["Recency"].map(lambda x: f"{x:.0f} d" if pd.notna(x) else "—")
    st.dataframe(provider_detail, hide_index=True, use_container_width=True)


# =============================================================================
# CONFIGURACIÓN
# =============================================================================

elif page == "Configuración":
    page_header(
        "Configuración",
        "Gestiona las clientas que quieres ocultar del panel y actualiza la información mostrada",
    )

    c1, c2 = st.columns([1.3, .7])
    with c1:
        st.markdown(
            '<div class="card"><div class="card-title">Clientas excluidas del panel</div>'
            '<div class="card-caption">Puedes ocultar temporalmente una clienta del panel cuando ya no quieras tenerla en el seguimiento.</div></div>',
            unsafe_allow_html=True,
        )
        if not st.session_state.excluidas:
            st.info("No hay clientas excluidas en esta sesión.")
        else:
            rows = []
            for cid, motivo in st.session_state.excluidas.items():
                match = scoring[scoring["id_cliente_anon"] == cid]
                code = int(match["codigo_display"].iloc[0]) if not match.empty else "—"
                rows.append({"Cliente": code, "Motivo": motivo, "Seleccionar": False})

            exclusion_editor = st.data_editor(
                pd.DataFrame(rows),
                hide_index=True,
                use_container_width=True,
                disabled=["Cliente", "Motivo"],
                column_config={
                    "Seleccionar": st.column_config.CheckboxColumn(
                        "Seleccionar",
                        help="Marca las clientas cuya exclusión quieres revertir.",
                    ),
                    "Cliente": st.column_config.TextColumn("Cliente"),
                    "Motivo": st.column_config.TextColumn("Motivo"),
                },
                key="exclusion_editor",
            )

            selected_codes = exclusion_editor.loc[
                exclusion_editor["Seleccionar"] == True, "Cliente"
            ].tolist()

            b1, b2 = st.columns(2)
            with b1:
                if st.button(
                    "Revertir seleccionadas",
                    use_container_width=True,
                    disabled=not selected_codes,
                ):
                    code_to_id = {
                        int(row["codigo_display"]): row["id_cliente_anon"]
                        for _, row in scoring.iterrows()
                    }
                    for code in selected_codes:
                        cid = code_to_id.get(int(code))
                        if cid in st.session_state.excluidas:
                            del st.session_state.excluidas[cid]
                    st.success("Se han vuelto a mostrar las clientas seleccionadas.")
                    st.rerun()

            with b2:
                if st.button("Revertir todas las exclusiones", use_container_width=True):
                    st.session_state.excluidas = {}
                    st.success("Se han vuelto a mostrar todas las clientas.")
                    st.rerun()

    with c2:
        st.markdown(
            """<div class="card">
                <div class="card-title">Actualizar información</div>
                <div class="card-caption">Si el equipo ha actualizado los datos del negocio fuera del dashboard, este botón vuelve a cargarlos para que el panel muestre la información más reciente.</div>
            </div>""",
            unsafe_allow_html=True,
        )
        if st.button("Actualizar datos del panel", use_container_width=True):
            st.cache_data.clear()
            st.success("La información del panel se ha actualizado.")
            st.rerun()

    st.markdown('<div class="section-space"></div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="note"><b>Sobre las exclusiones:</b> ocultar una clienta solo cambia lo que ves durante esta sesión. Los datos originales del negocio y el cálculo del riesgo no se modifican.</div>',
        unsafe_allow_html=True,
    )
