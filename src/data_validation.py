"""
Модуль проверки качества данных NIKE.

Выполняет автоматические проверки целостности, структуры и значений датасета.
При обнаружении критических ошибок записывает их в лог и возбуждает исключение.
"""

import pandas as pd
import numpy as np
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

# Ожидаемые константы
EXPECTED_QUARTERS = 13  # Q1 FY2023 — Q1 FY2026
EXPECTED_PRODUCTS = 3   # Footwear, Apparel, Equipment
EXPECTED_REGIONS = 4    # North America, EMEA, Greater China, APLA
EXPECTED_ROWS = EXPECTED_QUARTERS * EXPECTED_PRODUCTS * EXPECTED_REGIONS  # 156

VALID_PRODUCTS = {'Footwear', 'Apparel', 'Equipment'}
VALID_REGIONS = {'North America', 'EMEA', 'Greater China', 'APLA'}

# Ожидаемые кварталы в хронологическом порядке
EXPECTED_PERIODS = [
    'Q1 FY2023', 'Q2 FY2023', 'Q3 FY2023', 'Q4 FY2023',
    'Q1 FY2024', 'Q2 FY2024', 'Q3 FY2024', 'Q4 FY2024',
    'Q1 FY2025', 'Q2 FY2025', 'Q3 FY2025', 'Q4 FY2025',
    'Q1 FY2026',
]


def validate_dataset(df: pd.DataFrame) -> Tuple[bool, list[str]]:
    """
    Выполняет полную проверку качества датасета.

    Проверяет структуру, значения, отсутствие дубликатов и корректность
    расчётных показателей. Возвращает статус и список ошибок/предупреждений.

    Args:
        df: Датасет для проверки.

    Returns:
        Tuple[bool, list[str]]: (успех, список сообщений об ошибках)
    """
    errors = []
    warnings = []

    # ---------------------------------------------------------------
    # Проверка 1: Количество строк
    # ---------------------------------------------------------------
    if len(df) != EXPECTED_ROWS:
        errors.append(
            f"Неверное количество строк: {len(df)}, ожидается {EXPECTED_ROWS}"
        )
    else:
        logger.info(f"✓ Количество строк: {len(df)}")

    # ---------------------------------------------------------------
    # Проверка 2: Количество кварталов
    # ---------------------------------------------------------------
    actual_quarters = df['fiscal_period'].nunique()
    if actual_quarters != EXPECTED_QUARTERS:
        errors.append(
            f"Неверное количество кварталов: {actual_quarters}, "
            f"ожидается {EXPECTED_QUARTERS}"
        )
    else:
        logger.info(f"✓ Количество кварталов: {actual_quarters}")

    # ---------------------------------------------------------------
    # Проверка 3: Наличие всех ожидаемых кварталов
    # ---------------------------------------------------------------
    actual_periods = set(df['fiscal_period'].unique())
    missing_periods = set(EXPECTED_PERIODS) - actual_periods
    if missing_periods:
        errors.append(f"Отсутствуют кварталы: {sorted(missing_periods)}")
    else:
        logger.info("✓ Все ожидаемые кварталы присутствуют")

    # ---------------------------------------------------------------
    # Проверка 4: Количество продуктов
    # ---------------------------------------------------------------
    actual_products = set(df['product'].unique())
    if actual_products != VALID_PRODUCTS:
        errors.append(
            f"Неверный набор продуктов: {actual_products}, "
            f"ожидается {VALID_PRODUCTS}"
        )
    else:
        logger.info(f"✓ Продукты: {actual_products}")

    # ---------------------------------------------------------------
    # Проверка 5: Количество регионов
    # ---------------------------------------------------------------
    actual_regions = set(df['region'].unique())
    if actual_regions != VALID_REGIONS:
        errors.append(
            f"Неверный набор регионов: {actual_regions}, "
            f"ожидается {VALID_REGIONS}"
        )
    else:
        logger.info(f"✓ Регионы: {actual_regions}")

    # ---------------------------------------------------------------
    # Проверка 6: 12 сочетаний в каждом квартале
    # ---------------------------------------------------------------
    combos_per_quarter = df.groupby('fiscal_period').size()
    bad_quarters = combos_per_quarter[combos_per_quarter != 12]
    if len(bad_quarters) > 0:
        errors.append(
            f"Неверное количество сочетаний в кварталах: {bad_quarters.to_dict()}"
        )
    else:
        logger.info("✓ В каждом квартале ровно 12 сочетаний продукт × регион")

    # ---------------------------------------------------------------
    # Проверка 7: Отсутствие дубликатов по ключу квартал + регион + продукт
    # ---------------------------------------------------------------
    dups = df.duplicated(subset=['fiscal_period', 'region', 'product'])
    if dups.any():
        errors.append(f"Обнаружены дубликаты: {dups.sum()} строк")
    else:
        logger.info("✓ Дубликаты отсутствуют")

    # ---------------------------------------------------------------
    # Проверка 8: Числовой тип выручки
    # ---------------------------------------------------------------
    if not pd.api.types.is_numeric_dtype(df['revenue_usd_mn']):
        errors.append("Столбец revenue_usd_mn не является числовым")
    else:
        logger.info("✓ Тип данных revenue_usd_mn корректен")

    # ---------------------------------------------------------------
    # Проверка 9: Отсутствие отрицательных значений выручки
    # ---------------------------------------------------------------
    neg_rev = df[df['revenue_usd_mn'] < 0]
    if len(neg_rev) > 0:
        errors.append(
            f"Обнаружены отрицательные значения выручки: {len(neg_rev)} строк"
        )
    else:
        logger.info("✓ Отрицательных значений выручки нет")

    # ---------------------------------------------------------------
    # Проверка 10: Отсутствие пустых значений в ключевых полях
    # ---------------------------------------------------------------
    key_fields = ['fiscal_period', 'region', 'product', 'revenue_usd_mn']
    for field in key_fields:
        nulls = df[field].isna().sum()
        if nulls > 0:
            errors.append(f"Пустые значения в столбце '{field}': {nulls}")
        else:
            logger.info(f"✓ Пустые значения в '{field}' отсутствуют")

    # ---------------------------------------------------------------
    # Проверка 11: Диапазон долей (0–100%)
    # ---------------------------------------------------------------
    if 'revenue_share_pct' in df.columns:
        bad_shares = df[
            (df['revenue_share_pct'] < 0) | (df['revenue_share_pct'] > 100)
        ]
        if len(bad_shares) > 0:
            errors.append(
                f"Доли вне диапазона 0–100%: {len(bad_shares)} строк"
            )
        else:
            logger.info("✓ Доли в диапазоне 0–100%")

    # ---------------------------------------------------------------
    # Проверка 12: Сумма долей за квартал ≈ 100%
    # ---------------------------------------------------------------
    if 'revenue_share_pct' in df.columns:
        share_sums = df.groupby('fiscal_period')['revenue_share_pct'].sum()
        bad_sums = share_sums[abs(share_sums - 100) > 1.0]
        if len(bad_sums) > 0:
            warnings.append(
                f"Сумма долей отклоняется от 100% в кварталах: "
                f"{bad_sums.round(2).to_dict()}"
            )
        else:
            logger.info("✓ Суммы долей по кварталам ≈ 100%")

    # ---------------------------------------------------------------
    # Проверка 13: Разумность значений выручки (не слишком маленькие)
    # ---------------------------------------------------------------
    tiny_rev = df[df['revenue_usd_mn'] < 10]
    if len(tiny_rev) > 0:
        warnings.append(
            f"Подозрительно малые значения выручки (< $10 млн): "
            f"{len(tiny_rev)} строк — возможная ошибка масштаба"
        )

    # ---------------------------------------------------------------
    # Проверка 14: Разумность значений выручки (не слишком большие)
    # ---------------------------------------------------------------
    huge_rev = df[df['revenue_usd_mn'] > 20000]
    if len(huge_rev) > 0:
        warnings.append(
            f"Подозрительно большие значения выручки (> $20 000 млн): "
            f"{len(huge_rev)} строк — возможная ошибка масштаба"
        )

    # ---------------------------------------------------------------
    # Итоговый результат
    # ---------------------------------------------------------------
    all_messages = errors + warnings
    if errors:
        for err in errors:
            logger.error(f"ОШИБКА: {err}")
        return False, all_messages
    else:
        for warn in warnings:
            logger.warning(f"ПРЕДУПРЕЖДЕНИЕ: {warn}")
        logger.info("✓ Все проверки качества данных пройдены")
        return True, all_messages
