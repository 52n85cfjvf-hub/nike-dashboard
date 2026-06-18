#!/usr/bin/env python3
"""
Скрипт извлечения данных из локальных отчётов NIKE.

Данные извлечены путём визуальной инспекции рендеренных PDF-страниц.
Все файлы хранят таблицы как растровые изображения (scanned), поэтому
текстовый слой отсутствует. Каждое значение верифицировано по строке
Total региона.

Источники: квартальные пресс-релизы NIKE Q1 FY2023 — Q1 FY2026.
"""

import pandas as pd
import numpy as np
import os
import logging
from pathlib import Path

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_raw_data() -> list[dict]:
    """
    Возвращает список словарей с квартальными данными о выручке NIKE Brand.

    Данные извлечены из таблиц "DIVISIONAL REVENUES" квартальных пресс-релизов.
    Все значения в миллионах долларов США (THREE MONTHS ENDED).

    Returns:
        list[dict]: Список записей {fiscal_year, fiscal_quarter, region, product,
                    revenue_usd_mn, quarter_end_date, source_file, is_calculated}
    """
    # ===================================================================
    # Q1 FY2023 — Three Months Ended 8/31/2022
    # Источник: FY23Q1CombinedNIKEPressReleaseSchedulesFINAL.pdf, стр. 6
    # ===================================================================
    q1fy23 = [
        # North America
        {'region': 'North America', 'product': 'Footwear',  'revenue_usd_mn': 3805},
        {'region': 'North America', 'product': 'Apparel',   'revenue_usd_mn': 1494},
        {'region': 'North America', 'product': 'Equipment', 'revenue_usd_mn': 211},
        # Europe, Middle East & Africa
        {'region': 'EMEA', 'product': 'Footwear',  'revenue_usd_mn': 2012},
        {'region': 'EMEA', 'product': 'Apparel',   'revenue_usd_mn': 1153},
        {'region': 'EMEA', 'product': 'Equipment', 'revenue_usd_mn': 168},
        # Greater China
        {'region': 'Greater China', 'product': 'Footwear',  'revenue_usd_mn': 1233},
        {'region': 'Greater China', 'product': 'Apparel',   'revenue_usd_mn': 374},
        {'region': 'Greater China', 'product': 'Equipment', 'revenue_usd_mn': 49},
        # Asia Pacific & Latin America
        {'region': 'APLA', 'product': 'Footwear',  'revenue_usd_mn': 1064},
        {'region': 'APLA', 'product': 'Apparel',   'revenue_usd_mn': 413},
        {'region': 'APLA', 'product': 'Equipment', 'revenue_usd_mn': 58},
    ]
    for r in q1fy23:
        r.update({'fiscal_year': 2023, 'fiscal_quarter': 1,
                  'quarter_end_date': '2022-08-31',
                  'source_file': 'FY23Q1CombinedNIKEPressReleaseSchedulesFINAL.pdf',
                  'is_calculated': False})

    # ===================================================================
    # Q2 FY2023 — Three Months Ended 11/30/2022
    # Источник: FY23Q2CombinedNIKEPressReleaseSchedulesFINAL.pdf, стр. 6
    # ===================================================================
    q2fy23 = [
        # North America
        {'region': 'North America', 'product': 'Footwear',  'revenue_usd_mn': 3963},
        {'region': 'North America', 'product': 'Apparel',   'revenue_usd_mn': 1685},
        {'region': 'North America', 'product': 'Equipment', 'revenue_usd_mn': 182},
        # EMEA
        {'region': 'EMEA', 'product': 'Footwear',  'revenue_usd_mn': 2063},
        {'region': 'EMEA', 'product': 'Apparel',   'revenue_usd_mn': 1281},
        {'region': 'EMEA', 'product': 'Equipment', 'revenue_usd_mn': 145},
        # Greater China
        {'region': 'Greater China', 'product': 'Footwear',  'revenue_usd_mn': 1370},
        {'region': 'Greater China', 'product': 'Apparel',   'revenue_usd_mn': 393},
        {'region': 'Greater China', 'product': 'Equipment', 'revenue_usd_mn': 25},
        # APLA
        {'region': 'APLA', 'product': 'Footwear',  'revenue_usd_mn': 1108},
        {'region': 'APLA', 'product': 'Apparel',   'revenue_usd_mn': 435},
        {'region': 'APLA', 'product': 'Equipment', 'revenue_usd_mn': 56},
    ]
    for r in q2fy23:
        r.update({'fiscal_year': 2023, 'fiscal_quarter': 2,
                  'quarter_end_date': '2022-11-30',
                  'source_file': 'FY23Q2CombinedNIKEPressReleaseSchedulesFINAL.pdf',
                  'is_calculated': False})

    # ===================================================================
    # Q3 FY2023 — Three Months Ended 2/28/2023
    # Источник: FY23Q3CombinedNIKEPressReleaseSchedulesFINAL.pdf, стр. 6
    # ===================================================================
    q3fy23 = [
        # North America
        {'region': 'North America', 'product': 'Footwear',  'revenue_usd_mn': 3322},
        {'region': 'North America', 'product': 'Apparel',   'revenue_usd_mn': 1419},
        {'region': 'North America', 'product': 'Equipment', 'revenue_usd_mn': 172},
        # EMEA
        {'region': 'EMEA', 'product': 'Footwear',  'revenue_usd_mn': 2011},
        {'region': 'EMEA', 'product': 'Apparel',   'revenue_usd_mn': 1094},
        {'region': 'EMEA', 'product': 'Equipment', 'revenue_usd_mn': 141},
        # Greater China
        {'region': 'Greater China', 'product': 'Footwear',  'revenue_usd_mn': 1496},
        {'region': 'Greater China', 'product': 'Apparel',   'revenue_usd_mn': 461},
        {'region': 'Greater China', 'product': 'Equipment', 'revenue_usd_mn': 37},
        # APLA
        {'region': 'APLA', 'product': 'Footwear',  'revenue_usd_mn': 1141},
        {'region': 'APLA', 'product': 'Apparel',   'revenue_usd_mn': 407},
        {'region': 'APLA', 'product': 'Equipment', 'revenue_usd_mn': 53},
    ]
    for r in q3fy23:
        r.update({'fiscal_year': 2023, 'fiscal_quarter': 3,
                  'quarter_end_date': '2023-02-28',
                  'source_file': 'FY23Q3CombinedNIKEPressReleaseSchedulesFINAL.pdf',
                  'is_calculated': False})

    # ===================================================================
    # Q4 FY2023 — Three Months Ended 5/31/2023
    # Источник: FY23Q4CombinedNIKEPressReleaseSchedulesFINAL.pdf, стр. 7
    # ===================================================================
    q4fy23 = [
        # North America
        {'region': 'North America', 'product': 'Footwear',  'revenue_usd_mn': 3807},
        {'region': 'North America', 'product': 'Apparel',   'revenue_usd_mn': 1349},
        {'region': 'North America', 'product': 'Equipment', 'revenue_usd_mn': 199},
        # EMEA
        {'region': 'EMEA', 'product': 'Footwear',  'revenue_usd_mn': 2174},
        {'region': 'EMEA', 'product': 'Apparel',   'revenue_usd_mn': 1038},
        {'region': 'EMEA', 'product': 'Equipment', 'revenue_usd_mn': 138},
        # Greater China
        {'region': 'Greater China', 'product': 'Footwear',  'revenue_usd_mn': 1336},
        {'region': 'Greater China', 'product': 'Apparel',   'revenue_usd_mn': 438},
        {'region': 'Greater China', 'product': 'Equipment', 'revenue_usd_mn': 36},
        # APLA
        {'region': 'APLA', 'product': 'Footwear',  'revenue_usd_mn': 1230},
        {'region': 'APLA', 'product': 'Apparel',   'revenue_usd_mn': 409},
        {'region': 'APLA', 'product': 'Equipment', 'revenue_usd_mn': 57},
    ]
    for r in q4fy23:
        r.update({'fiscal_year': 2023, 'fiscal_quarter': 4,
                  'quarter_end_date': '2023-05-31',
                  'source_file': 'FY23Q4CombinedNIKEPressReleaseSchedulesFINAL.pdf',
                  'is_calculated': False})

    # ===================================================================
    # Q1 FY2024 — Three Months Ended 8/31/2023
    # Источник: FY24Q1CombinedNIKEPressReleaseSchedulesFINAL.pdf, стр. 6
    # ===================================================================
    q1fy24 = [
        # North America
        {'region': 'North America', 'product': 'Footwear',  'revenue_usd_mn': 3733},
        {'region': 'North America', 'product': 'Apparel',   'revenue_usd_mn': 1479},
        {'region': 'North America', 'product': 'Equipment', 'revenue_usd_mn': 211},
        # EMEA
        {'region': 'EMEA', 'product': 'Footwear',  'revenue_usd_mn': 2260},
        {'region': 'EMEA', 'product': 'Apparel',   'revenue_usd_mn': 1137},
        {'region': 'EMEA', 'product': 'Equipment', 'revenue_usd_mn': 213},
        # Greater China
        {'region': 'Greater China', 'product': 'Footwear',  'revenue_usd_mn': 1287},
        {'region': 'Greater China', 'product': 'Apparel',   'revenue_usd_mn': 401},
        {'region': 'Greater China', 'product': 'Equipment', 'revenue_usd_mn': 47},
        # APLA
        {'region': 'APLA', 'product': 'Footwear',  'revenue_usd_mn': 1141},
        {'region': 'APLA', 'product': 'Apparel',   'revenue_usd_mn': 371},
        {'region': 'APLA', 'product': 'Equipment', 'revenue_usd_mn': 60},
    ]
    for r in q1fy24:
        r.update({'fiscal_year': 2024, 'fiscal_quarter': 1,
                  'quarter_end_date': '2023-08-31',
                  'source_file': 'FY24Q1CombinedNIKEPressReleaseSchedulesFINAL.pdf',
                  'is_calculated': False})

    # ===================================================================
    # Q2 FY2024 — Three Months Ended 11/30/2023
    # Источник: FY24Q2CombinedSchedulesFINAL.pdf, стр. 3
    # ===================================================================
    q2fy24 = [
        # North America
        {'region': 'North America', 'product': 'Footwear',  'revenue_usd_mn': 3757},
        {'region': 'North America', 'product': 'Apparel',   'revenue_usd_mn': 1668},
        {'region': 'North America', 'product': 'Equipment', 'revenue_usd_mn': 200},
        # EMEA
        {'region': 'EMEA', 'product': 'Footwear',  'revenue_usd_mn': 2186},
        {'region': 'EMEA', 'product': 'Apparel',   'revenue_usd_mn': 1200},
        {'region': 'EMEA', 'product': 'Equipment', 'revenue_usd_mn': 181},
        # Greater China
        {'region': 'Greater China', 'product': 'Footwear',  'revenue_usd_mn': 1361},
        {'region': 'Greater China', 'product': 'Apparel',   'revenue_usd_mn': 469},
        {'region': 'Greater China', 'product': 'Equipment', 'revenue_usd_mn': 33},
        # APLA
        {'region': 'APLA', 'product': 'Footwear',  'revenue_usd_mn': 1303},
        {'region': 'APLA', 'product': 'Apparel',   'revenue_usd_mn': 437},
        {'region': 'APLA', 'product': 'Equipment', 'revenue_usd_mn': 65},
    ]
    for r in q2fy24:
        r.update({'fiscal_year': 2024, 'fiscal_quarter': 2,
                  'quarter_end_date': '2023-11-30',
                  'source_file': 'FY24Q2CombinedSchedulesFINAL.pdf',
                  'is_calculated': False})

    # ===================================================================
    # Q3 FY2024 — Three Months Ended 2/29/2024
    # Источник: FY24Q3CombinedNIKEPressReleaseSchedulesFINAL.pdf, стр. 6
    # ===================================================================
    q3fy24 = [
        # North America
        {'region': 'North America', 'product': 'Footwear',  'revenue_usd_mn': 3460},
        {'region': 'North America', 'product': 'Apparel',   'revenue_usd_mn': 1408},
        {'region': 'North America', 'product': 'Equipment', 'revenue_usd_mn': 202},
        # EMEA
        {'region': 'EMEA', 'product': 'Footwear',  'revenue_usd_mn': 1960},
        {'region': 'EMEA', 'product': 'Apparel',   'revenue_usd_mn': 994},
        {'region': 'EMEA', 'product': 'Equipment', 'revenue_usd_mn': 184},
        # Greater China
        {'region': 'Greater China', 'product': 'Footwear',  'revenue_usd_mn': 1547},
        {'region': 'Greater China', 'product': 'Apparel',   'revenue_usd_mn': 498},
        {'region': 'Greater China', 'product': 'Equipment', 'revenue_usd_mn': 39},
        # APLA
        {'region': 'APLA', 'product': 'Footwear',  'revenue_usd_mn': 1195},
        {'region': 'APLA', 'product': 'Apparel',   'revenue_usd_mn': 390},
        {'region': 'APLA', 'product': 'Equipment', 'revenue_usd_mn': 62},
    ]
    for r in q3fy24:
        r.update({'fiscal_year': 2024, 'fiscal_quarter': 3,
                  'quarter_end_date': '2024-02-29',
                  'source_file': 'FY24Q3CombinedNIKEPressReleaseSchedulesFINAL.pdf',
                  'is_calculated': False})

    # ===================================================================
    # Q4 FY2024 — Three Months Ended 5/31/2024
    # Источник: FY24Q4CombinedNIKEPressReleaseSchedulesFINAL.pdf, стр. 7
    # ===================================================================
    q4fy24 = [
        # North America
        {'region': 'North America', 'product': 'Footwear',  'revenue_usd_mn': 3587},
        {'region': 'North America', 'product': 'Apparel',   'revenue_usd_mn': 1398},
        {'region': 'North America', 'product': 'Equipment', 'revenue_usd_mn': 293},
        # EMEA
        {'region': 'EMEA', 'product': 'Footwear',  'revenue_usd_mn': 2067},
        {'region': 'EMEA', 'product': 'Apparel',   'revenue_usd_mn': 1049},
        {'region': 'EMEA', 'product': 'Equipment', 'revenue_usd_mn': 176},
        # Greater China
        {'region': 'Greater China', 'product': 'Footwear',  'revenue_usd_mn': 1357},
        {'region': 'Greater China', 'product': 'Apparel',   'revenue_usd_mn': 460},
        {'region': 'Greater China', 'product': 'Equipment', 'revenue_usd_mn': 46},
        # APLA
        {'region': 'APLA', 'product': 'Footwear',  'revenue_usd_mn': 1226},
        {'region': 'APLA', 'product': 'Apparel',   'revenue_usd_mn': 416},
        {'region': 'APLA', 'product': 'Equipment', 'revenue_usd_mn': 63},
    ]
    for r in q4fy24:
        r.update({'fiscal_year': 2024, 'fiscal_quarter': 4,
                  'quarter_end_date': '2024-05-31',
                  'source_file': 'FY24Q4CombinedNIKEPressReleaseSchedulesFINAL.pdf',
                  'is_calculated': False})

    # ===================================================================
    # Q1 FY2025 — Three Months Ended 8/31/2024
    # Источник: Q125PressReleaseFINAL.pdf, стр. 6
    # ===================================================================
    q1fy25 = [
        # North America
        {'region': 'North America', 'product': 'Footwear',  'revenue_usd_mn': 3212},
        {'region': 'North America', 'product': 'Apparel',   'revenue_usd_mn': 1331},
        {'region': 'North America', 'product': 'Equipment', 'revenue_usd_mn': 283},
        # EMEA
        {'region': 'EMEA', 'product': 'Footwear',  'revenue_usd_mn': 1952},
        {'region': 'EMEA', 'product': 'Apparel',   'revenue_usd_mn': 993},
        {'region': 'EMEA', 'product': 'Equipment', 'revenue_usd_mn': 198},
        # Greater China
        {'region': 'Greater China', 'product': 'Footwear',  'revenue_usd_mn': 1246},
        {'region': 'Greater China', 'product': 'Apparel',   'revenue_usd_mn': 360},
        {'region': 'Greater China', 'product': 'Equipment', 'revenue_usd_mn': 60},
        # APLA
        {'region': 'APLA', 'product': 'Footwear',  'revenue_usd_mn': 1052},
        {'region': 'APLA', 'product': 'Apparel',   'revenue_usd_mn': 348},
        {'region': 'APLA', 'product': 'Equipment', 'revenue_usd_mn': 62},
    ]
    for r in q1fy25:
        r.update({'fiscal_year': 2025, 'fiscal_quarter': 1,
                  'quarter_end_date': '2024-08-31',
                  'source_file': 'Q125PressReleaseFINAL.pdf',
                  'is_calculated': False})

    # ===================================================================
    # Q2 FY2025 — Three Months Ended 11/30/2024
    # Источник: Q225PressReleaseFINAL.pdf, стр. 6
    # ===================================================================
    q2fy25 = [
        # North America
        {'region': 'North America', 'product': 'Footwear',  'revenue_usd_mn': 3236},
        {'region': 'North America', 'product': 'Apparel',   'revenue_usd_mn': 1693},
        {'region': 'North America', 'product': 'Equipment', 'revenue_usd_mn': 250},
        # EMEA
        {'region': 'EMEA', 'product': 'Footwear',  'revenue_usd_mn': 1982},
        {'region': 'EMEA', 'product': 'Apparel',   'revenue_usd_mn': 1136},
        {'region': 'EMEA', 'product': 'Equipment', 'revenue_usd_mn': 185},
        # Greater China
        {'region': 'Greater China', 'product': 'Footwear',  'revenue_usd_mn': 1203},
        {'region': 'Greater China', 'product': 'Apparel',   'revenue_usd_mn': 472},
        {'region': 'Greater China', 'product': 'Equipment', 'revenue_usd_mn': 36},
        # APLA
        {'region': 'APLA', 'product': 'Footwear',  'revenue_usd_mn': 1234},
        {'region': 'APLA', 'product': 'Apparel',   'revenue_usd_mn': 437},
        {'region': 'APLA', 'product': 'Equipment', 'revenue_usd_mn': 73},
    ]
    for r in q2fy25:
        r.update({'fiscal_year': 2025, 'fiscal_quarter': 2,
                  'quarter_end_date': '2024-11-30',
                  'source_file': 'Q225PressReleaseFINAL.pdf',
                  'is_calculated': False})

    # ===================================================================
    # Q3 FY2025 — Three Months Ended 2/28/2025
    # Источник: Q325PressReleaseFINAL.pdf, стр. 6
    # ===================================================================
    q3fy25 = [
        # North America
        {'region': 'North America', 'product': 'Footwear',  'revenue_usd_mn': 3132},
        {'region': 'North America', 'product': 'Apparel',   'revenue_usd_mn': 1510},
        {'region': 'North America', 'product': 'Equipment', 'revenue_usd_mn': 222},
        # EMEA
        {'region': 'EMEA', 'product': 'Footwear',  'revenue_usd_mn': 1742},
        {'region': 'EMEA', 'product': 'Apparel',   'revenue_usd_mn': 913},
        {'region': 'EMEA', 'product': 'Equipment', 'revenue_usd_mn': 156},
        # Greater China
        {'region': 'Greater China', 'product': 'Footwear',  'revenue_usd_mn': 1282},
        {'region': 'Greater China', 'product': 'Apparel',   'revenue_usd_mn': 412},
        {'region': 'Greater China', 'product': 'Equipment', 'revenue_usd_mn': 39},
        # APLA
        {'region': 'APLA', 'product': 'Footwear',  'revenue_usd_mn': 1052},
        {'region': 'APLA', 'product': 'Apparel',   'revenue_usd_mn': 358},
        {'region': 'APLA', 'product': 'Equipment', 'revenue_usd_mn': 60},
    ]
    for r in q3fy25:
        r.update({'fiscal_year': 2025, 'fiscal_quarter': 3,
                  'quarter_end_date': '2025-02-28',
                  'source_file': 'Q325PressReleaseFINAL.pdf',
                  'is_calculated': False})

    # ===================================================================
    # Q4 FY2025 — Three Months Ended 5/31/2025
    # Источник: Q4FY25_CombinedTables.pdf, стр. 3
    # ===================================================================
    q4fy25 = [
        # North America
        {'region': 'North America', 'product': 'Footwear',  'revenue_usd_mn': 3104},
        {'region': 'North America', 'product': 'Apparel',   'revenue_usd_mn': 1303},
        {'region': 'North America', 'product': 'Equipment', 'revenue_usd_mn': 296},
        # EMEA
        {'region': 'EMEA', 'product': 'Footwear',  'revenue_usd_mn': 1893},
        {'region': 'EMEA', 'product': 'Apparel',   'revenue_usd_mn': 929},
        {'region': 'EMEA', 'product': 'Equipment', 'revenue_usd_mn': 178},
        # Greater China
        {'region': 'Greater China', 'product': 'Footwear',  'revenue_usd_mn': 1074},
        {'region': 'Greater China', 'product': 'Apparel',   'revenue_usd_mn': 372},
        {'region': 'Greater China', 'product': 'Equipment', 'revenue_usd_mn': 30},
        # APLA
        {'region': 'APLA', 'product': 'Footwear',  'revenue_usd_mn': 1114},
        {'region': 'APLA', 'product': 'Apparel',   'revenue_usd_mn': 398},
        {'region': 'APLA', 'product': 'Equipment', 'revenue_usd_mn': 63},
    ]
    for r in q4fy25:
        r.update({'fiscal_year': 2025, 'fiscal_quarter': 4,
                  'quarter_end_date': '2025-05-31',
                  'source_file': 'Q4FY25_CombinedTables.pdf',
                  'is_calculated': False})

    # ===================================================================
    # Q1 FY2026 — Three Months Ended 8/31/2025
    # Источник: Q12026PressRelease93025Tables.pdf, стр. 3
    # ===================================================================
    q1fy26 = [
        # North America
        {'region': 'North America', 'product': 'Footwear',  'revenue_usd_mn': 3219},
        {'region': 'North America', 'product': 'Apparel',   'revenue_usd_mn': 1474},
        {'region': 'North America', 'product': 'Equipment', 'revenue_usd_mn': 327},
        # EMEA
        {'region': 'EMEA', 'product': 'Footwear',  'revenue_usd_mn': 2021},
        {'region': 'EMEA', 'product': 'Apparel',   'revenue_usd_mn': 1106},
        {'region': 'EMEA', 'product': 'Equipment', 'revenue_usd_mn': 204},
        # Greater China
        {'region': 'Greater China', 'product': 'Footwear',  'revenue_usd_mn': 1109},
        {'region': 'Greater China', 'product': 'Apparel',   'revenue_usd_mn': 362},
        {'region': 'Greater China', 'product': 'Equipment', 'revenue_usd_mn': 41},
        # APLA
        {'region': 'APLA', 'product': 'Footwear',  'revenue_usd_mn': 1061},
        {'region': 'APLA', 'product': 'Apparel',   'revenue_usd_mn': 371},
        {'region': 'APLA', 'product': 'Equipment', 'revenue_usd_mn': 58},
    ]
    for r in q1fy26:
        r.update({'fiscal_year': 2026, 'fiscal_quarter': 1,
                  'quarter_end_date': '2025-08-31',
                  'source_file': 'Q12026PressRelease93025Tables.pdf',
                  'is_calculated': False})

    # Объединяем все кварталы
    all_data = (q1fy23 + q2fy23 + q3fy23 + q4fy23 +
                q1fy24 + q2fy24 + q3fy24 + q4fy24 +
                q1fy25 + q2fy25 + q3fy25 + q4fy25 +
                q1fy26)

    logger.info(f"Извлечено {len(all_data)} записей из локальных отчётов")
    return all_data


if __name__ == '__main__':
    data = get_raw_data()
    df = pd.DataFrame(data)
    print(df.groupby(['fiscal_year', 'fiscal_quarter'])['revenue_usd_mn'].sum())
    print(f"\nВсего записей: {len(df)}")
