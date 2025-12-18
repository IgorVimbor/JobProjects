# claims/modules/forecast/__init__.py
"""
Модуль методов прогнозирования.

Классы:
- BaseForecast: Абстрактный базовый класс
- StatisticalForecast: Скользящее среднее + тренд
- MachineLearningForecast: ML-модели (linear, ridge, polynomial)
- SeasonalForecast: Сезонный прогноз (Holt-Winters, декомпозиция)
- TimeSeriesCorrelation: Кросс-корреляция с лагом
- ClaimsPredictor: Связанный прогноз претензий на основе рекламаций
"""

from .base import BaseForecast
from .statistical import StatisticalForecast
from .ml import MachineLearningForecast
from .seasonal import SeasonalForecast
from .correlation import TimeSeriesCorrelation, LagCorrelationResult, OptimalLagResult
from .claims_predictor import ClaimsPredictor, ClaimPrediction, ModelCoefficients


__all__ = [
    # Базовый класс
    "BaseForecast",
    # Методы прогнозирования
    "StatisticalForecast",
    "MachineLearningForecast",
    "SeasonalForecast",
    # Корреляция
    "TimeSeriesCorrelation",
    "LagCorrelationResult",
    "OptimalLagResult",
    # Связанный прогноз
    "ClaimsPredictor",
    "ClaimPrediction",
    "ModelCoefficients",
]


# """
# Модуль методов прогнозирования

# Доступные классы:
# - BaseForecast: базовый абстрактный класс
# - StatisticalForecast: статистические методы
# - MachineLearningForecast: машинное обучение
# """

# from .base import BaseForecast
# from .statistical import StatisticalForecast
# from .ml import MachineLearningForecast

# __all__ = [
#     "BaseForecast",
#     "StatisticalForecast",
#     "MachineLearningForecast",
# ]
