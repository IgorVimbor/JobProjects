# claims/modules/forecast/seasonal.py
"""
Модуль сезонного прогнозирования (для фактических данных менее 24 месяца).

Включает класс:
- `SeasonalForecast` - Прогнозирование с учётом сезонности
"""

import numpy as np
from typing import List, Dict, Tuple
from .base import BaseForecast


class SeasonalForecast(BaseForecast):
    """
    Прогнозирование с учётом сезонности

    Метод: Сезонный наивный прогноз с трендом

    Решает проблему "усреднения" - сохраняет пики и спады

    TODO: Добавить Holt-Winters (seasonal_24_month.py) когда накопится 24+ месяцев данных (2026+)
    """

    def __init__(
        self,
        method: str = "auto",
        seasonal_period: int = 12,
        seasonal_type: str = "mul",
    ):
        """
        Args:
            method: Метод прогноза (пока только naive)
            seasonal_period: Период сезонности (12 = месячная годовая)
            seasonal_type: Тип сезонности (mul=мультипликативная, add=аддитивная) - для будущего Holt-Winters
        """
        self.method = method
        self.seasonal_period = seasonal_period
        self.seasonal_type = seasonal_type

    # def _calculate_seasonal_indices(self, data: List[float]) -> Dict[int, float]:
    #     """
    #     Расчёт сезонных индексов.

    #     Индекс = среднее значение месяца / общее среднее

    #     Args:
    #         data: Исторические данные (минимум 12 значений)

    #     Returns:
    #         Dict[month_index, seasonal_factor]
    #     """
    #     if len(data) < self.seasonal_period:
    #         return {i: 1.0 for i in range(self.seasonal_period)}

    #     overall_mean = np.mean(data)
    #     if overall_mean == 0:
    #         return {i: 1.0 for i in range(self.seasonal_period)}

    #     indices = {}
    #     for month_idx in range(self.seasonal_period):
    #         # Собираем все значения для этого месяца
    #         month_values = [
    #             data[i] for i in range(month_idx, len(data), self.seasonal_period)
    #         ]
    #         if month_values:
    #             month_mean = np.mean(month_values)
    #             indices[month_idx] = month_mean / overall_mean
    #         else:
    #             indices[month_idx] = 1.0

    #     return indices

    def _calculate_seasonal_indices(self, data: List[float]) -> Dict[int, float]:
        """
        Расчёт сезонных индексов.

        Работает даже при неполном годе данных.
        """
        n = len(data)

        if n == 0:
            return {i: 1.0 for i in range(self.seasonal_period)}

        overall_mean = np.mean(data)
        if overall_mean == 0:
            return {i: 1.0 for i in range(self.seasonal_period)}

        indices = {}

        # Рассчитываем индексы для имеющихся месяцев
        for month_idx in range(self.seasonal_period):
            # Собираем все значения для этого месяца
            month_values = [data[i] for i in range(month_idx, n, self.seasonal_period)]
            if month_values:
                month_mean = np.mean(month_values)
                indices[month_idx] = month_mean / overall_mean
            else:
                # Для месяцев без данных — используем 1.0
                indices[month_idx] = 1.0

        return indices

    # def _forecast_seasonal_naive(
    #     self, historical_data: List[float], forecast_months: int, round_decimals: int
    # ) -> List[float]:
    #     """
    #     Сезонный наивный прогноз.

    #     Берёт значение того же месяца из прошлого + линейный тренд.
    #     Работает при минимуме данных (от 12 месяцев).
    #     """
    #     data = np.array(historical_data)
    #     n = len(data)

    #     # Рассчитываем тренд
    #     if n >= 12:
    #         # Тренд на основе линейной регрессии
    #         x = np.arange(n)
    #         coeffs = np.polyfit(x, data, 1)
    #         monthly_trend = coeffs[0]  # Месячный тренд
    #     else:
    #         monthly_trend = 0

    #     # Сезонные индексы
    #     seasonal_indices = self._calculate_seasonal_indices(historical_data)

    #     # Базовое значение (среднее за последний год или все данные)
    #     base_value = (
    #         np.mean(data[-self.seasonal_period :])
    #         if n >= self.seasonal_period
    #         else np.mean(data)
    #     )

    #     forecast = []
    #     for i in range(forecast_months):
    #         # Индекс месяца в сезоне
    #         month_idx = (n + i) % self.seasonal_period
    #         seasonal_factor = seasonal_indices.get(month_idx, 1.0)

    #         # Прогноз = база × сезонность + тренд
    #         months_ahead = i + 1
    #         trend_adjustment = monthly_trend * months_ahead

    #         predicted = base_value * seasonal_factor + trend_adjustment
    #         predicted = max(0, predicted)

    #         if round_decimals == 0:
    #             forecast.append(int(round(predicted)))
    #         else:
    #             forecast.append(round(predicted, round_decimals))

    #     return forecast

    def _forecast_seasonal_naive(
        self, historical_data: List[float], forecast_months: int, round_decimals: int
    ) -> List[float]:
        """
        Сезонный наивный прогноз.

        Работает даже при неполном годе данных.
        """
        data = np.array(historical_data)
        n = len(data)

        # Рассчитываем тренд (даже при малом количестве данных)
        if n >= 3:
            x = np.arange(n)
            coeffs = np.polyfit(x, data, 1)
            monthly_trend = coeffs[0]
        else:
            monthly_trend = 0

        # Сезонные индексы (теперь работают при любом n)
        seasonal_indices = self._calculate_seasonal_indices(historical_data)

        # Базовое значение
        if n >= self.seasonal_period:
            base_value = np.mean(data[-self.seasonal_period :])
        else:
            base_value = np.mean(data)

        # Коэффициент затухания тренда (чтобы не улетал в бесконечность)
        damping = 0.9

        forecast = []
        for i in range(forecast_months):
            # Индекс месяца в сезоне
            month_idx = (n + i) % self.seasonal_period
            seasonal_factor = seasonal_indices.get(month_idx, 1.0)

            # Прогноз = база × сезонность + затухающий тренд
            months_ahead = i + 1
            trend_adjustment = monthly_trend * months_ahead * (damping**i)

            predicted = base_value * seasonal_factor + trend_adjustment
            predicted = max(0, predicted)

            if round_decimals == 0:
                forecast.append(int(round(predicted)))
            else:
                forecast.append(round(predicted, round_decimals))

        return forecast

    def forecast(
        self,
        historical_data: List[float],
        forecast_months: int,
        round_decimals: int = 0,
    ) -> List[float]:
        """
        Главный метод прогноза с учётом сезонности.

        Args:
            historical_data: Исторические данные (по месяцам)
            forecast_months: Количество месяцев для прогноза
            round_decimals: Округление (0 для количества, 2 для сумм)

        Returns:
            Список прогнозных значений
        """
        # 1. Валидация
        is_valid, error = self._validate_data(historical_data)
        if not is_valid:
            return [0 if round_decimals == 0 else 0.0] * forecast_months

        # 2. Обработка недостаточных данных
        simple_forecast = self._handle_insufficient_data(
            historical_data, forecast_months, round_decimals
        )
        if simple_forecast is not None:
            return simple_forecast

        # 3. Прогноз
        return self._forecast_seasonal_naive(
            historical_data, forecast_months, round_decimals
        )

    def forecast_with_metadata(
        self,
        historical_data: List[float],
        forecast_months: int,
        round_decimals: int = 0,
    ) -> Dict:
        """
        Прогноз с дополнительной информацией.

        Returns:
            Dict с ключами: forecast, method, seasonal_indices
        """
        is_valid, error = self._validate_data(historical_data)
        if not is_valid:
            return {
                "forecast": [0 if round_decimals == 0 else 0.0] * forecast_months,
                "method": None,
                "error": error,
            }

        forecast = self._forecast_seasonal_naive(
            historical_data, forecast_months, round_decimals
        )

        return {
            "forecast": forecast,
            "method": "seasonal_naive",
            "seasonal_indices": self._calculate_seasonal_indices(historical_data),
        }

    def get_seasonality_pattern(self, historical_data: List[float]) -> Dict[int, float]:
        """
        Возвращает паттерн сезонности для визуализации.

        Returns:
            Dict[month_index, seasonal_factor]
        """
        return self._calculate_seasonal_indices(historical_data)

    def __repr__(self):
        return (
            f"SeasonalForecast(method='seasonal_naive', period={self.seasonal_period})"
        )
