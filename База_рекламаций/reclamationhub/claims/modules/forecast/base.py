# claims/modules/forecast/base.py

"""Базовый класс для всех методов прогнозирования"""

from abc import ABC, abstractmethod


class BaseForecast(ABC):
    """
    Абстрактный базовый класс для методов прогнозирования
    Все наследники должны реализовать метод forecast()
    """

    @abstractmethod
    def forecast(self, historical_data, forecast_months, round_decimals=0):
        """
        Прогноз на основе исторических данных

        historical_data: список исторических значений
        forecast_months: количество месяцев для прогноза
        round_decimals: округление (0 для количества, 2 для сумм)

        Returns:
            list: прогнозные значения
        """
        pass

    def _validate_data(self, historical_data):
        """
        Общая валидация данных (можно переопределить в наследниках)

        Returns:
            tuple: (is_valid, error_message)
        """
        if not historical_data:
            return False, "Нет данных для прогноза"

        if all(v == 0 for v in historical_data):
            return False, "Все данные равны нулю"

        return True, None

    def _handle_insufficient_data(
        self, historical_data, forecast_months, round_decimals
    ):
        """Обработка случая недостаточных данных"""

        if not historical_data or all(v == 0 for v in historical_data):
            if round_decimals == 0:
                return [0] * forecast_months  # int для количества
            else:
                return [0.0] * forecast_months  # float для сумм

        # Достаточно данных
        return None

    def __repr__(self):
        """Строковое представление"""
        return f"{self.__class__.__name__}()"
