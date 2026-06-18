"""
Модуль прогнозирования квартальных продаж NIKE.

Реализует прогнозирование для каждого из 12 направлений (3 × 4)
с использованием модели Holt-Winters (ExponentialSmoothing) с учётом
квартальной сезонности (период = 4).

Резервный метод: сезонный наивный прогноз (значение того же квартала год назад).
Все прогнозы выполняются в рамках Python без интернет-запросов.
"""

import pandas as pd
import numpy as np
import logging
from typing import Tuple, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# Горизонт прогноза — 4 квартала вперёд
FORECAST_HORIZON = 4

# Сезонный период — 4 квартала
SEASONAL_PERIOD = 4

# Минимальное число наблюдений для обучения Holt-Winters
MIN_OBS_FOR_HW = 8


def forecast_series(
    series: pd.Series,
    horizon: int = FORECAST_HORIZON,
    series_name: str = ""
) -> Tuple[pd.Series, str, float, Optional[float]]:
    """
    Прогнозирует временной ряд моделью Holt-Winters или сезонным наивным методом.

    Перед обучением проверяет длину ряда, наличие пропусков,
    положительность значений. При ошибке использует резервный метод.

    Не добавляет сезонный индекс поверх модели — Holt-Winters уже
    содержит сезонную компоненту.

    Args:
        series: Временной ряд выручки (квартальные значения).
        horizon: Горизонт прогноза (число кварталов).
        series_name: Название ряда для логирования.

    Returns:
        Tuple:
            - pd.Series: Прогнозные значения (горизонт наблюдений)
            - str: Название использованного метода
            - float: MAE на тестовой выборке
            - Optional[float]: MAPE на тестовой выборке (если применимо)
    """
    from statsmodels.tsa.holtwinters import ExponentialSmoothing

    series = series.dropna()
    n = len(series)
    method_used = "Holt-Winters"
    mae = np.nan
    mape = None

    # ---------------------------------------------------------------
    # Проверка минимального числа наблюдений
    # ---------------------------------------------------------------
    if n < MIN_OBS_FOR_HW:
        logger.warning(
            f"{series_name}: Мало наблюдений ({n}), использую сезонный наивный метод"
        )
        return _seasonal_naive_forecast(series, horizon), "Сезонный наивный", mae, mape

    # ---------------------------------------------------------------
    # Проверка положительности значений (Holt-Winters требует > 0)
    # ---------------------------------------------------------------
    if (series <= 0).any():
        logger.warning(
            f"{series_name}: Неположительные значения, использую сезонный наивный метод"
        )
        return _seasonal_naive_forecast(series, horizon), "Сезонный наивный", mae, mape

    # ---------------------------------------------------------------
    # Простая проверка модели: исключаем последние 4 квартала
    # и сравниваем прогноз с фактом
    # ---------------------------------------------------------------
    try:
        if n >= MIN_OBS_FOR_HW + SEASONAL_PERIOD:
            train = series.iloc[:-SEASONAL_PERIOD]
            test = series.iloc[-SEASONAL_PERIOD:]

            # Обучаем HW на тренировочной выборке
            hw_model = ExponentialSmoothing(
                train,
                trend="add",
                seasonal="add",
                seasonal_periods=SEASONAL_PERIOD,
                initialization_method="estimated"
            ).fit(optimized=True)

            hw_pred = hw_model.forecast(SEASONAL_PERIOD)

            # Также сравниваем с сезонным наивным методом
            naive_pred = _seasonal_naive_forecast(train, SEASONAL_PERIOD)

            # Рассчитываем MAE для обоих методов
            mae_hw = float(np.mean(np.abs(hw_pred.values - test.values)))
            mae_naive = float(np.mean(np.abs(naive_pred.values - test.values)))

            # Выбираем лучший метод
            if mae_hw <= mae_naive:
                method_used = "Holt-Winters"
                mae = mae_hw
                # MAPE (только если нет нулей в тесте)
                if (test != 0).all():
                    mape = float(np.mean(np.abs((hw_pred.values - test.values) / test.values)) * 100)
            else:
                logger.info(
                    f"{series_name}: Сезонный наивный метод лучше HW "
                    f"(MAE: {mae_naive:.1f} < {mae_hw:.1f})"
                )
                method_used = "Сезонный наивный"
                mae = mae_naive
        else:
            method_used = "Holt-Winters"

    except Exception as e:
        logger.warning(f"{series_name}: Ошибка в проверке модели: {e}")
        method_used = "Holt-Winters"

    # ---------------------------------------------------------------
    # Итоговое обучение на всех доступных данных и прогноз
    # ---------------------------------------------------------------
    if method_used == "Holt-Winters":
        try:
            final_model = ExponentialSmoothing(
                series,
                trend="add",
                seasonal="add",
                seasonal_periods=SEASONAL_PERIOD,
                initialization_method="estimated"
            ).fit(optimized=True)

            forecast = final_model.forecast(horizon)
            # Не допускаем отрицательных прогнозов
            forecast = forecast.clip(lower=0)
            logger.info(f"{series_name}: Прогноз Holt-Winters, MAE={mae:.1f}")

        except Exception as e:
            logger.warning(
                f"{series_name}: Holt-Winters не удался ({e}), "
                f"перехожу к сезонному наивному методу"
            )
            method_used = "Сезонный наивный"
            forecast = _seasonal_naive_forecast(series, horizon)

    else:
        forecast = _seasonal_naive_forecast(series, horizon)

    return forecast, method_used, mae, mape


def _seasonal_naive_forecast(series: pd.Series, horizon: int) -> pd.Series:
    """
    Сезонный наивный прогноз: прогноз = факт того же квартала год назад.

    Прогноз Q(t) = факт Q(t - 4). Сохраняет квартальную сезонность.

    Args:
        series: Исторические данные.
        horizon: Горизонт прогноза.

    Returns:
        pd.Series: Прогнозные значения.
    """
    n = len(series)
    forecast_values = []

    for h in range(1, horizon + 1):
        # Индекс соответствующего квартала год назад
        lag_idx = n - SEASONAL_PERIOD + (h - 1)
        if lag_idx >= 0 and lag_idx < n:
            forecast_values.append(series.iloc[lag_idx])
        elif n > 0:
            # Если нет данных за год назад, берём последнее значение
            forecast_values.append(series.iloc[-1])
        else:
            forecast_values.append(np.nan)

    # Создаём индекс, продолжающий ряд
    if isinstance(series.index, pd.RangeIndex):
        new_index = range(n, n + horizon)
    else:
        new_index = range(n, n + horizon)

    return pd.Series(forecast_values, index=new_index)


def build_all_forecasts(
    df: pd.DataFrame,
    end_period: str,
    horizon: int = FORECAST_HORIZON
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Строит прогнозы для всех 12 направлений (3 × 4).

    Для каждого сочетания продукт × регион:
    1. Извлекает квартальный ряд выручки (в хронологическом порядке)
    2. Обучает модель на данных от Q1 FY2023 до выбранного конечного квартала
    3. Прогнозирует следующие 4 квартала
    4. Записывает диагностику модели

    Args:
        df: Полный датасет.
        end_period: Конечный квартал для обучения (например, "Q1 FY2026").
        horizon: Горизонт прогноза.

    Returns:
        Tuple:
            - pd.DataFrame: Прогнозные данные (168 строк = 12 × 14 периодов)
            - pd.DataFrame: Диагностика моделей (12 строк)
    """
    logger.info(f"Построение прогнозов для {end_period}...")

    # Определяем конечный period_order для обучения
    period_order_map = (df[['fiscal_period', 'period_order']]
                       .drop_duplicates()
                       .set_index('fiscal_period')['period_order'])

    if end_period not in period_order_map.index:
        logger.error(f"Период {end_period} не найден в данных")
        return pd.DataFrame(), pd.DataFrame()

    end_order = period_order_map[end_period]
    last_order = end_order  # последний фактический квартал

    # Генерируем метки будущих кварталов
    future_periods = _generate_future_periods(end_period, horizon)

    all_forecasts = []
    diagnostics = []

    products = df['product'].unique()
    regions = df['region'].unique()

    for product in products:
        for region in regions:
            # Извлекаем ряд для конкретного направления
            mask = (
                (df['product'] == product) &
                (df['region'] == region) &
                (df['period_order'] <= end_order)
            )
            series_df = df[mask].sort_values('period_order')
            series = series_df['revenue_usd_mn']

            if len(series) < 2:
                logger.warning(f"Мало данных для {product} × {region}")
                continue

            # Прогнозируем
            forecast, method, mae, mape = forecast_series(
                series, horizon=horizon,
                series_name=f"{product} × {region}"
            )

            # Записываем фактические данные
            for _, row in series_df.iterrows():
                all_forecasts.append({
                    'product': product,
                    'product_ru': row['product_ru'],
                    'region': region,
                    'region_ru': row['region_ru'],
                    'fiscal_period': row['fiscal_period'],
                    'period_label_ru': row.get('period_label_ru', row['fiscal_period']),
                    'period_order': row['period_order'],
                    'revenue_usd_mn': row['revenue_usd_mn'],
                    'is_forecast': False,
                    'forecast_method': method,
                })

            # Записываем прогнозные данные
            for i, (fp, fp_label) in enumerate(future_periods):
                forecast_val = float(forecast.iloc[i]) if i < len(forecast) else np.nan
                all_forecasts.append({
                    'product': product,
                    'product_ru': series_df['product_ru'].iloc[0],
                    'region': region,
                    'region_ru': series_df['region_ru'].iloc[0],
                    'fiscal_period': fp,
                    'period_label_ru': fp_label,
                    'period_order': last_order + i + 1,
                    'revenue_usd_mn': max(0, forecast_val) if not np.isnan(forecast_val) else 0,
                    'is_forecast': True,
                    'forecast_method': method,
                })

            # Диагностика
            diagnostics.append({
                'product': product,
                'region': region,
                'forecast_method': method,
                'mae': round(mae, 2) if not np.isnan(mae) else None,
                'mape_pct': round(mape, 2) if mape is not None else None,
                'n_train_obs': len(series),
                'end_train_period': end_period,
            })

    forecast_df = pd.DataFrame(all_forecasts)
    diag_df = pd.DataFrame(diagnostics)

    logger.info(
        f"Прогнозы построены: {len(forecast_df)} строк, "
        f"{len(diag_df)} направлений"
    )
    return forecast_df, diag_df


def _generate_future_periods(
    last_period: str,
    horizon: int
) -> list[Tuple[str, str]]:
    """
    Генерирует метки будущих кварталов после последнего фактического.

    Args:
        last_period: Последний фактический период (например, "Q1 FY2026").
        horizon: Количество будущих кварталов.

    Returns:
        list[Tuple[str, str]]: Список (технический код, русская метка).
    """
    from src.data_loader import QUARTER_LABELS_RU

    # Парсим последний период
    parts = last_period.split(' ')
    q_num = int(parts[0][1])  # Q1 → 1
    fy = int(parts[1][2:])    # FY2026 → 2026

    future = []
    for _ in range(horizon):
        q_num += 1
        if q_num > 4:
            q_num = 1
            fy += 1
        code = f"Q{q_num} FY{fy}"
        label = QUARTER_LABELS_RU.get(code, code)
        future.append((code, label))

    return future


def get_aggregated_forecast(
    forecast_df: pd.DataFrame,
    products: list[str],
    regions: list[str],
    full_products: list[str],
    full_regions: list[str]
) -> pd.DataFrame:
    """
    Агрегирует прогнозы выбранного среза и рассчитывает прогнозную долю.

    Прогноз выбранной выручки = сумма прогнозов выбранных направлений.
    Прогноз доли = прогноз выбранной выручки / прогноз общей выручки × 100.

    Args:
        forecast_df: Датасет со всеми прогнозами (12 направлений).
        products: Выбранные продукты (английские названия).
        regions: Выбранные регионы (английские названия).
        full_products: Все продукты (для знаменателя доли).
        full_regions: Все регионы (для знаменателя доли).

    Returns:
        pd.DataFrame: Агрегированные прогнозы с выручкой и долей.
    """
    if forecast_df.empty:
        return pd.DataFrame()

    # Прогноз выбранной выручки
    mask_selected = (
        forecast_df['product'].isin(products) &
        forecast_df['region'].isin(regions)
    )
    selected_agg = (forecast_df[mask_selected]
                    .groupby(['fiscal_period', 'period_label_ru',
                              'period_order', 'is_forecast'])
                    ['revenue_usd_mn']
                    .sum()
                    .reset_index()
                    .rename(columns={'revenue_usd_mn': 'selected_revenue'}))

    # Прогноз общей анализируемой выручки (все 12 направлений)
    mask_total = (
        forecast_df['product'].isin(full_products) &
        forecast_df['region'].isin(full_regions)
    )
    total_agg = (forecast_df[mask_total]
                 .groupby(['fiscal_period', 'period_order', 'is_forecast'])
                 ['revenue_usd_mn']
                 .sum()
                 .reset_index()
                 .rename(columns={'revenue_usd_mn': 'total_revenue'}))

    # Объединяем
    result = selected_agg.merge(
        total_agg[['fiscal_period', 'period_order', 'total_revenue']],
        on=['fiscal_period', 'period_order'],
        how='left'
    )

    # Рассчитываем прогнозную долю
    result['selected_share_pct'] = (
        result['selected_revenue'] / result['total_revenue'] * 100
    ).clip(0, 100).round(2)

    result = result.sort_values('period_order').reset_index(drop=True)

    return result


def save_diagnostics(df: pd.DataFrame, output_dir: str = 'data/processed') -> None:
    """
    Сохраняет диагностику прогнозных моделей в CSV.

    Args:
        df: Диагностический датасет.
        output_dir: Путь к директории вывода.
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    path = f"{output_dir}/forecast_diagnostics.csv"
    df.to_csv(path, index=False)
    logger.info(f"Диагностика моделей сохранена: {path}")
