"""
Дашборд продаж NIKE — Streamlit-приложение.
Запуск: streamlit run app.py
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import logging

from src.data_loader import (
    load_data, get_sorted_periods, filter_data,
    PRODUCT_TRANSLATIONS, REGION_TRANSLATIONS,
    PRODUCT_RU_TO_EN, REGION_RU_TO_EN,
    QUARTER_LABELS_RU, LABELS_TO_PERIOD
)
from src.data_validation import validate_dataset
from src.metrics import aggregate_selected_revenue, get_kpi_values
from src.seasonality import (
    calculate_seasonality, get_seasonal_summary, get_best_quarter_text
)
from src.forecasting import (
    build_all_forecasts, get_aggregated_forecast, save_diagnostics
)
from src.charts import (
    plot_revenue_forecast, plot_share_forecast,
    plot_seasonality_bar, plot_heatmap, plot_bubble_chart
)

# ── Конфигурация страницы ─────────────────────────────────────────────
st.set_page_config(
    page_title="NIKE Sales Dashboard",
    page_icon="✔",
    layout="wide",
    initial_sidebar_state="collapsed",
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Стили ─────────────────────────────────────────────────────────────
STYLES = """
<style>
/* ── Базовые переменные ── */
:root {
    --nike-black:   #111111;
    --nike-white:   #FFFFFF;
    --nike-red:     #FA5400;
    --card-bg:      #1A1A1A;
    --card-border:  #2A2A2A;
    --muted:        #888888;
    --text-primary: #F0F0F0;
    --text-secondary:#AAAAAA;
    --positive:     #3DD68C;
    --negative:     #FF4B4B;
    --radius:       10px;
}

/* ── Фон приложения ── */
.stApp, .main, section.main > div {
    background-color: var(--nike-black) !important;
}
.stApp header { display: none !important; }

/* ── Убираем стандартные отступы ── */
.block-container {
    padding: 0 2rem 2rem 2rem !important;
    max-width: 1400px;
}

/* ── Шапка ── */
.nike-header {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 28px 0 20px 0;
    border-bottom: 1px solid var(--card-border);
    margin-bottom: 24px;
}
.nike-logo {
    font-size: 36px;
    font-weight: 900;
    letter-spacing: -1px;
    color: var(--nike-white);
    font-style: italic;
}
.nike-logo span { color: var(--nike-red); }
.nike-subtitle {
    font-size: 13px;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-top: 2px;
}
.header-badge {
    margin-left: auto;
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: 6px;
    padding: 6px 14px;
    font-size: 12px;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 1px;
}

/* ── KPI-карточки ── */
.kpi-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    margin-bottom: 24px;
}
.kpi-card {
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: var(--radius);
    padding: 20px 22px;
    position: relative;
    overflow: hidden;
}
.kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: 3px; height: 100%;
    background: var(--nike-red);
}
.kpi-label {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: var(--muted);
    margin-bottom: 8px;
}
.kpi-value {
    font-size: 28px;
    font-weight: 700;
    color: var(--text-primary);
    line-height: 1;
    margin-bottom: 6px;
}
.kpi-delta {
    font-size: 13px;
    font-weight: 600;
}
.kpi-delta.pos { color: var(--positive); }
.kpi-delta.neg { color: var(--negative); }
.kpi-delta.neu { color: var(--muted); }

/* ── Секционные заголовки ── */
.section-title {
    font-size: 13px;
    text-transform: uppercase;
    letter-spacing: 2px;
    color: var(--muted);
    margin: 28px 0 14px 0;
    display: flex;
    align-items: center;
    gap: 10px;
}
.section-title::after {
    content: '';
    flex: 1;
    height: 1px;
    background: var(--card-border);
}

/* ── Фильтры ── */
.filter-bar {
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: var(--radius);
    padding: 16px 20px;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
}
.filter-label {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: var(--muted);
    margin-right: 8px;
}

/* ── Streamlit виджеты — тёмная тема ── */
div[data-testid="stMultiSelect"] > div > div,
div[data-testid="stSelectSlider"] > div > div,
div[data-testid="stSelectbox"] > div > div {
    background-color: #222222 !important;
    border: 1px solid var(--card-border) !important;
    color: var(--text-primary) !important;
    border-radius: 6px !important;
}
div[data-testid="stMultiSelect"] label,
div[data-testid="stSelectbox"] label,
div[data-testid="stSlider"] label {
    color: var(--text-secondary) !important;
    font-size: 12px !important;
    text-transform: uppercase !important;
    letter-spacing: 1px !important;
}
/* Тэги мультиселекта */
span[data-baseweb="tag"] {
    background-color: var(--nike-red) !important;
    border-radius: 4px !important;
}
/* Слайдер */
div[data-testid="stSlider"] > div > div > div > div {
    background-color: var(--nike-red) !important;
}

/* ── Вкладки ── */
div[data-testid="stTabs"] > div > div > button {
    color: var(--muted) !important;
    font-size: 12px !important;
    text-transform: uppercase !important;
    letter-spacing: 1.5px !important;
    border-radius: 0 !important;
    border-bottom: 2px solid transparent !important;
    padding-bottom: 10px !important;
}
div[data-testid="stTabs"] > div > div > button[aria-selected="true"] {
    color: var(--text-primary) !important;
    border-bottom-color: var(--nike-red) !important;
    background: transparent !important;
}
div[data-testid="stTabPanel"] {
    background: transparent !important;
    padding-top: 20px !important;
}

/* ── Блок с графиком ── */
.chart-card {
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: var(--radius);
    padding: 20px;
    margin-bottom: 16px;
}
.chart-title {
    font-size: 14px;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 4px;
}
.chart-desc {
    font-size: 12px;
    color: var(--muted);
    margin-bottom: 16px;
}

/* ── Инсайт-блок ── */
.insight-box {
    background: linear-gradient(135deg, #1E1E1E 0%, #242424 100%);
    border: 1px solid var(--card-border);
    border-left: 3px solid var(--nike-red);
    border-radius: var(--radius);
    padding: 16px 20px;
    margin-top: 12px;
    font-size: 13px;
    color: var(--text-secondary);
    line-height: 1.6;
}
.insight-box strong { color: var(--text-primary); }

/* ── Полосы прогресса ── */
.rank-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 0;
    border-bottom: 1px solid var(--card-border);
}
.rank-num {
    font-size: 11px;
    color: var(--muted);
    width: 20px;
    text-align: right;
    font-weight: 600;
}
.rank-name {
    font-size: 13px;
    color: var(--text-primary);
    width: 120px;
}
.rank-bar-wrap {
    flex: 1;
    background: #2A2A2A;
    border-radius: 3px;
    height: 6px;
    overflow: hidden;
}
.rank-bar {
    height: 100%;
    background: var(--nike-red);
    border-radius: 3px;
    transition: width 0.4s ease;
}
.rank-val {
    font-size: 13px;
    font-weight: 700;
    color: var(--text-primary);
    width: 70px;
    text-align: right;
}

/* ── Скрываем лишнее в Streamlit ── */
#MainMenu, footer, .stDeployButton { display: none !important; }
div[data-testid="stStatusWidget"] { display: none !important; }

/* ── Spinner ── */
div[data-testid="stSpinner"] { color: var(--nike-red) !important; }
</style>
"""

st.markdown(STYLES, unsafe_allow_html=True)

# ── Утилиты цвета для Plotly ──────────────────────────────────────────
PLOT_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, -apple-system, sans-serif", color="#AAAAAA", size=12),
    margin=dict(l=10, r=10, t=30, b=10),
    xaxis=dict(
        gridcolor="#1E1E1E", linecolor="#2A2A2A",
        tickfont=dict(size=11, color="#888888"),
    ),
    yaxis=dict(
        gridcolor="#1E1E1E", linecolor="#2A2A2A",
        tickfont=dict(size=11, color="#888888"),
        zeroline=False,
    ),
    legend=dict(
        bgcolor="rgba(0,0,0,0)", bordercolor="rgba(0,0,0,0)",
        font=dict(size=11, color="#AAAAAA"),
    ),
    hoverlabel=dict(
        bgcolor="#1A1A1A", bordercolor="#333333",
        font=dict(color="#F0F0F0", size=12),
    ),
)

def apply_dark_layout(fig, title=""):
    fig.update_layout(**PLOT_LAYOUT, title=dict(
        text=title, font=dict(size=14, color="#F0F0F0"), x=0, y=0.98
    ))
    return fig


# ── Загрузка данных ───────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def load_all():
    df = load_data()
    try:
        validate_dataset(df)
    except Exception as e:
        logger.warning(f"Validation warning: {e}")
    periods = get_sorted_periods(df)
    try:
        result = build_all_forecasts(df)
        # build_all_forecasts может вернуть (forecast_df, diag_df) или просто df
        forecasts = result[0] if isinstance(result, tuple) else result
    except Exception as e:
        logger.warning(f"Forecasting failed: {e}")
        forecasts = None
    return df, periods, forecasts


# ══════════════════════════════════════════════════════════════════════
# ШАПКА
# ══════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="nike-header">
  <div>
    <div class="nike-logo">NIKE<span>.</span></div>
    <div class="nike-subtitle">Sales Intelligence Dashboard</div>
  </div>
  <div class="header-badge">FY2023 – Q3 FY2026</div>
</div>
""", unsafe_allow_html=True)


# ── Загрузка ──────────────────────────────────────────────────────────
with st.spinner("Загружаем данные…"):
    df_all, all_periods, all_forecasts = load_all()

ALL_PRODUCTS_RU = sorted(df_all["product"].map(PRODUCT_TRANSLATIONS).dropna().unique())
ALL_REGIONS_RU  = sorted(df_all["region"].map(REGION_TRANSLATIONS).dropna().unique())
QUARTER_OPTS    = [QUARTER_LABELS_RU[p] for p in all_periods if p in QUARTER_LABELS_RU]


# ══════════════════════════════════════════════════════════════════════
# ФИЛЬТРЫ
# ══════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-title">Фильтры</div>', unsafe_allow_html=True)

col_p, col_r, col_q = st.columns([2, 2, 3])

with col_p:
    sel_products_ru = st.multiselect(
        "Продукт", ALL_PRODUCTS_RU, default=ALL_PRODUCTS_RU, key="prod"
    )
with col_r:
    sel_regions_ru = st.multiselect(
        "Регион", ALL_REGIONS_RU, default=ALL_REGIONS_RU, key="reg"
    )
with col_q:
    q_range = st.select_slider(
        "Период", options=QUARTER_OPTS,
        value=(QUARTER_OPTS[0], QUARTER_OPTS[-1]), key="qrange"
    )

# Применяем фильтры
sel_products = [PRODUCT_RU_TO_EN.get(p, p) for p in (sel_products_ru or ALL_PRODUCTS_RU)]
sel_regions  = [REGION_RU_TO_EN.get(r, r)  for r in (sel_regions_ru  or ALL_REGIONS_RU)]

start_p = LABELS_TO_PERIOD.get(q_range[0], all_periods[0])
end_p   = LABELS_TO_PERIOD.get(q_range[1], all_periods[-1])

try:
    i0 = all_periods.index(start_p)
    i1 = all_periods.index(end_p)
    sel_periods = all_periods[i0:i1+1]
except ValueError:
    sel_periods = all_periods

df_filtered = filter_data(df_all, sel_products, sel_regions, sel_periods)


# ══════════════════════════════════════════════════════════════════════
# KPI-КАРТОЧКИ
# ══════════════════════════════════════════════════════════════════════
kpi = get_kpi_values(df_all, df_filtered, sel_products, sel_regions, sel_periods)

def delta_class(v):
    if v is None: return "neu"
    return "pos" if v > 0 else ("neg" if v < 0 else "neu")

def fmt_delta(v):
    if v is None: return "—"
    sign = "▲" if v > 0 else "▼"
    return f"{sign} {abs(v):.1f}%"

def fmt_val(v, suffix=""):
    if v is None: return "—"
    if v >= 1000: return f"${v/1000:.1f}B{suffix}"
    return f"${v:.0f}M{suffix}"

kpi_html = f"""
<div class="kpi-grid">
  <div class="kpi-card">
    <div class="kpi-label">Выручка (период)</div>
    <div class="kpi-value">{fmt_val(kpi.get('total_rev'))}</div>
    <div class="kpi-delta {delta_class(kpi.get('rev_yoy'))}">{fmt_delta(kpi.get('rev_yoy'))} г/г</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">Последний квартал</div>
    <div class="kpi-value">{fmt_val(kpi.get('last_q_rev'))}</div>
    <div class="kpi-delta {delta_class(kpi.get('last_q_yoy'))}">{fmt_delta(kpi.get('last_q_yoy'))} г/г</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">Лучший регион</div>
    <div class="kpi-value" style="font-size:20px;margin-top:4px">{kpi.get('top_region', '—')}</div>
    <div class="kpi-delta neu">{fmt_val(kpi.get('top_region_rev'))}</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">Лучший продукт</div>
    <div class="kpi-value" style="font-size:20px;margin-top:4px">{kpi.get('top_product', '—')}</div>
    <div class="kpi-delta neu">{fmt_val(kpi.get('top_product_rev'))}</div>
  </div>
</div>
"""
st.markdown(kpi_html, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════
# ВКЛАДКИ
# ══════════════════════════════════════════════════════════════════════
tab1, tab2, tab3 = st.tabs(["📈  Динамика & Прогноз", "🗺  Продукты & Регионы", "🏆  Рейтинги"])


# ──────────────────────────────────────────────────────────────────────
# ВКЛАДКА 1 — ДИНАМИКА
# ──────────────────────────────────────────────────────────────────────
with tab1:
    col_l, col_r = st.columns([3, 2])

    with col_l:
        st.markdown('<div class="chart-title">Выручка по кварталам</div>'
                    '<div class="chart-desc">Факт + прогноз на 4 квартала вперёд</div>',
                    unsafe_allow_html=True)

        try:
            if all_forecasts is None:
                raise ValueError("Прогнозы не загружены")
            # get_aggregated_forecast может принимать разные сигнатуры
            try:
                result = get_aggregated_forecast(
                    df_all, all_forecasts, sel_products, sel_regions, sel_periods
                )
            except TypeError:
                result = get_aggregated_forecast(
                    all_forecasts, sel_products, sel_regions
                )
            # результат может быть (ts, fc) или единый df
            if isinstance(result, tuple):
                agg_ts, agg_fc = result
            else:
                agg_ts, agg_fc = result, None
            fig_rev = plot_revenue_forecast(agg_ts, agg_fc)
            apply_dark_layout(fig_rev)
            fig_rev.update_traces(
                selector=dict(mode="lines+markers"),
                line=dict(color="#FA5400", width=2),
                marker=dict(color="#FA5400", size=5),
            )
            st.plotly_chart(fig_rev, use_container_width=True, config={"displayModeBar": False})
        except Exception as e:
            logger.warning(f"Forecast chart error: {e}")
            # Fallback: простой линейный график без прогноза
            try:
                import plotly.graph_objects as go
                ts = (df_filtered.groupby("fiscal_period")["revenue_usd_mn"]
                      .sum().reset_index().sort_values("fiscal_period"))
                labels = [QUARTER_LABELS_RU.get(p, p) for p in ts["fiscal_period"]]
                fig_fb = go.Figure()
                fig_fb.add_scatter(
                    x=labels, y=ts["revenue_usd_mn"],
                    mode="lines+markers",
                    line=dict(color="#FA5400", width=2),
                    marker=dict(color="#FA5400", size=6),
                    name="Факт",
                    hovertemplate="<b>%{x}</b><br>$%{y:,.0f}M<extra></extra>",
                )
                apply_dark_layout(fig_fb)
                st.plotly_chart(fig_fb, use_container_width=True, config={"displayModeBar": False})
            except Exception as e2:
                logger.warning(f"Fallback chart error: {e2}")
                st.info("График динамики недоступен.")

    with col_r:
        st.markdown('<div class="chart-title">Сезонность</div>'
                    '<div class="chart-desc">Средний квартальный индекс</div>',
                    unsafe_allow_html=True)

        try:
            seas = calculate_seasonality(df_filtered)
            fig_seas = plot_seasonality_bar(seas)
            apply_dark_layout(fig_seas)
            fig_seas.update_traces(marker_color="#FA5400", opacity=0.85)
            st.plotly_chart(fig_seas, use_container_width=True, config={"displayModeBar": False})

            best_q = get_best_quarter_text(seas)
            seas_sum = get_seasonal_summary(seas)
            st.markdown(
                f'<div class="insight-box">'
                f'<strong>Пик продаж:</strong> {best_q}<br>'
                f'{seas_sum}'
                f'</div>',
                unsafe_allow_html=True
            )
        except Exception as e:
            logger.warning(f"Seasonality chart error: {e}")
            st.info("Данные сезонности недоступны.")


# ──────────────────────────────────────────────────────────────────────
# ВКЛАДКА 2 — ТЕПЛОВАЯ КАРТА
# ──────────────────────────────────────────────────────────────────────
with tab2:
    col_l2, col_r2 = st.columns([3, 2])

    with col_l2:
        st.markdown('<div class="chart-title">Тепловая карта: продукт × регион</div>'
                    '<div class="chart-desc">Суммарная выручка в $млн за выбранный период</div>',
                    unsafe_allow_html=True)
        try:
            fig_heat = plot_heatmap(df_filtered)
            apply_dark_layout(fig_heat)
            # Меняем цветовую шкалу на красную
            fig_heat.update_traces(
                colorscale=[[0, "#1A1A1A"], [0.5, "#7A2A00"], [1, "#FA5400"]],
            )
            st.plotly_chart(fig_heat, use_container_width=True, config={"displayModeBar": False})
        except Exception as e:
            logger.warning(f"Heatmap error: {e}")
            st.info("Тепловая карта недоступна.")

    with col_r2:
        st.markdown('<div class="chart-title">Структура выручки</div>'
                    '<div class="chart-desc">Доля продуктов по регионам</div>',
                    unsafe_allow_html=True)
        try:
            fig_share = plot_share_forecast(df_filtered)
            apply_dark_layout(fig_share)
            st.plotly_chart(fig_share, use_container_width=True, config={"displayModeBar": False})
        except Exception as e:
            logger.warning(f"Share chart error: {e}")
            # Fallback: простая pie-диаграмма
            try:
                prod_data = (
                    df_filtered.groupby("product")["revenue_usd_mn"]
                    .sum().reset_index()
                    .rename(columns={"product": "p", "revenue_usd_mn": "rev"})
                )
                prod_data["p"] = prod_data["p"].map(PRODUCT_TRANSLATIONS).fillna(prod_data["p"])
                fig_pie = go.Figure(go.Pie(
                    labels=prod_data["p"], values=prod_data["rev"],
                    hole=0.55,
                    marker=dict(colors=["#FA5400", "#C84300", "#8B2F00", "#5A1F00"]),
                    textfont=dict(color="#F0F0F0", size=11),
                ))
                apply_dark_layout(fig_pie)
                st.plotly_chart(fig_pie, use_container_width=True, config={"displayModeBar": False})
            except Exception:
                st.info("Данные для диаграммы недоступны.")


# ──────────────────────────────────────────────────────────────────────
# ВКЛАДКА 3 — РЕЙТИНГИ
# ──────────────────────────────────────────────────────────────────────
with tab3:
    col_a, col_b = st.columns(2)

    def render_ranking(df, group_col, label_map, title, desc):
        ranked = (
            df.groupby(group_col)["revenue_usd_mn"]
            .sum()
            .reset_index()
            .sort_values("revenue_usd_mn", ascending=False)
        )
        ranked["label"] = ranked[group_col].map(label_map).fillna(ranked[group_col])
        total = ranked["revenue_usd_mn"].sum() or 1
        max_val = ranked["revenue_usd_mn"].max() or 1

        rows = ""
        for i, row in enumerate(ranked.itertuples(), 1):
            pct_bar = row.revenue_usd_mn / max_val * 100
            val_str = f"${row.revenue_usd_mn/1000:.2f}B" if row.revenue_usd_mn >= 1000 else f"${row.revenue_usd_mn:.0f}M"
            rows += f"""
            <div class="rank-item">
              <div class="rank-num">{i:02d}</div>
              <div class="rank-name">{row.label}</div>
              <div class="rank-bar-wrap">
                <div class="rank-bar" style="width:{pct_bar:.1f}%"></div>
              </div>
              <div class="rank-val">{val_str}</div>
            </div>"""

        st.markdown(
            f'<div class="chart-card">'
            f'<div class="chart-title">{title}</div>'
            f'<div class="chart-desc">{desc}</div>'
            f'{rows}'
            f'</div>',
            unsafe_allow_html=True
        )

    with col_a:
        render_ranking(
            df_filtered, "region",
            {v: k_ru for k_ru, v in REGION_RU_TO_EN.items()},
            "Регионы по выручке",
            "Суммарная за выбранный период"
        )

    with col_b:
        render_ranking(
            df_filtered, "product",
            {v: k_ru for k_ru, v in PRODUCT_RU_TO_EN.items()},
            "Продукты по выручке",
            "Суммарная за выбранный период"
        )

    # Дополнительный graf — bubble chart
    st.markdown('<div class="section-title">Детальный анализ</div>', unsafe_allow_html=True)
    try:
        fig_bub = plot_bubble_chart(df_filtered)
        apply_dark_layout(fig_bub)
        st.plotly_chart(fig_bub, use_container_width=True, config={"displayModeBar": False})
    except Exception as e:
        logger.warning(f"Bubble chart error: {e}")

        # Fallback: bar chart регионы × продукты
        try:
            pivot = df_filtered.groupby(["region", "product"])["revenue_usd_mn"].sum().reset_index()
            pivot["region_ru"] = pivot["region"].map(REGION_TRANSLATIONS).fillna(pivot["region"])
            pivot["product_ru"] = pivot["product"].map(PRODUCT_TRANSLATIONS).fillna(pivot["product"])
            colors = ["#FA5400", "#C84300", "#8B2F00", "#5A1F00"]
            fig_bar = go.Figure()
            for i, prod in enumerate(pivot["product_ru"].unique()):
                sub = pivot[pivot["product_ru"] == prod]
                fig_bar.add_bar(
                    name=prod, x=sub["region_ru"], y=sub["revenue_usd_mn"],
                    marker_color=colors[i % len(colors)],
                )
            fig_bar.update_layout(barmode="group", **PLOT_LAYOUT)
            st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar": False})
        except Exception:
            st.info("Детальный анализ недоступен.")


# ── Подвал ────────────────────────────────────────────────────────────
st.markdown("""
<div style="margin-top:32px;padding-top:20px;border-top:1px solid #2A2A2A;
            display:flex;justify-content:space-between;align-items:center;">
  <span style="color:#555;font-size:11px;letter-spacing:1px;text-transform:uppercase">
    NIKE, Inc. · Quarterly Sales Data · FY2023–Q3 FY2026
  </span>
  <span style="color:#555;font-size:11px">
    Источник: NIKE Press Releases & 10-K Filings
  </span>
</div>
""", unsafe_allow_html=True)
