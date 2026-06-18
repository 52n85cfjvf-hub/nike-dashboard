"""
Модуль расчёта финансовых показателей NIKE.

Рассчитывает агрегированные метрики для выбранного среза данных:
выручку, долю, рост год к году. Строго соблюдает правило агрегации:
сначала суммируем денежные показатели, затем вычисляем производные.
"""

import pandas as pd
import numpy as np
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def aggregate_selected_revenue(
    df_filtered: pd.DataFrame,
    df_full: pd.DataFrame
) -> pd.DataFrame:
    """
    Агрегирует выручку выбранного среза по кварталам.

    Рассчитывает для каждого квартала:
    - selected_revenue: сумма выручки выбранных продуктов и регионов
    - total_revenue: сумма всех 12 направлений (для расчёта доли)
    - selected_share: доля выбранного среза в анализируемой выручке

    ВАЖНО: Нельзя суммировать доли или темпы роста напрямую.
    Сначала агрегируем денежные показатели, потом рассчитываем производные.

    Args:
        df_filtered: Отфильтрованный датасет (только выбранные продукты/регионы).
        df_full: Полный датасет (для расчёта знаменателя долей).

    Returns:
        pd.DataFrame: Агрегированные данные по кварталам.
    """
    if df_filtered.empty:
        return pd.DataFrame()

    # Шаг 1: Агрегируем выбранную выручку по кварталам
    selected = (df_filtered
                .groupby(['fiscal_period', 'period_order', 'period_label_ru'])
                ['revenue_usd_mn']
                .sum()
                .reset_index()
                .rename(columns={'revenue_usd_mn': 'selected_revenue'}))

    # Шаг 2: Берём общую анализируемую выручку из полного датасета
    # Это важно: знаменатель всегда берём из ПОЛНОГО датасета,
    # чтобы доля была корректной долей в общей выручке NIKE Brand
    total = (df_full
             .groupby('fiscal_period')['revenue_usd_mn']
             .sum()
             .reset_index()
             .rename(columns={'revenue_usd_mn': 'total_revenue'}))

    # Шаг 3: Объединяем
    result = selected.merge(total, on='fiscal_period', how='left')

    # Шаг 4: Рассчитываем долю (ПОСЛЕ агрегации денежных показателей)
    result['selected_share_pct'] = (
        result['selected_revenue'] / result['total_revenue'] * 100
    ).round(2)

    # Шаг 5: Рассчитываем рост год к году для ВЫБРАННОГО среза
    # Нельзя суммировать темпы роста отдельных направлений
    result = result.sort_values('period_order').reset_index(drop=True)
    result['selected_yoy_pct'] = result['selected_revenue'].pct_change(periods=4) * 100
    result['selected_yoy_pct'] = result['selected_yoy_pct'].round(2)

    return result


def get_kpi_values(
    df_filtered: pd.DataFrame,
    df_full: pd.DataFrame
) -> dict:
    """
    Рассчитывает четыре KPI-показателя для последнего доступного квартала.

    KPI:
    1. Выручка выбранного среза за последний квартал
    2. Рост год к году (последний квартал vs тот же квартал год назад)
    3. Доля в анализируемой выручке NIKE Brand
    4. Лучший квартал (Q1–Q4) по средней исторической выручке

    Args:
        df_filtered: Отфильтрованный датасет.
        df_full: Полный датасет.

    Returns:
        dict: Словарь с ключами revenue, yoy_pct, share_pct, best_quarter.
    """
    result = {
        'revenue': None,
        'yoy_pct': None,
        'share_pct': None,
        'best_quarter': None,
        'best_quarter_avg': None,
    }

    if df_filtered.empty:
        return result

    # Агрегируем по кварталам
    agg = aggregate_selected_revenue(df_filtered, df_full)
    if agg.empty:
        return result

    # Последний квартал
    last_row = agg.iloc[-1]
    result['revenue'] = last_row['selected_revenue']
    result['yoy_pct'] = last_row['selected_yoy_pct'] if not pd.isna(
        last_row['selected_yoy_pct']) else None
    result['share_pct'] = last_row['selected_share_pct']

    # Лучший квартал по средней исторической выручке
    # Группируем по номеру квартала (1–4) и берём среднее
    df_temp = df_filtered.copy()
    df_temp['q_agg'] = (df_temp
                        .groupby(['fiscal_period', 'period_order'])['revenue_usd_mn']
                        .transform('sum'))
    df_temp = df_temp[['fiscal_quarter', 'fiscal_period', 'period_order', 'q_agg']].drop_duplicates()

    best_q = df_temp.groupby('fiscal_quarter')['q_agg'].mean()
    if not best_q.empty:
        best_q_num = best_q.idxmax()
        result['best_quarter'] = best_q_num
        result['best_quarter_avg'] = best_q.max()

    return result
