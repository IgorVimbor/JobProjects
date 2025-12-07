# claims/modules/forecast/ml.py

"""Методы машинного обучения для прогнозирования"""

import numpy as np
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import make_pipeline

from .base import BaseForecast


class MachineLearningForecast(BaseForecast):
    """
    Методы машинного обучения для прогнозирования

    Модели:
    - linear: Линейная регрессия (простая, быстрая)
    - ridge: Ridge регрессия (устойчива к выбросам)
    - polynomial: Полиномиальная регрессия степени 2 (нелинейный тренд)
    """

    def __init__(self, model="linear"):
        """
        model: тип модели (linear/ridge/polynomial)
        """
        self.model = model

    def _prepare_data(self, historical_data):
        """
        Подготовка данных для sklearn

        historical_data: список значений

        Returns:
            tuple: (X, y) где X - индексы времени, y - значения
        """
        # X = индексы (время): [[0], [1], [2], ...]
        X = np.arange(len(historical_data)).reshape(-1, 1)

        # y = значения: [10, 12, 15, ...]
        y = np.array(historical_data)

        return X, y

    def _forecast_linear(self, historical_data, forecast_months, round_decimals):
        """
        Линейная регрессия: y = ax + b

        Простая экстраполяция линейного тренда
        """
        X, y = self._prepare_data(historical_data)

        # Обучаем модель
        model = LinearRegression()
        model.fit(X, y)

        # Прогнозируем будущие значения
        future_indices = np.arange(
            len(historical_data), len(historical_data) + forecast_months
        ).reshape(-1, 1)

        predictions = model.predict(future_indices)

        # Не даем уйти в отрицательные значения
        predictions = np.maximum(predictions, 0)

        # Округляем
        if round_decimals == 0:
            return [int(round(p)) for p in predictions]
        else:
            return [round(float(p), round_decimals) for p in predictions]

    def _forecast_ridge(self, historical_data, forecast_months, round_decimals):
        """
        Ridge регрессия: y = ax + b (с регуляризацией)

        Параметр alpha контролирует силу регуляризации:
        - alpha=1.0: умеренная регуляризация (по умолчанию)
        - alpha=0.1: слабая (близко к обычной линейной)
        - alpha=10.0: сильная (сглаживание)
        """
        X, y = self._prepare_data(historical_data)

        # Обучаем модель с регуляризацией
        model = Ridge(alpha=1.0)  # Параметр регуляризации
        model.fit(X, y)

        # Прогнозируем
        future_indices = np.arange(
            len(historical_data), len(historical_data) + forecast_months
        ).reshape(-1, 1)

        predictions = model.predict(future_indices)
        predictions = np.maximum(predictions, 0)

        if round_decimals == 0:
            return [int(round(p)) for p in predictions]
        else:
            return [round(float(p), round_decimals) for p in predictions]

    def _forecast_polynomial(self, historical_data, forecast_months, round_decimals):
        """
        Полиномиальная регрессия: y = ax² + bx + c

        Степень 2 (квадратичная) - улавливает ускорение/замедление тренда
        (Полиномиальная регрессия степени 2 на малом объеме данных → переобучение)
        """
        X, y = self._prepare_data(historical_data)

        # Создаем pipeline: полиномиальные признаки + линейная регрессия
        model = make_pipeline(
            PolynomialFeatures(degree=2),  # Степень полинома degree=2
            # Можно понизить степень degree=1.5 при переобучении или сделать линейную степень degree=1
            LinearRegression(),
        )
        model.fit(X, y)

        # Прогнозируем
        future_indices = np.arange(
            len(historical_data), len(historical_data) + forecast_months
        ).reshape(-1, 1)

        predictions = model.predict(future_indices)
        predictions = np.maximum(predictions, 0)

        if round_decimals == 0:
            return [int(round(p)) for p in predictions]
        else:
            return [round(float(p), round_decimals) for p in predictions]

    def forecast(self, historical_data, forecast_months, round_decimals=0):
        """
        Главный метод прогноза

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

        # 2. Обработка недостаточных данных
        simple_forecast = self._handle_insufficient_data(
            historical_data, forecast_months, round_decimals
        )
        if simple_forecast is not None:
            return simple_forecast

        # 3. Минимум 3 точки данных для ML
        if len(historical_data) < 3:
            # Слишком мало данных для ML - возвращаем среднее
            avg = sum(historical_data) / len(historical_data)
            if round_decimals == 0:
                return [int(round(avg))] * forecast_months
            else:
                return [round(avg, round_decimals)] * forecast_months

        # 4. Выбор модели и прогноз
        try:
            if self.model == "linear":
                return self._forecast_linear(
                    historical_data, forecast_months, round_decimals
                )
            elif self.model == "ridge":
                return self._forecast_ridge(
                    historical_data, forecast_months, round_decimals
                )
            elif self.model == "polynomial":
                return self._forecast_polynomial(
                    historical_data, forecast_months, round_decimals
                )
            else:
                # Неизвестная модель - fallback на linear
                return self._forecast_linear(
                    historical_data, forecast_months, round_decimals
                )

        except Exception as e:
            # При ошибке ML - возвращаем простое среднее
            avg = sum(historical_data) / len(historical_data)
            if round_decimals == 0:
                return [int(round(avg))] * forecast_months
            else:
                return [round(avg, round_decimals)] * forecast_months

    def __repr__(self):
        """Строковое представление"""
        return f"MachineLearningForecast(model='{self.model}')"
