"""
Модуль расчёта сезонности продаж NIKE.

Рассчитывает сезонные индексы для каждого сочетания продукт × регион,
определяет лучшие кварталы и лучшие сочетания для каждого квартала.

Сезонный индекс = средняя выручка в квартале / средняя выручка за все кварталы.
Индекс > 1 означает, что квартал исторически сильнее среднего.
Индекс < 1 означает, что квартал исторически слабее среднего.
"""

import pandas as pd
import numpy as np
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def calculate_seasonality(df: pd.DataFrame) -> pd.DataFrame:
    """
    Рассчитывает сезонные индексы для каждого сочетания продукт × регион.

    Для каждого из 12 сочетаний (3 продукта × 4 региона) вычисляет:
    - среднюю выручку по каждому финансовому кварталу (Q1–Q4)
    - среднюю выручку за все кварталы
    - сезонный индекс каждого квартала
    - флаг лучшего квартала для данного сочетания

    Args:
        df: Полный датасет nike_quarterly_sales.

    Returns:
        pd.DataFrame: Датасет с сезонными индексами (48 строк = 12 × 4).
    """
    logger.info("Расчёт сезонных индексов...")

    # Группируем по сочетанию продукт × регион × квартал
    # и берём среднюю выручку за доступные годы
    seasonal = (df.groupby(['product', 'product_ru', 'region', 'region_ru',
                            'fiscal_quarter'])['revenue_usd_mn']
                .mean()
                .reset_index()
                .rename(columns={'revenue_usd_mn': 'average_revenue_usd_mn'}))

    # Рассчитываем среднюю выручку за все кварталы для каждого сочетания
    overall_avg = (seasonal
                   .groupby(['product', 'region'])['average_revenue_usd_mn']
                   .mean()
                   .reset_index()
                   .rename(columns={'average_revenue_usd_mn': 'overall_avg_revenue'}))

    seasonal = seasonal.merge(overall_avg, on=['product', 'region'], how='left')

    # Сезонный индекс = средняя выручка в квартале / общая средняя
    seasonal['seasonal_index'] = (
        seasonal['average_revenue_usd_mn'] / seasonal['overall_avg_revenue']
    ).round(4)

    # Ранжирование кварталов по выручке внутри каждого сочетания
    seasonal['rank_within_combination'] = (
        seasonal.groupby(['product', 'region'])['average_revenue_usd_mn']
        .rank(ascending=False)
        .astype(int)
    )

    # Флаг: является ли квартал лучшим для данного сочетания
    seasonal['is_best_quarter_for_combination'] = (
        seasonal['rank_within_combination'] == 1
    )

    # Ранжирование сочетаний внутри каждого квартала
    seasonal['rank_within_quarter'] = (
        seasonal.groupby('fiscal_quarter')['average_revenue_usd_mn']
        .rank(ascending=False)
        .astype(int)
    )

    logger.info(f"Сезонные индексы рассчитаны: {len(seasonal)} строк")
    return seasonal


def get_seasonal_summary(
    df_filtered: pd.DataFrame,
    df_full: pd.DataFrame
) -> pd.DataFrame:
    """
    Формирует сводную таблицу сезонности для выбранного среза.

    Для каждого из финансовых кварталов Q1–Q4 определяет:
    - лучший продукт (по средней выручке)
    - лучший регион (по средней выручке)
    - лучшее сочетание продукт × регион
    - среднюю выручку выбранного среза

    Args:
        df_filtered: Отфильтрованный датасет.
        df_full: Полный датасет (для расчёта сезонных индексов).

    Returns:
        pd.DataFrame: Сводная таблица (4 строки, по одной на квартал).
    """
    if df_filtered.empty:
        return pd.DataFrame()

    rows = []
    for q in [1, 2, 3, 4]:
        # Фильтруем по конкретному номеру квартала
        q_data = df_filtered[df_filtered['fiscal_quarter'] == q]
        if q_data.empty:
            continue

        # Средняя выручка выбранного среза за этот квартал
        agg_revenue = q_data.groupby('fiscal_period')['revenue_usd_mn'].sum().mean()

        # Лучший продукт по средней выручке в этом квартале
        best_product_row = (q_data.groupby(['product', 'product_ru'])['revenue_usd_mn']
                           .mean()
                           .idxmax())
        best_product_ru = best_product_row[1]

        # Лучший регион по средней выручке в этом квартале
        best_region_row = (q_data.groupby(['region', 'region_ru'])['revenue_usd_mn']
                          .mean()
                          .idxmax())
        best_region_ru = best_region_row[1]

        # Лучшее сочетание продукт × регион
        best_combo = (q_data.groupby(['product_ru', 'region_ru'])['revenue_usd_mn']
                     .mean()
                     .idxmax())

        rows.append({
            'fiscal_quarter': q,
            'quarter_label': f'{q} кв.',
            'avg_revenue_usd_mn': round(agg_revenue, 0),
            'best_product_ru': best_product_ru,
            'best_region_ru': best_region_ru,
            'best_combo': f"{best_combo[0]} / {best_combo[1]}",
        })

    if not rows:
        return pd.DataFrame()

    result = pd.DataFrame(rows)

    # Добавляем сезонный индекс относительно среднего выбранного среза
    overall_mean = result['avg_revenue_usd_mn'].mean()
    if overall_mean > 0:
        result['seasonal_index'] = (
            result['avg_revenue_usd_mn'] / overall_mean
        ).round(3)
    else:
        result['seasonal_index'] = 1.0

    # Флаг лучшего квартала
    result['is_best'] = result['avg_revenue_usd_mn'] == result['avg_revenue_usd_mn'].max()

    return result


def get_best_quarter_text(seasonal_summary: pd.DataFrame) -> str:
    """
    Формирует автоматический текстовый вывод о сезонности.

    Текст генерируется из фактических расчётов, а не записан заранее.

    Args:
        seasonal_summary: Сводная таблица сезонности.

    Returns:
        str: Текстовый вывод на русском языке.
    """
    if seasonal_summary.empty:
        return "Недостаточно данных для анализа сезонности."

    # Лучший квартал
    best_row = seasonal_summary[seasonal_summary['is_best']].iloc[0]
    best_q = best_row['quarter_label']
    best_rev = best_row['avg_revenue_usd_mn']
    best_product = best_row['best_product_ru']
    best_region = best_row['best_region_ru']
    best_idx = best_row['seasonal_index']

    text = (
        f"Для выбранной выборки исторически наиболее сильным был **{best_q}** "
        f"(сезонный индекс: {best_idx:.2f}). "
        f"Максимальная средняя выручка в этом квартале приходилась на категорию "
        f"«{best_product}» в регионе «{best_region}» "
        f"(средняя выручка: **${best_rev:,.0f} млн**). "
        f"Сезонная модель учитывает эту закономерность при прогнозировании "
        f"следующих кварталов."
    )
    return text


def save_seasonality(df: pd.DataFrame, output_dir: str = 'data/processed') -> None:
    """
    Сохраняет рассчитанные сезонные показатели в CSV.

    Args:
        df: Датасет с сезонными индексами.
        output_dir: Путь к директории вывода.
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    path = f"{output_dir}/nike_seasonality.csv"
    df.to_csv(path, index=False)
    logger.info(f"Сезонные показатели сохранены: {path}")
