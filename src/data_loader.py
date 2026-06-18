"""
Модуль загрузки и кэширования датасета NIKE.

Предоставляет функции для загрузки обработанных данных с кэшированием
через Streamlit st.cache_data. Формирует человекочитаемые метки кварталов.
"""

import pandas as pd
import numpy as np
import logging
import os
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# Путь к обработанным данным (относительно корня проекта)
PROCESSED_DATA_PATH = 'data/processed/nike_quarterly_sales.csv'

# Соответствие финансовых кварталов NIKE календарным месяцам
# Q1: июнь — август, Q2: сентябрь — ноябрь, Q3: декабрь — февраль, Q4: март — май
QUARTER_LABELS_RU = {
    'Q1 FY2023': '1 кв. 2023 ф. г.',
    'Q2 FY2023': '2 кв. 2023 ф. г.',
    'Q3 FY2023': '3 кв. 2023 ф. г.',
    'Q4 FY2023': '4 кв. 2023 ф. г.',
    'Q1 FY2024': '1 кв. 2024 ф. г.',
    'Q2 FY2024': '2 кв. 2024 ф. г.',
    'Q3 FY2024': '3 кв. 2024 ф. г.',
    'Q4 FY2024': '4 кв. 2024 ф. г.',
    'Q1 FY2025': '1 кв. 2025 ф. г.',
    'Q2 FY2025': '2 кв. 2025 ф. г.',
    'Q3 FY2025': '3 кв. 2025 ф. г.',
    'Q4 FY2025': '4 кв. 2025 ф. г.',
    'Q1 FY2026': '1 кв. 2026 ф. г.',
}

# Обратный маппинг: русская метка → технический код
LABELS_TO_PERIOD = {v: k for k, v in QUARTER_LABELS_RU.items()}

# Переводы продуктов
PRODUCT_TRANSLATIONS = {
    'Footwear': 'Обувь',
    'Apparel': 'Одежда',
    'Equipment': 'Экипировка',
}
PRODUCT_RU_TO_EN = {v: k for k, v in PRODUCT_TRANSLATIONS.items()}

# Переводы регионов
REGION_TRANSLATIONS = {
    'North America': 'Северная Америка',
    'EMEA': 'Европа, Ближний Восток и Африка',
    'Greater China': 'Большой Китай',
    'APLA': 'Азиатско-Тихоокеанский регион и Латинская Америка',
}
REGION_RU_TO_EN = {v: k for k, v in REGION_TRANSLATIONS.items()}

# Цвета продуктов для консистентной визуализации
PRODUCT_COLORS = {
    'Footwear': '#1a73e8',   # синий
    'Apparel': '#34a853',    # зелёный
    'Equipment': '#fa7b17',  # оранжевый
    'Обувь': '#1a73e8',
    'Одежда': '#34a853',
    'Экипировка': '#fa7b17',
}


def load_data() -> pd.DataFrame:
    """
    Загружает обработанный датасет NIKE из CSV.

    Если файл не найден, формирует датасет на лету из сырых данных.
    Добавляет русские метки кварталов для отображения в интерфейсе.

    Returns:
        pd.DataFrame: Датасет с 156 строками.

    Raises:
        RuntimeError: Если данные не удаётся загрузить или сформировать.
    """
    # Определяем путь к файлу относительно корня проекта
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    csv_path = project_root / PROCESSED_DATA_PATH

    if csv_path.exists():
        # Загружаем из готового файла
        df = pd.read_csv(csv_path, parse_dates=['quarter_end_date'])
        logger.info(f"Данные загружены из {csv_path}: {len(df)} строк")
    else:
        # Формируем датасет на лету
        logger.warning(f"Файл {csv_path} не найден, формируем датасет...")
        sys.path.insert(0, str(project_root))
        from scripts.build_dataset import build_dataset, save_dataset
        df = build_dataset()
        save_dataset(df, str(project_root / 'data/processed'))

    # Добавляем русские метки кварталов
    df['period_label_ru'] = df['fiscal_period'].map(QUARTER_LABELS_RU)

    # Убеждаемся в правильной сортировке
    df = df.sort_values(['period_order', 'region', 'product']).reset_index(drop=True)

    return df


def get_sorted_periods(df: pd.DataFrame) -> list[str]:
    """
    Возвращает список кварталов в хронологическом порядке (русские метки).

    Args:
        df: Датасет.

    Returns:
        list[str]: Список русских меток кварталов.
    """
    periods = (df[['fiscal_period', 'period_order']]
               .drop_duplicates()
               .sort_values('period_order')['fiscal_period']
               .tolist())
    return [QUARTER_LABELS_RU.get(p, p) for p in periods]


def filter_data(
    df: pd.DataFrame,
    start_period: str,
    end_period: str,
    products_ru: list[str],
    regions_ru: list[str]
) -> pd.DataFrame:
    """
    Фильтрует датасет по выбранным параметрам.

    Принимает русские метки и переводит их в технические коды для фильтрации.

    Args:
        df: Полный датасет.
        start_period: Начальный квартал (русская метка).
        end_period: Конечный квартал (русская метка).
        products_ru: Список выбранных продуктов (русские названия).
        regions_ru: Список выбранных регионов (русские названия).

    Returns:
        pd.DataFrame: Отфильтрованный датасет.
    """
    # Переводим русские метки в технические коды
    start_code = LABELS_TO_PERIOD.get(start_period, start_period)
    end_code = LABELS_TO_PERIOD.get(end_period, end_period)

    # Переводим русские названия в английские для фильтрации
    products_en = [PRODUCT_RU_TO_EN.get(p, p) for p in products_ru]
    regions_en = [REGION_RU_TO_EN.get(r, r) for r in regions_ru]

    # Получаем диапазон period_order для периода
    period_lookup = df[['fiscal_period', 'period_order']].drop_duplicates()
    start_order = period_lookup[period_lookup['fiscal_period'] == start_code]['period_order'].values
    end_order = period_lookup[period_lookup['fiscal_period'] == end_code]['period_order'].values

    if len(start_order) == 0 or len(end_order) == 0:
        logger.warning("Период не найден в данных, возвращаем пустой датафрейм")
        return df.iloc[0:0]

    start_order = start_order[0]
    end_order = end_order[0]

    # Применяем фильтры
    mask = (
        (df['period_order'] >= start_order) &
        (df['period_order'] <= end_order) &
        (df['product'].isin(products_en)) &
        (df['region'].isin(regions_en))
    )

    return df[mask].copy()
