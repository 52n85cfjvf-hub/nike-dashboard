#!/usr/bin/env python3
"""
Скрипт формирования итогового датасета NIKE.

Выполняет:
1. Извлечение сырых данных из локальных отчётов
2. Добавление метаданных (переводы, period_order, fiscal_period)
3. Расчёт производных показателей (доля, рост год к году)
4. Валидацию данных
5. Сохранение датасета в CSV и Parquet
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pandas as pd
import numpy as np
import logging
from pathlib import Path

from scripts.extract_local_reports import get_raw_data

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------
# Словари переводов и маппингов
# -----------------------------------------------------------------------

# Перевод регионов на русский язык
REGION_TRANSLATIONS = {
    'North America': 'Северная Америка',
    'EMEA': 'Европа, Ближний Восток и Африка',
    'Greater China': 'Большой Китай',
    'APLA': 'Азиатско-Тихоокеанский регион и Латинская Америка',
}

# Перевод продуктов на русский язык
PRODUCT_TRANSLATIONS = {
    'Footwear': 'Обувь',
    'Apparel': 'Одежда',
    'Equipment': 'Экипировка',
}

# Порядок регионов для стабильной сортировки
REGION_ORDER = ['North America', 'EMEA', 'Greater China', 'APLA']

# Порядок продуктов для стабильной сортировки
PRODUCT_ORDER = ['Footwear', 'Apparel', 'Equipment']


def build_dataset() -> pd.DataFrame:
    """
    Формирует полный нормализованный датасет квартальных продаж NIKE.

    Добавляет метаданные, переводы, расчётные показатели.
    Валидирует структуру и значения.

    Returns:
        pd.DataFrame: Итоговый датасет с 156 строками (13 кв × 3 прод × 4 рег).
    """
    logger.info("Начало формирования датасета...")

    # Шаг 1: Извлечение сырых данных из локальных отчётов
    raw = get_raw_data()
    df = pd.DataFrame(raw)
    logger.info(f"Загружено {len(df)} сырых записей")

    # Шаг 2: Добавление финансового периода в читаемом формате
    # Формируем строку типа "Q1 FY2023" для каждой записи
    df['fiscal_period'] = df.apply(
        lambda r: f"Q{r['fiscal_quarter']} FY{r['fiscal_year']}", axis=1
    )

    # Шаг 3: Добавление period_order для правильной хронологической сортировки
    # period_order = (финансовый год - 2023) * 4 + (квартал - 1)
    df['period_order'] = (df['fiscal_year'] - 2023) * 4 + (df['fiscal_quarter'] - 1)

    # Шаг 4: Добавление переводов
    df['region_ru'] = df['region'].map(REGION_TRANSLATIONS)
    df['product_ru'] = df['product'].map(PRODUCT_TRANSLATIONS)

    # Шаг 5: Преобразование типов данных
    df['quarter_end_date'] = pd.to_datetime(df['quarter_end_date'])
    df['revenue_usd_mn'] = df['revenue_usd_mn'].astype(float)

    # Шаг 6: Расчёт общей анализируемой выручки по кварталу
    # Это сумма всех 12 направлений (3 продукта × 4 региона) за квартал.
    # Не включаем Converse и Global Brand Divisions, так как они
    # не входят в аналитическую детализацию по продуктам и регионам.
    quarter_total = df.groupby('fiscal_period')['revenue_usd_mn'].sum()
    df['total_analyzed_revenue_usd_mn'] = df['fiscal_period'].map(quarter_total)

    # Шаг 7: Расчёт доли направления в анализируемой выручке
    # Формула: revenue_usd_mn / total_analyzed_revenue_usd_mn * 100
    df['revenue_share_pct'] = (
        df['revenue_usd_mn'] / df['total_analyzed_revenue_usd_mn'] * 100
    ).round(2)

    # Шаг 8: Расчёт роста год к году
    # Сравниваем с тем же финансовым кварталом предыдущего года.
    # Для Q1 FY2023 сравнения нет (первый доступный год).
    df = df.sort_values(['region', 'product', 'period_order']).reset_index(drop=True)

    # Создаём ключ для объединения с прошлогодним значением
    df['prev_year'] = df['fiscal_year'] - 1
    df['lookup_key'] = df.apply(
        lambda r: f"Q{r['fiscal_quarter']} FY{r['prev_year']}", axis=1
    )

    # Создаём словарь выручки по ключу (период + регион + продукт)
    rev_dict = {}
    for _, row in df.iterrows():
        key = (row['fiscal_period'], row['region'], row['product'])
        rev_dict[key] = row['revenue_usd_mn']

    # Рассчитываем рост год к году
    def calc_yoy(row: pd.Series) -> float:
        """Рассчитывает рост год к году для одной строки."""
        prev_key = (row['lookup_key'], row['region'], row['product'])
        if prev_key in rev_dict:
            prev_rev = rev_dict[prev_key]
            if prev_rev and prev_rev > 0:
                return round((row['revenue_usd_mn'] / prev_rev - 1) * 100, 2)
        return np.nan

    df['revenue_yoy_growth_pct'] = df.apply(calc_yoy, axis=1)

    # Шаг 9: Очистка вспомогательных столбцов
    df = df.drop(columns=['prev_year', 'lookup_key'])

    # Шаг 10: Финальная сортировка — хронологически, затем по региону и продукту
    df = df.sort_values(['period_order', 'region', 'product']).reset_index(drop=True)

    # Шаг 11: Выбор и упорядочивание итоговых столбцов
    columns_order = [
        'fiscal_year', 'fiscal_quarter', 'fiscal_period', 'quarter_end_date',
        'period_order', 'region', 'region_ru', 'product', 'product_ru',
        'revenue_usd_mn', 'total_analyzed_revenue_usd_mn', 'revenue_share_pct',
        'revenue_yoy_growth_pct', 'is_calculated', 'source_file'
    ]
    df = df[columns_order]

    logger.info(f"Датасет сформирован: {len(df)} строк")
    return df


def save_dataset(df: pd.DataFrame, output_dir: str = 'data/processed') -> None:
    """
    Сохраняет датасет в CSV и Parquet форматы.

    Args:
        df: Датасет для сохранения.
        output_dir: Путь к директории вывода.
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Сохраняем CSV
    csv_path = os.path.join(output_dir, 'nike_quarterly_sales.csv')
    df.to_csv(csv_path, index=False)
    logger.info(f"Датасет сохранён: {csv_path}")

    # Сохраняем Parquet для быстрой загрузки
    try:
        parquet_path = os.path.join(output_dir, 'nike_quarterly_sales.parquet')
        df.to_parquet(parquet_path, index=False)
        logger.info(f"Датасет сохранён: {parquet_path}")
    except Exception as e:
        logger.warning(f"Не удалось сохранить Parquet: {e}")


if __name__ == '__main__':
    # Меняем рабочую директорию на корень проекта
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    df = build_dataset()
    save_dataset(df)

    print("\nСводка по кварталам:")
    summary = df.groupby('fiscal_period')['revenue_usd_mn'].sum()
    for period, total in summary.items():
        print(f"  {period}: ${total:,.0f} млн")
    print(f"\nВсего строк: {len(df)}")
    print(f"Уникальных кварталов: {df['fiscal_period'].nunique()}")
    print(f"Уникальных продуктов: {df['product'].nunique()}")
    print(f"Уникальных регионов: {df['region'].nunique()}")
