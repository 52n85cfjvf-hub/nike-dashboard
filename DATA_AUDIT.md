# DATA_AUDIT.md — Аудит локальных отчётов NIKE

## 1. Найденные файлы

| Файл | Финансовый год | Квартал | Тип | Конец периода |
|------|---------------|---------|-----|---------------|
| FY23Q1CombinedNIKEPressReleaseSchedulesFINAL.pdf | FY2023 | Q1 | Press Release | 31.08.2022 |
| FY23Q2CombinedNIKEPressReleaseSchedulesFINAL.pdf | FY2023 | Q2 | Press Release | 30.11.2022 |
| FY23Q3CombinedNIKEPressReleaseSchedulesFINAL.pdf | FY2023 | Q3 | Press Release | 28.02.2023 |
| FY23Q4CombinedNIKEPressReleaseSchedulesFINAL.pdf | FY2023 | Q4 | Press Release | 31.05.2023 |
| FY24Q1CombinedNIKEPressReleaseSchedulesFINAL.pdf | FY2024 | Q1 | Press Release | 31.08.2023 |
| FY24Q2CombinedSchedulesFINAL.pdf | FY2024 | Q2 | Press Release | 30.11.2023 |
| FY24Q3CombinedNIKEPressReleaseSchedulesFINAL.pdf | FY2024 | Q3 | Press Release | 29.02.2024 |
| FY24Q4CombinedNIKEPressReleaseSchedulesFINAL.pdf | FY2024 | Q4 | Press Release | 31.05.2024 |
| Q125PressReleaseFINAL.pdf | FY2025 | Q1 | Press Release | 31.08.2024 |
| Q225PressReleaseFINAL.pdf | FY2025 | Q2 | Press Release | 30.11.2024 |
| Q325PressReleaseFINAL.pdf | FY2025 | Q3 | Press Release | 28.02.2025 |
| Q4FY25_CombinedTables.pdf | FY2025 | Q4 | Press Release | 31.05.2025 |
| Q12026PressRelease93025Tables.pdf | FY2026 | Q1 | Press Release | 31.08.2025 |
| Q2FY26Exhibit991ERFINAL3397.pdf | FY2026 | Q2 | Press Release | 30.11.2025 |
| Q326PressReleaseFINAL42.pdf | FY2026 | Q3 | Press Release | 28.02.2026 |
| 414759-1-_5_Nike-NPS-Combo_Form-10-K_WR.pdf | FY2023 | Annual | 10-K | 31.05.2023 |
| 427857-1-_7_Nike-2024-Combo_Form-10-K_WR.pdf | FY2024 | Annual | 10-K | 31.05.2024 |
| Nike-Inc-2025_10K.pdf | FY2025 | Annual | 10-K | 31.05.2025 |

## 2. Структура таблицы DIVISIONAL REVENUES

Все квартальные пресс-релизы содержат таблицу **"NIKE, Inc. DIVISIONAL REVENUES"** со следующей структурой:

- Регионы: North America, Europe Middle East & Africa, Greater China, Asia Pacific & Latin America
- Продукты в каждом регионе: Footwear, Apparel, Equipment
- Показатель: Выручка за три месяца (THREE MONTHS ENDED), млн долларов США
- Сравнительный период: тот же квартал прошлого года

## 3. Покрытие периода Q1 FY2023 — Q1 FY2026

| Квартал | Статус | Источник | Метод |
|---------|--------|---------|-------|
| Q1 FY2023 | ✅ Покрыт | FY23Q1CombinedNIKEPressReleaseSchedulesFINAL.pdf | reported |
| Q2 FY2023 | ✅ Покрыт | FY23Q2CombinedNIKEPressReleaseSchedulesFINAL.pdf | reported |
| Q3 FY2023 | ✅ Покрыт | FY23Q3CombinedNIKEPressReleaseSchedulesFINAL.pdf | reported |
| Q4 FY2023 | ✅ Покрыт | FY23Q4CombinedNIKEPressReleaseSchedulesFINAL.pdf | reported |
| Q1 FY2024 | ✅ Покрыт | FY24Q1CombinedNIKEPressReleaseSchedulesFINAL.pdf | reported |
| Q2 FY2024 | ✅ Покрыт | FY24Q2CombinedSchedulesFINAL.pdf | reported |
| Q3 FY2024 | ✅ Покрыт | FY24Q3CombinedNIKEPressReleaseSchedulesFINAL.pdf | reported |
| Q4 FY2024 | ✅ Покрыт | FY24Q4CombinedNIKEPressReleaseSchedulesFINAL.pdf | reported |
| Q1 FY2025 | ✅ Покрыт | Q125PressReleaseFINAL.pdf | reported |
| Q2 FY2025 | ✅ Покрыт | Q225PressReleaseFINAL.pdf | reported |
| Q3 FY2025 | ✅ Покрыт | Q325PressReleaseFINAL.pdf | reported |
| Q4 FY2025 | ✅ Покрыт | Q4FY25_CombinedTables.pdf | reported |
| Q1 FY2026 | ✅ Покрыт | Q12026PressRelease93025Tables.pdf | reported |

**Итого: 13 из 13 кварталов покрыты напрямую из отчётов.**

## 4. Использованные таблицы

- Таблица "DIVISIONAL REVENUES" — квартальная выручка по регионам и продуктам
- Колонка "THREE MONTHS ENDED" — только квартальные данные (не накопленные)
- Все значения в миллионах долларов США

## 5. Расчётные значения

**Расчётных значений нет.** Все 156 наблюдений (13 × 3 × 4) извлечены напрямую из официальных отчётов.

## 6. Замечания

- PDF-файлы содержат сканированные страницы (тип block=1 в PyMuPDF), поэтому текстовый слой недоступен
- Данные извлечены визуальной инспекцией рендеренных страниц и закодированы вручную
- Каждая цифра верифицирована перекрёстной проверкой со строкой "Total" в соответствующей таблице
- Converse исключён из анализа согласно требованиям задания
- Global Brand Divisions исключены (не входят ни в один регион)
- 10-K годовые отчёты использованы только для перекрёстной проверки (annualized data)

## 7. Отсутствующие данные

Отсутствующих данных нет. Все 13 кварталов × 3 продукта × 4 региона = 156 наблюдений доступны.
