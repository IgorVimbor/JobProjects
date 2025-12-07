"""
Модуль методов прогнозирования

Доступные классы:
- BaseForecast: базовый абстрактный класс
- StatisticalForecast: статистические методы
- MachineLearningForecast: машинное обучение
"""

from .base import BaseForecast
from .statistical import StatisticalForecast
from .ml import MachineLearningForecast

__all__ = [
    "BaseForecast",
    "StatisticalForecast",
    "MachineLearningForecast",
]
