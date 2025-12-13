# claims/modules/forecast/statistical.py
"""
Модуль методов статистическего анализа.

Включает класс:
- `StatisticalForecast` - Статистические методы прогнозирования
"""

import numpy as np
from .base import BaseForecast


class StatisticalForecast(BaseForecast):
    """
    Статистические методы прогнозирования

    Метод: Скользящее среднее + Линейный тренд + Затухание

    Режимы:
    - conservative: Консервативный (сглаживание, медленная реакция)
    - balanced: Сбалансированный (универсальный, по умолчанию)
    - aggressive: Агрессивный (быстрая реакция на тренд)
    """

    # Параметры для разных режимов
    MODES = {
        "conservative": {
            "MOVING_AVERAGE_WINDOW": 6,
            "TREND_WINDOW": 9,
            "WEIGHT_STABLE": 0.8,
            "WEIGHT_TREND": 0.2,
            "DAMPING_FACTOR": 0.85,
        },
        "balanced": {
            "MOVING_AVERAGE_WINDOW": 3,
            "TREND_WINDOW": 6,
            "WEIGHT_STABLE": 0.7,
            "WEIGHT_TREND": 0.3,
            "DAMPING_FACTOR": 0.9,
        },
        "aggressive": {
            "MOVING_AVERAGE_WINDOW": 2,
            "TREND_WINDOW": 4,
            "WEIGHT_STABLE": 0.6,
            "WEIGHT_TREND": 0.4,
            "DAMPING_FACTOR": 0.95,
        },
    }

    def __init__(self, mode="balanced"):
        """
        mode: режим прогноза (conservative/balanced/aggressive)
        """
        self.mode = mode
        params = self.MODES.get(mode, self.MODES["balanced"])

        self.MOVING_AVERAGE_WINDOW = params["MOVING_AVERAGE_WINDOW"]
        self.TREND_WINDOW = params["TREND_WINDOW"]
        self.WEIGHT_STABLE = params["WEIGHT_STABLE"]
        self.WEIGHT_TREND = params["WEIGHT_TREND"]
        self.DAMPING_FACTOR = params["DAMPING_FACTOR"]

    def _calculate_moving_average(self, data, window):
        """
        Расчет скользящего среднего

        data: список значений
        window: окно усреднения

        Returns:
            float: среднее значение последних N элементов
        """

        if not data:
            return 0

        effective_window = min(window, len(data))
        return sum(data[-effective_window:]) / effective_window

    def _calculate_trend(self, data):
        """
        Расчет линейного тренда (наклона) через numpy

        data: список значений

        Returns:
            float: коэффициент тренда (наклон линейной регрессии)
        """
        if len(data) < 2:
            return 0

        x = np.arange(len(data))
        y = np.array(data)

        # Линейная регрессия: y = ax + b
        coefficients = np.polyfit(x, y, 1)
        slope = coefficients[0]

        return slope

    def forecast(self, historical_data, forecast_months, round_decimals=0):
        """
        Прогноз методом скользящего среднего + тренд

        historical_data: список исторических значений
        forecast_months: количество месяцев для прогноза
        round_decimals: округление (0 для int, 2 для float)

        Returns:
            list: прогнозные значения
        """

        # 1. Валидация данных (из базового класса)
        is_valid, error = self._validate_data(historical_data)
        if not is_valid:
            if round_decimals == 0:
                return [0] * forecast_months
            else:
                return [0.0] * forecast_months

        # 2. Обработка недостаточных данных (из базового класса)
        simple_forecast = self._handle_insufficient_data(
            historical_data, forecast_months, round_decimals
        )
        if simple_forecast is not None:
            return simple_forecast

        # 3. Адаптивное окно (не больше доступных данных)
        actual_ma_window = min(self.MOVING_AVERAGE_WINDOW, len(historical_data))
        actual_trend_window = min(self.TREND_WINDOW, len(historical_data))

        # 4. Скользящее среднее
        base_value = self._calculate_moving_average(
            historical_data, window=actual_ma_window
        )

        # 5. Тренд
        trend_window = min(actual_trend_window, len(historical_data))
        recent_data = historical_data[-trend_window:]
        trend = self._calculate_trend(recent_data)

        # 6. Генерация прогноза
        forecast = []

        for i in range(forecast_months):
            # Взвешенная комбинация + затухающий тренд
            stable_component = self.WEIGHT_STABLE * base_value

            trend_component = self.WEIGHT_TREND * (
                base_value + trend * (i + 1) * (self.DAMPING_FACTOR**i)
            )

            predicted_value = stable_component + trend_component
            predicted_value = max(0, predicted_value)

            if round_decimals == 0:
                forecast.append(int(round(predicted_value)))
            else:
                forecast.append(round(predicted_value, round_decimals))

        return forecast

    def __repr__(self):
        """Строковое представление"""
        return f"StatisticalForecast(mode='{self.mode}')"
