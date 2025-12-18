# claims/modules/forecast/seasonal.py
"""
Модуль сезонного прогнозирования (для фактических данных более 24 месяцев).

Включает класс:
- `SeasonalForecast` - Прогнозирование с учётом сезонности
"""

import numpy as np
from typing import List, Dict, Optional, Tuple
from .base import BaseForecast

# Опциональные зависимости
try:
    from statsmodels.tsa.holtwinters import ExponentialSmoothing  # type: ignore
    from statsmodels.tsa.seasonal import seasonal_decompose  # type: ignore

    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False


class SeasonalForecast(BaseForecast):
    """
    Прогнозирование с учётом сезонности

    Методы:
    - holt_winters: Экспоненциальное сглаживание Хольта-Винтерса
    - seasonal_decompose: Декомпозиция + экстраполяция тренда
    - seasonal_naive: Сезонный наивный прогноз (fallback)

    Решает проблему "усреднения" - сохраняет пики и спады
    """

    # Минимальные требования к данным
    MIN_DATA_HOLT_WINTERS = 24  # 2 полных сезона
    MIN_DATA_DECOMPOSITION = 24
    MIN_DATA_SEASONAL_NAIVE = 12

    def __init__(
        self,
        method: str = "auto",
        seasonal_period: int = 12,
        seasonal_type: str = "mul",
    ):
        """
        Args:
            method: Метод прогноза (auto/holt_winters/decomposition/naive)
            seasonal_period: Период сезонности (12 = месячная годовая)
            seasonal_type: Тип сезонности (mul=мультипликативная, add=аддитивная)
        """
        self.method = method
        self.seasonal_period = seasonal_period
        self.seasonal_type = seasonal_type

    def _calculate_seasonal_indices(self, data: List[float]) -> Dict[int, float]:
        """
        Расчёт сезонных индексов вручную.

        Индекс = среднее значение месяца / общее среднее

        Args:
            data: Исторические данные (минимум 12 значений)

        Returns:
            Dict[month_index, seasonal_factor]
        """
        if len(data) < self.seasonal_period:
            return {i: 1.0 for i in range(self.seasonal_period)}

        overall_mean = np.mean(data)
        if overall_mean == 0:
            return {i: 1.0 for i in range(self.seasonal_period)}

        indices = {}
        for month_idx in range(self.seasonal_period):
            # Собираем все значения для этого месяца
            month_values = [
                data[i] for i in range(month_idx, len(data), self.seasonal_period)
            ]
            if month_values:
                month_mean = np.mean(month_values)
                indices[month_idx] = month_mean / overall_mean
            else:
                indices[month_idx] = 1.0

        return indices

    def _forecast_seasonal_naive(
        self, historical_data: List[float], forecast_months: int, round_decimals: int
    ) -> List[float]:
        """
        Сезонный наивный прогноз.

        Берёт значение того же месяца из прошлого + линейный тренд.
        Работает при минимуме данных (от 12 месяцев).
        """
        data = np.array(historical_data)
        n = len(data)

        # Рассчитываем годовой тренд
        if n >= 24:
            first_year_avg = np.mean(data[:12])
            last_year_avg = np.mean(data[-12:])
            annual_trend = last_year_avg - first_year_avg
        elif n >= 12:
            # Тренд на основе линейной регрессии
            x = np.arange(n)
            coeffs = np.polyfit(x, data, 1)
            annual_trend = coeffs[0] * 12  # Годовой тренд
        else:
            annual_trend = 0

        # Сезонные индексы
        seasonal_indices = self._calculate_seasonal_indices(historical_data)

        # Базовое значение (среднее за последний год или все данные)
        base_value = (
            np.mean(data[-self.seasonal_period :])
            if n >= self.seasonal_period
            else np.mean(data)
        )

        forecast = []
        for i in range(forecast_months):
            # Индекс месяца в сезоне
            month_idx = (n + i) % self.seasonal_period
            seasonal_factor = seasonal_indices.get(month_idx, 1.0)

            # Прогноз = база × сезонность + тренд
            months_ahead = i + 1
            trend_adjustment = annual_trend * (months_ahead / 12)

            predicted = base_value * seasonal_factor + trend_adjustment
            predicted = max(0, predicted)

            if round_decimals == 0:
                forecast.append(int(round(predicted)))
            else:
                forecast.append(round(predicted, round_decimals))

        return forecast

    def _forecast_holt_winters(
        self, historical_data: List[float], forecast_months: int, round_decimals: int
    ) -> Tuple[List[float], Optional[Dict]]:
        """
        Прогноз методом Хольта-Винтерса.

        Учитывает: уровень, тренд, сезонность.
        Требует statsmodels и минимум 2 полных сезона данных.

        Returns:
            Tuple[forecast, metadata]
        """
        if not HAS_STATSMODELS:
            return self._forecast_seasonal_naive(
                historical_data, forecast_months, round_decimals
            ), {"fallback": "statsmodels not installed"}

        try:
            # Преобразуем в numpy array
            data = np.array(historical_data, dtype=float)

            # Заменяем нули на маленькие значения (для мультипликативной модели)
            if self.seasonal_type == "mul":
                data = np.maximum(data, 0.01)

            model = ExponentialSmoothing(
                data,
                seasonal_periods=self.seasonal_period,
                trend="add",
                seasonal=self.seasonal_type,
                damped_trend=True,  # Затухающий тренд - более стабильный прогноз
                use_boxcox=False,
            )

            fitted = model.fit(optimized=True)
            predictions = fitted.forecast(forecast_months)

            # Метаданные модели
            metadata = {
                "method": "holt_winters",
                "aic": fitted.aic if hasattr(fitted, "aic") else None,
                "seasonal_type": self.seasonal_type,
            }

            # Форматируем результат
            predictions = np.maximum(predictions, 0)  # Не меньше 0

            if round_decimals == 0:
                result = [int(round(p)) for p in predictions]
            else:
                result = [round(float(p), round_decimals) for p in predictions]

            return result, metadata

        except Exception as e:
            # Fallback на наивный метод
            return self._forecast_seasonal_naive(
                historical_data, forecast_months, round_decimals
            ), {"fallback": str(e)}

    def _forecast_decomposition(
        self, historical_data: List[float], forecast_months: int, round_decimals: int
    ) -> Tuple[List[float], Optional[Dict]]:
        """
        Прогноз через сезонную декомпозицию.

        1. Разложение на тренд + сезонность + остаток
        2. Экстраполяция тренда
        3. Применение сезонных коэффициентов
        """
        if not HAS_STATSMODELS:
            return self._forecast_seasonal_naive(
                historical_data, forecast_months, round_decimals
            ), {"fallback": "statsmodels not installed"}

        try:
            data = np.array(historical_data, dtype=float)

            # Для мультипликативной модели нужны положительные значения
            if self.seasonal_type == "mul":
                data = np.maximum(data, 0.01)

            # Декомпозиция
            decomposition = seasonal_decompose(
                data,
                model="multiplicative" if self.seasonal_type == "mul" else "additive",
                period=self.seasonal_period,
                extrapolate_trend="freq",
            )

            trend = decomposition.trend
            seasonal = decomposition.seasonal

            # Убираем NaN из тренда
            trend_clean = trend[~np.isnan(trend)]

            # Экстраполируем тренд линейной регрессией
            x = np.arange(len(trend_clean))
            coeffs = np.polyfit(x, trend_clean, 1)
            slope, intercept = coeffs[0], coeffs[1]

            # Прогноз
            forecast = []
            n = len(historical_data)

            for i in range(forecast_months):
                # Экстраполированный тренд
                trend_value = intercept + slope * (len(trend_clean) + i)

                # Сезонный множитель (берём из последнего полного цикла)
                season_idx = (n + i) % self.seasonal_period
                seasonal_factor = seasonal[-(self.seasonal_period - season_idx)]

                if self.seasonal_type == "mul":
                    predicted = trend_value * seasonal_factor
                else:
                    predicted = trend_value + seasonal_factor

                predicted = max(0, predicted)

                if round_decimals == 0:
                    forecast.append(int(round(predicted)))
                else:
                    forecast.append(round(predicted, round_decimals))

            metadata = {
                "method": "decomposition",
                "trend_slope": slope,
                "seasonal_type": self.seasonal_type,
            }

            return forecast, metadata

        except Exception as e:
            return self._forecast_seasonal_naive(
                historical_data, forecast_months, round_decimals
            ), {"fallback": str(e)}

    def _select_method(self, data_length: int) -> str:
        """
        Автоматический выбор метода на основе объёма данных.
        """
        if self.method != "auto":
            return self.method

        if data_length >= self.MIN_DATA_HOLT_WINTERS and HAS_STATSMODELS:
            return "holt_winters"
        elif data_length >= self.MIN_DATA_DECOMPOSITION and HAS_STATSMODELS:
            return "decomposition"
        elif data_length >= self.MIN_DATA_SEASONAL_NAIVE:
            return "seasonal_naive"
        else:
            return "seasonal_naive"  # Будет использовать что есть

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

        # 3. Выбор метода
        method = self._select_method(len(historical_data))

        # 4. Прогноз
        if method == "holt_winters":
            result, _ = self._forecast_holt_winters(
                historical_data, forecast_months, round_decimals
            )
        elif method == "decomposition":
            result, _ = self._forecast_decomposition(
                historical_data, forecast_months, round_decimals
            )
        else:
            result = self._forecast_seasonal_naive(
                historical_data, forecast_months, round_decimals
            )

        return result

    def forecast_with_metadata(
        self,
        historical_data: List[float],
        forecast_months: int,
        round_decimals: int = 0,
    ) -> Dict:
        """
        Прогноз с дополнительной информацией.

        Returns:
            Dict с ключами: forecast, method, seasonal_indices, metadata
        """
        is_valid, error = self._validate_data(historical_data)
        if not is_valid:
            return {
                "forecast": [0 if round_decimals == 0 else 0.0] * forecast_months,
                "method": None,
                "error": error,
            }

        method = self._select_method(len(historical_data))

        if method == "holt_winters":
            forecast, metadata = self._forecast_holt_winters(
                historical_data, forecast_months, round_decimals
            )
        elif method == "decomposition":
            forecast, metadata = self._forecast_decomposition(
                historical_data, forecast_months, round_decimals
            )
        else:
            forecast = self._forecast_seasonal_naive(
                historical_data, forecast_months, round_decimals
            )
            metadata = {"method": "seasonal_naive"}

        return {
            "forecast": forecast,
            "method": method,
            "seasonal_indices": self._calculate_seasonal_indices(historical_data),
            "metadata": metadata,
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
            f"SeasonalForecast(method='{self.method}', period={self.seasonal_period})"
        )
