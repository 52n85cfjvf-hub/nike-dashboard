"""
Модуль построения графиков для дашборда NIKE.

Все графики реализованы на Plotly с русскоязычными подписями.
Цвета продуктов зафиксированы для консистентности.

ИСПРАВЛЕНИЯ (pandas 3.x + Plotly 6.x совместимость):
  - applymap → apply(col.map(...))
  - add_vline с текстовой осью → add_shape + add_annotation
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import logging

logger = logging.getLogger(__name__)

# Цвета продуктов — зафиксированы для всех графиков
PRODUCT_COLORS = {
    'Footwear': '#1a73e8',
    'Apparel': '#34a853',
    'Equipment': '#fa7b17',
    'Обувь': '#1a73e8',
    'Одежда': '#34a853',
    'Экипировка': '#fa7b17',
}

FORECAST_COLOR = '#9aa0a6'
DIVIDER_COLOR = '#ea4335'


def _add_vline_text(fig, x_label, color, text="Начало прогноза"):
    """
    Plotly 6.x ломается на add_vline с текстовой (категориальной) осью.
    Используем add_shape + add_annotation вместо add_vline.
    """
    fig.add_shape(
        type='line',
        xref='x', yref='paper',
        x0=x_label, x1=x_label,
        y0=0, y1=1,
        line=dict(dash='dot', color=color, width=2),
    )
    fig.add_annotation(
        x=x_label,
        y=0.97,
        yref='paper',
        text=text,
        showarrow=False,
        xanchor='left',
        xshift=6,
        font=dict(size=10, color=color),
        bgcolor='rgba(255,255,255,0.8)',
        bordercolor=color,
        borderwidth=1,
    )


def plot_revenue_forecast(
    agg_df: pd.DataFrame,
    forecast_method: str = "Holt-Winters"
) -> go.Figure:
    if agg_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="Нет данных для отображения",
                           xref="paper", yref="paper", x=0.5, y=0.5)
        return fig

    actual = agg_df[~agg_df['is_forecast']].copy()
    forecast = agg_df[agg_df['is_forecast']].copy()

    if not actual.empty and not forecast.empty:
        last_actual = actual.iloc[[-1]].copy()
        last_actual['is_forecast'] = True
        forecast = pd.concat([last_actual, forecast], ignore_index=True)

    fig = go.Figure()

    if not actual.empty:
        fig.add_trace(go.Scatter(
            x=actual['period_label_ru'],
            y=actual['selected_revenue'],
            mode='lines+markers',
            name='Факт',
            line=dict(color='#1a73e8', width=2.5),
            marker=dict(size=6),
            hovertemplate='<b>%{x}</b><br>Выручка: $%{y:,.0f} млн<br><extra>Факт</extra>'
        ))

    if not forecast.empty:
        fig.add_trace(go.Scatter(
            x=forecast['period_label_ru'],
            y=forecast['selected_revenue'],
            mode='lines+markers',
            name=f'Прогноз ({forecast_method})',
            line=dict(color='#1a73e8', width=2.5, dash='dash'),
            marker=dict(size=6, symbol='diamond'),
            hovertemplate=(
                '<b>%{x}</b><br>'
                'Прогноз: $%{y:,.0f} млн<br>'
                f'Модель: {forecast_method}<br>'
                '<extra>Прогноз</extra>'
            )
        ))

    # ── FIX: add_vline → add_shape + add_annotation ──────────────────
    if not actual.empty and not forecast.empty:
        _add_vline_text(fig, actual.iloc[-1]['period_label_ru'], DIVIDER_COLOR)

    fig.update_layout(
        title=dict(
            text=f'Выручка выбранного среза, млн $<br>'
                 f'<sub>Модель: {forecast_method} | Сезонность: 4 квартала</sub>',
            font=dict(size=14)
        ),
        xaxis_title='Финансовый квартал',
        yaxis_title='Выручка, млн $',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        hovermode='x unified',
        plot_bgcolor='white',
        paper_bgcolor='white',
        yaxis=dict(gridcolor='#f0f0f0'),
        xaxis=dict(gridcolor='#f0f0f0'),
        height=350,
        margin=dict(l=50, r=20, t=80, b=50),
    )
    return fig


def plot_share_forecast(
    agg_df: pd.DataFrame,
    forecast_method: str = "Holt-Winters"
) -> go.Figure:
    if agg_df.empty or 'selected_share_pct' not in agg_df.columns:
        fig = go.Figure()
        fig.add_annotation(text="Нет данных", xref="paper", yref="paper", x=0.5, y=0.5)
        return fig

    actual = agg_df[~agg_df['is_forecast']].copy()
    forecast = agg_df[agg_df['is_forecast']].copy()

    if not actual.empty and not forecast.empty:
        last_actual = actual.iloc[[-1]].copy()
        last_actual['is_forecast'] = True
        forecast = pd.concat([last_actual, forecast], ignore_index=True)

    fig = go.Figure()

    if not actual.empty:
        fig.add_trace(go.Scatter(
            x=actual['period_label_ru'],
            y=actual['selected_share_pct'],
            mode='lines+markers',
            name='Факт',
            line=dict(color='#34a853', width=2.5),
            marker=dict(size=6),
            hovertemplate='<b>%{x}</b><br>Доля: %{y:.1f}%<br><extra>Факт</extra>'
        ))

    if not forecast.empty:
        fig.add_trace(go.Scatter(
            x=forecast['period_label_ru'],
            y=forecast['selected_share_pct'],
            mode='lines+markers',
            name=f'Прогноз ({forecast_method})',
            line=dict(color='#34a853', width=2.5, dash='dash'),
            marker=dict(size=6, symbol='diamond'),
            hovertemplate=(
                '<b>%{x}</b><br>'
                'Прогноз доли: %{y:.1f}%<br>'
                f'Метод: {forecast_method}<br>'
                '<extra>Прогноз</extra>'
            )
        ))

    # ── FIX: add_vline → add_shape + add_annotation ──────────────────
    if not actual.empty and not forecast.empty:
        _add_vline_text(fig, actual.iloc[-1]['period_label_ru'], DIVIDER_COLOR)

    fig.update_layout(
        title=dict(text='Доля выбранного среза в выручке NIKE Brand, %', font=dict(size=13)),
        xaxis_title='Финансовый квартал',
        yaxis_title='Доля, %',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        hovermode='x unified',
        plot_bgcolor='white',
        paper_bgcolor='white',
        yaxis=dict(gridcolor='#f0f0f0', ticksuffix='%'),
        xaxis=dict(gridcolor='#f0f0f0'),
        height=280,
        margin=dict(l=50, r=20, t=50, b=50),
    )
    return fig


def plot_seasonality_bar(seasonal_summary: pd.DataFrame) -> go.Figure:
    if seasonal_summary.empty:
        fig = go.Figure()
        fig.add_annotation(text="Нет данных", xref="paper", yref="paper", x=0.5, y=0.5)
        return fig

    colors = ['#1a73e8' if row['is_best'] else '#aecbfa'
              for _, row in seasonal_summary.iterrows()]

    fig = go.Figure(go.Bar(
        x=seasonal_summary['quarter_label'],
        y=seasonal_summary['avg_revenue_usd_mn'],
        marker_color=colors,
        text=[f"${v:,.0f}" for v in seasonal_summary['avg_revenue_usd_mn']],
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>Средняя выручка: $%{y:,.0f} млн<br><extra></extra>'
    ))

    fig.update_layout(
        title=dict(text='Средняя выручка по кварталам (сезонность)', font=dict(size=13)),
        xaxis_title='Квартал',
        yaxis_title='Средняя выручка, млн $',
        plot_bgcolor='white',
        paper_bgcolor='white',
        yaxis=dict(gridcolor='#f0f0f0'),
        height=280,
        margin=dict(l=50, r=20, t=50, b=50),
        showlegend=False,
    )
    return fig


def plot_heatmap(df_filtered: pd.DataFrame) -> go.Figure:
    if df_filtered.empty:
        fig = go.Figure()
        fig.add_annotation(text="Нет данных", xref="paper", yref="paper", x=0.5, y=0.5)
        return fig

    pivot = df_filtered.pivot_table(
        index='region_ru',
        columns='product_ru',
        values='revenue_usd_mn',
        aggfunc='sum'
    )

    region_order = [
        'Северная Америка',
        'Европа, Ближний Восток и Африка',
        'Большой Китай',
        'Азиатско-Тихоокеанский регион и Латинская Америка',
    ]
    product_order = ['Обувь', 'Одежда', 'Экипировка']

    pivot = pivot.reindex(
        index=[r for r in region_order if r in pivot.index],
        columns=[p for p in product_order if p in pivot.columns]
    )

    # ── FIX: applymap удалён в pandas 3.x → apply(col.map(...)) ─────
    text_matrix = pivot.apply(
        lambda col: col.map(lambda v: f"${v:,.0f}" if pd.notna(v) else "н/д")
    )

    fig = go.Figure(go.Heatmap(
        z=pivot.values,
        x=pivot.columns.tolist(),
        y=pivot.index.tolist(),
        text=text_matrix.values,
        texttemplate='%{text}',
        textfont=dict(size=12),
        colorscale='Blues',
        hovertemplate=(
            '<b>Регион:</b> %{y}<br>'
            '<b>Продукт:</b> %{x}<br>'
            '<b>Выручка:</b> $%{z:,.0f} млн<br>'
            '<extra></extra>'
        ),
        colorbar=dict(title='Выручка, млн $', title_side='right'),
    ))

    fig.update_layout(
        title=dict(text='Суммарная выручка по продуктам и регионам, млн $',
                   font=dict(size=14)),
        xaxis_title='Продукт',
        yaxis_title='Регион',
        height=320,
        margin=dict(l=250, r=50, t=60, b=50),
        plot_bgcolor='white',
        paper_bgcolor='white',
    )
    return fig


def plot_bubble_chart(df_filtered: pd.DataFrame) -> go.Figure:
    if df_filtered.empty:
        fig = go.Figure()
        fig.add_annotation(text="Нет данных", xref="paper", yref="paper", x=0.5, y=0.5)
        return fig

    last_order = df_filtered['period_order'].max()
    last_quarter_df = df_filtered[df_filtered['period_order'] == last_order].copy()

    if last_quarter_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="Нет данных за последний квартал",
                           xref="paper", yref="paper", x=0.5, y=0.5)
        return fig

    prev_order = last_order - 4

    prev_quarter_df = df_filtered[df_filtered['period_order'] == prev_order].copy()

    if not prev_quarter_df.empty:
        prev_rev = prev_quarter_df.set_index(['product', 'region'])['revenue_usd_mn']
        last_quarter_df['yoy_growth'] = last_quarter_df.apply(
            lambda r: (r['revenue_usd_mn'] / prev_rev.get((r['product'], r['region']), np.nan) - 1) * 100
            if (r['product'], r['region']) in prev_rev.index else np.nan,
            axis=1
        )
    else:
        last_quarter_df['yoy_growth'] = np.nan

    total_rev = last_quarter_df['revenue_usd_mn'].sum()
    last_quarter_df['share_pct'] = last_quarter_df['revenue_usd_mn'] / total_rev * 100

    median_rev = last_quarter_df['revenue_usd_mn'].median()
    median_growth = last_quarter_df['yoy_growth'].median() if last_quarter_df['yoy_growth'].notna().any() else 0

    fig = go.Figure()

    x_max = last_quarter_df['revenue_usd_mn'].max() * 1.3
    y_min = last_quarter_df['yoy_growth'].min() * 1.3 if last_quarter_df['yoy_growth'].notna().any() else -30
    y_max = last_quarter_df['yoy_growth'].max() * 1.3 if last_quarter_df['yoy_growth'].notna().any() else 30
    zone_alpha = 0.06

    fig.add_shape(type='rect', x0=median_rev, x1=x_max, y0=median_growth, y1=y_max,
                  fillcolor=f'rgba(52,168,83,{zone_alpha})', line=dict(width=0))
    fig.add_annotation(x=x_max * 0.98, y=y_max * 0.92, text='Приоритетные',
                       showarrow=False, font=dict(color='#34a853', size=10), xanchor='right')

    fig.add_shape(type='rect', x0=median_rev, x1=x_max, y0=y_min, y1=median_growth,
                  fillcolor=f'rgba(26,115,232,{zone_alpha})', line=dict(width=0))
    fig.add_annotation(x=x_max * 0.98, y=y_min * 0.92, text='Зрелые',
                       showarrow=False, font=dict(color='#1a73e8', size=10), xanchor='right')

    fig.add_shape(type='rect', x0=0, x1=median_rev, y0=median_growth, y1=y_max,
                  fillcolor=f'rgba(250,123,23,{zone_alpha})', line=dict(width=0))
    fig.add_annotation(x=median_rev * 0.05, y=y_max * 0.92, text='Развивающиеся',
                       showarrow=False, font=dict(color='#fa7b17', size=10), xanchor='left')

    fig.add_shape(type='rect', x0=0, x1=median_rev, y0=y_min, y1=median_growth,
                  fillcolor=f'rgba(154,160,166,{zone_alpha})', line=dict(width=0))
    fig.add_annotation(x=median_rev * 0.05, y=y_min * 0.92, text='Слабые',
                       showarrow=False, font=dict(color='#9aa0a6', size=10), xanchor='left')

    # ── FIX: add_vline / add_hline с числовой осью — здесь OK ────────
    fig.add_vline(x=median_rev, line_dash='dot', line_color='#5f6368', line_width=1)
    fig.add_hline(y=median_growth, line_dash='dot', line_color='#5f6368', line_width=1)

    for product in last_quarter_df['product'].unique():
        pdata = last_quarter_df[last_quarter_df['product'] == product]
        color = PRODUCT_COLORS.get(product, '#5f6368')

        fig.add_trace(go.Scatter(
            x=pdata['revenue_usd_mn'],
            y=pdata['yoy_growth'],
            mode='markers+text',
            name=pdata['product_ru'].iloc[0],
            marker=dict(size=pdata['share_pct'] * 3, color=color, opacity=0.8,
                        line=dict(width=1, color='white')),
            text=pdata['region_ru'].str.split(',').str[0],
            textposition='top center',
            textfont=dict(size=9),
            hovertemplate=(
                '<b>%{text}</b><br>'
                f'Продукт: {pdata["product_ru"].iloc[0]}<br>'
                'Выручка: $%{x:,.0f} млн<br>'
                'Рост г/г: %{y:.1f}%<br>'
                '<extra></extra>'
            ),
            customdata=pdata[['region_ru', 'product_ru', 'share_pct']].values,
        ))

    last_period = last_quarter_df['fiscal_period'].iloc[0]

    fig.update_layout(
        title=dict(
            text=f'Приоритетные направления — {last_period}<br>'
                 f'<sub>X: выручка | Y: рост г/г | размер: доля | '
                 f'медиана: ${median_rev:,.0f} млн / {median_growth:.1f}%</sub>',
            font=dict(size=13)
        ),
        xaxis_title='Квартальная выручка, млн $',
        yaxis_title='Рост год к году, %',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        hovermode='closest',
        plot_bgcolor='white',
        paper_bgcolor='white',
        yaxis=dict(gridcolor='#f0f0f0', ticksuffix='%', zeroline=False),
        xaxis=dict(gridcolor='#f0f0f0', zeroline=False),
        height=400,
        margin=dict(l=60, r=20, t=80, b=60),
    )

    return fig, last_quarter_df
