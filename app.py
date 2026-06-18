"""
Дашборд продаж NIKE — Streamlit-приложение.

Запуск: streamlit run app.py

Анализирует квартальную выручку NIKE Brand по продуктам и регионам
за период Q1 FY2023 — Q1 FY2026.

Три аналитических блока:
  1. Динамика продаж, сезонность и прогноз
  2. Карта продаж по продуктам и регионам
  3. Приоритетные направления продаж
"""

import sys
import os
# Добавляем корень проекта в путь для импорта модулей
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import logging

# Импорт модулей проекта
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

# -----------------------------------------------------------------------
# Конфигурация страницы — должна быть первой командой Streamlit
# -----------------------------------------------------------------------
st.set_page_config(
    page_title="Дашборд продаж NIKE",
    page_icon="👟",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------
# Кастомные стили — профессиональный BI-вид
# -----------------------------------------------------------------------
st.markdown("""
<style>
    /* Уменьшаем отступы */
    .block-container { padding-top: 1rem; padding-bottom: 1rem; }
    /* KPI-карточки */
    .kpi-card {
        background: white;
        border-radius: 8px;
        padding: 16px 20px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        text-align: center;
    }
    .kpi-label { font-size: 12px; color: #5f6368; margin-bottom: 4px; font-weight: 500; }
    .kpi-value { font-size: 22px; font-weight: 700; color: #202124; }
    .kpi-delta-pos { font-size: 13px; color: #34a853; }
    .kpi-delta-neg { font-size: 13px; color: #ea4335; }
    .kpi-delta-neu { font-size: 13px; color: #5f6368; }
    /* Заголовки блоков */
    .block-header {
        font-size: 15px;
        font-weight: 600;
        color: #202124;
        border-left: 4px solid #1a73e8;
        padding-left: 10px;
        margin-bottom: 8px;
    }
    /* Предупреждения */
    .warn-box {
        background: #fff3cd;
        border: 1px solid #ffc107;
        border-radius: 6px;
        padding: 10px 14px;
        font-size: 13px;
    }
</style>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------
# Загрузка и кэширование данных
# -----------------------------------------------------------------------
@st.cache_data(ttl=3600)
def get_main_data() -> pd.DataFrame:
    """Загружает и кэширует основной датасет."""
    return load_data()


@st.cache_data(ttl=3600)
def get_all_forecasts_cached(end_period: str) -> tuple:
    """Строит и кэширует прогнозы для заданного конечного периода."""
    df = get_main_data()
    # Для обучения используем все данные до выбранного периода
    return build_all_forecasts(df, end_period)


# -----------------------------------------------------------------------
# Загрузка данных с обработкой ошибок
# -----------------------------------------------------------------------
try:
    df_full = get_main_data()
except Exception as e:
    st.error(f"❌ Не удалось загрузить данные: {e}")
    st.stop()

# Проверка качества данных при первом запуске
if 'validated' not in st.session_state:
    ok, msgs = validate_dataset(df_full)
    if not ok:
        for msg in msgs:
            st.warning(f"⚠️ {msg}")
    st.session_state['validated'] = True

# -----------------------------------------------------------------------
# Заголовок дашборда
# -----------------------------------------------------------------------
col_logo, col_title = st.columns([1, 11])
with col_title:
    st.markdown("## Дашборд продаж NIKE")
    st.markdown(
        "<p style='color:#5f6368; margin-top:-12px; font-size:14px;'>"
        "Когда, какой продукт и в каком регионе продаётся лучше? &nbsp;|&nbsp; "
        "Анализ квартальной выручки NIKE Brand по продуктам и регионам, "
        "1 кв. 2023 ф. г. — 1 кв. 2026 ф. г."
        "</p>",
        unsafe_allow_html=True
    )

st.divider()

# -----------------------------------------------------------------------
# Блок фильтров
# -----------------------------------------------------------------------
all_periods_ru = get_sorted_periods(df_full)
all_products_ru = list(PRODUCT_TRANSLATIONS.values())
all_regions_ru = list(REGION_TRANSLATIONS.values())

col_f1, col_f2, col_f3 = st.columns([3, 3, 4])

with col_f1:
    st.markdown("**📅 Период**")
    fc1, fc2 = st.columns(2)
    with fc1:
        start_period = st.selectbox(
            "С квартала",
            options=all_periods_ru,
            index=0,
            label_visibility="collapsed",
            key="start_period"
        )
    with fc2:
        # Конечный квартал не может быть раньше начального
        start_idx = all_periods_ru.index(start_period)
        end_options = all_periods_ru[start_idx:]
        end_period = st.selectbox(
            "По квартал",
            options=end_options,
            index=len(end_options) - 1,
            label_visibility="collapsed",
            key="end_period"
        )

with col_f2:
    st.markdown("**👟 Продукт**")
    selected_products_ru = st.multiselect(
        "Продукты",
        options=all_products_ru,
        default=all_products_ru,
        label_visibility="collapsed",
        key="products"
    )

with col_f3:
    st.markdown("**🌍 Регион**")
    selected_regions_ru = st.multiselect(
        "Регионы",
        options=all_regions_ru,
        default=all_regions_ru,
        label_visibility="collapsed",
        key="regions"
    )

# -----------------------------------------------------------------------
# Проверка наличия выбора
# -----------------------------------------------------------------------
if not selected_products_ru:
    st.warning("⚠️ Выберите хотя бы один продукт.")
    st.stop()

if not selected_regions_ru:
    st.warning("⚠️ Выберите хотя бы один регион.")
    st.stop()

# -----------------------------------------------------------------------
# Фильтрация данных
# -----------------------------------------------------------------------
df_filtered = filter_data(
    df_full, start_period, end_period,
    selected_products_ru, selected_regions_ru
)

if df_filtered.empty:
    st.warning("⚠️ По выбранным параметрам нет данных.")
    st.stop()

# -----------------------------------------------------------------------
# Технические коды для прогнозирования
# -----------------------------------------------------------------------
products_en = [PRODUCT_RU_TO_EN.get(p, p) for p in selected_products_ru]
regions_en  = [REGION_RU_TO_EN.get(r, r) for r in selected_regions_ru]
end_period_code = LABELS_TO_PERIOD.get(end_period, end_period)
all_products_en = list(PRODUCT_RU_TO_EN.values())
all_regions_en  = list(REGION_RU_TO_EN.values())

# -----------------------------------------------------------------------
# Построение прогнозов (кэшируется по конечному периоду)
# -----------------------------------------------------------------------
with st.spinner("Рассчитываем прогнозы..."):
    forecast_df, diag_df = get_all_forecasts_cached(end_period_code)

# Метод прогноза (для подписей)
if not diag_df.empty:
    dominant_method = diag_df['forecast_method'].mode().iloc[0]
else:
    dominant_method = "Holt-Winters"

# -----------------------------------------------------------------------
# Агрегируем данные для графиков и KPI
# -----------------------------------------------------------------------
# Агрегированный датасет для выбранного среза (факт)
agg_fact = aggregate_selected_revenue(df_filtered, df_full)

# Агрегированный датасет с прогнозами (факт + прогноз)
if not forecast_df.empty:
    agg_with_forecast = get_aggregated_forecast(
        forecast_df, products_en, regions_en, all_products_en, all_regions_en
    )
else:
    agg_with_forecast = pd.DataFrame()

# KPI-показатели
kpi = get_kpi_values(df_filtered, df_full)

# Сезонность
seasonal_summary = get_seasonal_summary(df_filtered, df_full)

# -----------------------------------------------------------------------
# KPI-карточки
# -----------------------------------------------------------------------
st.markdown("---")
kc1, kc2, kc3, kc4 = st.columns(4)

def fmt_revenue(v):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "н/д"
    return f"${v:,.0f} млн"

def fmt_pct(v, sign=True):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "н/д"
    prefix = "+" if sign and v > 0 else ""
    return f"{prefix}{v:.1f}%"

with kc1:
    rev = kpi.get('revenue')
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">💰 Выручка (последний квартал)</div>
        <div class="kpi-value">{fmt_revenue(rev)}</div>
        <div class="kpi-delta-neu">выбранный срез</div>
    </div>
    """, unsafe_allow_html=True)

with kc2:
    yoy = kpi.get('yoy_pct')
    delta_class = "kpi-delta-pos" if yoy and yoy > 0 else ("kpi-delta-neg" if yoy and yoy < 0 else "kpi-delta-neu")
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">📈 Рост год к году</div>
        <div class="kpi-value">{fmt_pct(yoy)}</div>
        <div class="{delta_class}">vs аналогичный квартал год назад</div>
    </div>
    """, unsafe_allow_html=True)

with kc3:
    share = kpi.get('share_pct')
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">🥧 Доля</div>
        <div class="kpi-value">{fmt_pct(share, sign=False)}</div>
        <div class="kpi-delta-neu">в анализируемой выручке NIKE Brand</div>
    </div>
    """, unsafe_allow_html=True)

with kc4:
    bq = kpi.get('best_quarter')
    bq_avg = kpi.get('best_quarter_avg')
    bq_label = f"{bq} кв. — {fmt_revenue(bq_avg)} в среднем" if bq else "н/д"
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">⭐ Лучший квартал</div>
        <div class="kpi-value" style="font-size:18px;">{bq_label}</div>
        <div class="kpi-delta-neu">по средней исторической выручке</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════
# БЛОК 1: ДИНАМИКА ПРОДАЖ, СЕЗОННОСТЬ И ПРОГНОЗ
# ═══════════════════════════════════════════════════════════════════════
st.markdown('<div class="block-header">Блок 1 — Динамика продаж, сезонность и прогноз</div>',
            unsafe_allow_html=True)

b1_col1, b1_col2 = st.columns([6, 4])

with b1_col1:
    # Прогноз выручки
    if not agg_with_forecast.empty:
        fig_rev = plot_revenue_forecast(agg_with_forecast, dominant_method)
        st.plotly_chart(fig_rev, use_container_width=True, config={'displayModeBar': False})
    else:
        st.info("Прогноз недоступен — недостаточно данных.")

    # Прогноз доли
    if not agg_with_forecast.empty:
        fig_share = plot_share_forecast(agg_with_forecast, dominant_method)
        st.plotly_chart(fig_share, use_container_width=True, config={'displayModeBar': False})

with b1_col2:
    # Сезонность — столбчатая диаграмма
    if not seasonal_summary.empty:
        fig_seas = plot_seasonality_bar(seasonal_summary)
        st.plotly_chart(fig_seas, use_container_width=True, config={'displayModeBar': False})

    # Таблица сезонности
    if not seasonal_summary.empty:
        st.markdown("**Сезонность по кварталам**")
        seas_display = seasonal_summary[[
            'quarter_label', 'avg_revenue_usd_mn', 'seasonal_index',
            'best_product_ru', 'best_region_ru'
        ]].copy()
        seas_display.columns = [
            'Квартал', 'Средняя выручка, млн $', 'Сезонный индекс',
            'Лучший продукт', 'Лучший регион'
        ]
        seas_display['Средняя выручка, млн $'] = seas_display['Средняя выручка, млн $'].apply(
            lambda x: f"${x:,.0f}"
        )
        seas_display['Сезонный индекс'] = seas_display['Сезонный индекс'].apply(
            lambda x: f"{x:.2f}"
        )
        # Выделяем лучший квартал
        def highlight_best(row):
            q_idx = seas_display['Квартал'].tolist().index(row['Квартал'])
            if seasonal_summary.iloc[q_idx]['is_best']:
                return ['background-color: #e8f0fe'] * len(row)
            return [''] * len(row)

        st.dataframe(
            seas_display,
            use_container_width=True,
            hide_index=True,
            height=180,
        )

    # Автоматический вывод
    if not seasonal_summary.empty:
        insight_text = get_best_quarter_text(seasonal_summary)
        st.info(insight_text)

    # Предупреждение если мало данных для обучения
    n_periods = df_filtered['fiscal_period'].nunique()
    if n_periods < 8:
        st.warning(
            f"⚠️ Для обучения доступно {n_periods} кварталов (< 8). "
            "Используется резервный сезонный наивный метод."
        )

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════
# БЛОКИ 2 и 3: КАРТА ПРОДАЖ + ПРИОРИТЕТНЫЕ НАПРАВЛЕНИЯ
# ═══════════════════════════════════════════════════════════════════════
b2_col, b3_col = st.columns([5, 5])

# ----------------------------------------------------------
# БЛОК 2: КАРТА ПРОДАЖ ПО ПРОДУКТАМ И РЕГИОНАМ
# ----------------------------------------------------------
with b2_col:
    st.markdown('<div class="block-header">Блок 2 — Карта продаж по продуктам и регионам</div>',
                unsafe_allow_html=True)

    fig_heat = plot_heatmap(df_filtered)
    st.plotly_chart(fig_heat, use_container_width=True, config={'displayModeBar': False})

    # Автоматический вывод о лучшем направлении
    if not df_filtered.empty:
        best_combo = (df_filtered.groupby(['product_ru', 'region_ru'])
                     ['revenue_usd_mn'].sum().idxmax())
        best_val = (df_filtered.groupby(['product_ru', 'region_ru'])
                   ['revenue_usd_mn'].sum().max())
        st.markdown(
            f"📌 **Наибольшая выручка** за выбранный период приходится на "
            f"«**{best_combo[0]}**» в регионе «**{best_combo[1]}**» — "
            f"${best_val:,.0f} млн"
        )

# ----------------------------------------------------------
# БЛОК 3: ПРИОРИТЕТНЫЕ НАПРАВЛЕНИЯ ПРОДАЖ
# ----------------------------------------------------------
with b3_col:
    st.markdown('<div class="block-header">Блок 3 — Приоритетные направления продаж</div>',
                unsafe_allow_html=True)

    result = plot_bubble_chart(df_filtered)
    if isinstance(result, tuple):
        fig_bubble, last_q_df = result
        st.plotly_chart(fig_bubble, use_container_width=True, config={'displayModeBar': False})

        # Автоматические выводы
        if not last_q_df.empty:
            # Направление с максимальной выручкой
            top_rev_row = last_q_df.loc[last_q_df['revenue_usd_mn'].idxmax()]
            st.markdown(
                f"💰 **Макс. выручка:** «{top_rev_row['product_ru']}» / "
                f"«{top_rev_row['region_ru'].split(',')[0]}» — "
                f"${top_rev_row['revenue_usd_mn']:,.0f} млн"
            )

            # Направление с максимальным ростом
            if last_q_df['yoy_growth'].notna().any():
                top_growth_row = last_q_df.loc[last_q_df['yoy_growth'].idxmax()]
                growth_val = top_growth_row['yoy_growth']
                sign = "+" if growth_val > 0 else ""
                st.markdown(
                    f"📈 **Макс. рост:** «{top_growth_row['product_ru']}» / "
                    f"«{top_growth_row['region_ru'].split(',')[0]}» — "
                    f"{sign}{growth_val:.1f}%"
                )

            # Приоритетные направления (высокая выручка + высокий рост)
            if last_q_df['yoy_growth'].notna().any():
                median_rev = last_q_df['revenue_usd_mn'].median()
                median_growth = last_q_df['yoy_growth'].median()
                priority = last_q_df[
                    (last_q_df['revenue_usd_mn'] > median_rev) &
                    (last_q_df['yoy_growth'] > median_growth)
                ]
                if not priority.empty:
                    priority_names = [
                        f"«{r['product_ru']} / {r['region_ru'].split(',')[0]}»"
                        for _, r in priority.iterrows()
                    ]
                    st.markdown(
                        f"⭐ **Приоритетные направления:** {', '.join(priority_names)}"
                    )
    else:
        st.info("Пузырьковая диаграмма: выберите несколько продуктов и регионов.")

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════
# ДОКУМЕНТАЦИЯ ВНУТРИ ДАШБОРДА
# ═══════════════════════════════════════════════════════════════════════
with st.expander("📚 Методология, данные и ограничения"):
    tab1, tab2, tab3, tab4 = st.tabs([
        "Данные", "Методология", "Прогноз", "Ограничения"
    ])

    with tab1:
        st.markdown("""
**Источники данных**

Использованы исключительно приложенные локальные отчёты NIKE (PDF):
- 13 квартальных пресс-релизов за Q1 FY2023 — Q1 FY2026
- 3 годовых 10-K отчёта (FY2023, FY2024, FY2025) — для перекрёстной проверки

**Период анализа:** Q1 FY2023 (кв. завершён 31.08.2022) — Q1 FY2026 (кв. завершён 31.08.2025)

**Финансовый год NIKE** не совпадает с календарным:
- Q1: июнь — август
- Q2: сентябрь — ноябрь
- Q3: декабрь — февраль
- Q4: март — май

**Детализация:** 3 продукта × 4 региона × 13 кварталов = **156 наблюдений**

**Продукты:** Обувь (Footwear), Одежда (Apparel), Экипировка (Equipment)

**Регионы:** Северная Америка, Европа/Ближний Восток/Африка, Большой Китай, АТР и Латинская Америка

**Единица измерения:** млн долларов США (отчётная)

**Исключено:** Converse, Corporate, Global Brand Divisions
        """)

    with tab2:
        st.markdown("""
**Извлечение данных**

PDF-файлы содержат страницы в виде растровых изображений (не текст).
Данные извлечены путём визуальной инспекции рендеренных страниц (PyMuPDF).
Каждое значение верифицировано по итоговой строке региона в таблице DIVISIONAL REVENUES.
Расчётных значений нет — все 156 наблюдений получены напрямую из отчётов.

**Расчёт показателей**

- **Доля направления** = выручка направления / сумма всех 12 направлений × 100%
- **Рост год к году** = (выручка Q[t] / выручка Q[t-4] − 1) × 100%
- При агрегации нескольких направлений сначала суммируется выручка, затем рассчитываются производные

**Методология сезонности**

1. Для каждого сочетания продукт × регион рассчитывается средняя выручка в Q1, Q2, Q3, Q4
2. Сезонный индекс = средняя выручка в квартале / средняя выручка за все кварталы
3. Индекс > 1: квартал исторически сильнее среднего; < 1: слабее
4. Определяется лучший квартал для каждого сочетания и для выбранного среза
        """)

    with tab3:
        st.markdown("""
**Методология прогноза**

Прогнозируется **каждое из 12 направлений** отдельно (3 × 4), что позволяет:
- сохранить индивидуальную сезонность каждого направления
- корректно применять фильтры
- агрегировать прогнозы в любом сочетании

**Основная модель:** Holt-Winters (ExponentialSmoothing)
- Аддитивный тренд + аддитивная сезонность
- Сезонный период: 4 квартала
- Горизонт прогноза: 4 квартала
- Сезонная компонента включена в модель — добавлять сезонный индекс повторно нельзя

**Резервный метод:** Сезонный наивный прогноз
- Применяется если: < 8 наблюдений, неположительные значения или Holt-Winters проигрывает
- Прогноз Q(t) = факт Q(t−4)

**Выбор модели:** простая временна́я проверка — исключаем последние 4 квартала,
обучаем на ранних данных, сравниваем MAE Holt-Winters и сезонного наивного метода.

**Прогноз выбранной выручки** = сумма прогнозов выбранных направлений

**Прогноз доли** = прогноз выбранной выручки / прогноз общей выручки × 100%
(не независимая линия, а расчёт на основе прогнозов всех 12 рядов)

*Прогнозы носят учебный характер.*
        """)

    with tab4:
        st.markdown("""
**Ограничения анализа**

- Доступно только **13 кварталов** — ограниченная история для обучения моделей
- **Прогноз носит учебный характер** — не является инвестиционной рекомендацией
- Анализируется **выручка**, а не прибыль или рентабельность
- **Converse** и прочие направления исключены из анализа
- **Совместная прибыльность** продукта по регионам публично не раскрывается
- Результаты зависят от **качества приложенных отчётов** и точности извлечения
- Сезонность оценивается на ограниченной истории (3 наблюдения на квартал)
- Макроэкономические факторы (курсы валют, рецессии) в модели не учитываются
- После применения фильтров число наблюдений для обучения может сократиться
        """)

# -----------------------------------------------------------------------
# Подвал с технической информацией
# -----------------------------------------------------------------------
st.markdown(
    "<p style='text-align:center; color:#9aa0a6; font-size:11px; margin-top:20px;'>"
    "Дашборд продаж NIKE | Учебный проект | Данные: локальные отчёты NIKE FY2023–FY2026 | "
    "Стек: Python · Streamlit · Plotly · Statsmodels"
    "</p>",
    unsafe_allow_html=True
)
