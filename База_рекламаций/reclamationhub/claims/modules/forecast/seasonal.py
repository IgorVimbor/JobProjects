# claims/modules/forecast/seasonal.py
"""Модуль сезонного прогнозирования (для фактических данных менее 24 месяца)."""

"""
Принцип работы:
    1. Рассчитываем СЕЗОННЫЙ ИНДЕКС для каждого месяца (насколько месяц отличается от среднего)
    2. Рассчитываем ТРЕНД (растёт или падает общий уровень)
    3. Прогноз = Базовое_значение × Сезонный_индекс + Тренд

Включает класс:
- `SeasonalForecast` - Прогнозирование с учётом сезонности и тренда
"""

import numpy as np
from typing import List, Dict, Tuple
from .base import BaseForecast


class SeasonalForecast(BaseForecast):
    """Прогнозирование с учётом сезонности"""

    """
    Решает главную проблему статистических методов — "усреднение".
    Вместо ровной линии прогноза даёт кривую, повторяющую исторический паттерн.

    Атрибуты:
        method: Метод прогноза (пока только наивный прогноз с трендом → seasonal_naive)
        seasonal_period: Длина сезона (12 = год для месячных данных)
        seasonal_type: Тип сезонности ("mul" или "add") — для будущего Holt-Winters

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
            method: Метод прогноза "auto" выбирает лучший для объёма данных (пока только naive)
            seasonal_period: Период сезонности (12 = месячная годовая)
            seasonal_type: Тип сезонности для будущего расширения (mul=мультипликативная, add=аддитивная)
        """
        self.method = method
        self.seasonal_period = seasonal_period
        self.seasonal_type = seasonal_type

    def _calculate_seasonal_indices(self, data: List[float]) -> Dict[int, float]:
        """
        Расчёт сезонных индексов (число, показывающее, насколько месяц отличается от среднего).
        Работает даже при неполном годе данных.

        Индекс = среднее значение месяца / общее среднее

        Args:
            data: Исторические данные (список значений по месяцам)

        Returns:
            Словарь {номер_месяца: индекс}
        """
        n = len(data)

        # Если данных нет — все индексы = 1.0 (нет отклонений)
        if n == 0:
            return {i: 1.0 for i in range(self.seasonal_period)}

        # ============ ОБЩЕЕ СРЕДНЕЕ =============
        overall_mean = np.mean(data)  # Базовый уровень, от которого считаем отклонения

        # Защита от деления на ноль
        if overall_mean == 0:
            return {i: 1.0 for i in range(self.seasonal_period)}

        indices = {}

        # ============ РАСЧЁТ ИНДЕКСА ДЛЯ КАЖДОГО МЕСЯЦА =============
        # Рассчитываем индексы для имеющихся месяцев
        # Проходим по всем месяцам. Для каждого месяца собираем ВСЕ значения из истории.
        # ============================================================
        for month_idx in range(self.seasonal_period):
            # Собираем все значения для этого месяца
            month_values = [data[i] for i in range(month_idx, n, self.seasonal_period)]
            if month_values:
                # Среднее по этому месяцу за все годы
                month_mean = np.mean(month_values)
                # Индекс = отношение к общему среднему
                indices[month_idx] = month_mean / overall_mean
            else:
                # Для месяцев без данных — используем 1.0
                indices[month_idx] = 1.0

        return indices

    def _forecast_seasonal_naive(
        self, historical_data: List[float], forecast_months: int, round_decimals: int
    ) -> List[float]:
        """Сезонный наивный прогноз.

        Берёт значение того же месяца из прошлого + линейный тренд.
        Работает даже при неполном годе данных.

        --------- АЛГОРИТМ ----------
        Для каждого будущего месяца:
            ПРОГНОЗ = Базовое_значение × Сезонный_индекс + Тренд
        Где:
        - Базовое значение = среднее за последний год (или все данные)
        - Сезонный индекс = насколько этот месяц отличается от среднего
        - Тренд = общее направление (рост/падение) с затуханием
        """
        data = np.array(historical_data)
        n = len(data)

        # ============ РАСЧЁТ ТРЕНДА ================================
        # Тренд — это "наклон" данных (растут они или падают).
        #
        # Для расчета тренда используем линейную регрессию - проводим прямую через точки.
        # Наклон этой прямой = тренд
        # Нужно минимум 3 точки для надёжного расчёта тренда
        # ============================================================
        if n >= 3:
            x = np.arange(n)  # x = [0, 1, 2, 3, ...] — номера месяцев
            # np.polyfit находит коэффициенты полинома (прямой линии)
            # coeffs[0] = наклон (slope), coeffs[1] = intercept
            coeffs = np.polyfit(x, data, 1)
            monthly_trend = coeffs[0]  # Месячный тренд
        else:
            monthly_trend = 0  # Мало данных — считаем тренд нулевым

        # ============ СЕЗОННЫЕ ИНДЕКСЫ (теперь работают при любом n) =============
        seasonal_indices = self._calculate_seasonal_indices(historical_data)

        # ============ БАЗОВОЕ ЗНАЧЕНИЕ =============================
        # Это "средний уровень", от которого строится прогноз.
        # Если данных >= 12 месяцев — берём среднее за ПОСЛЕДНИЙ год (учитывает недавние изменения)
        # Если данных < 12 — берём среднее за ВСЕ данные
        # ============================================================
        if n >= self.seasonal_period:
            # Среднее за последние 12 месяцев
            base_value = np.mean(data[-self.seasonal_period :])
        else:
            # Среднее по всем доступным данным
            base_value = np.mean(data)

        # ============ КОЭФФИЦИЕНТ ЗАТУХАНИЯ ТРЕНДА ==================
        # Тренд "затухает" со временем.
        # damping = 0.9 означает: каждый следующий месяц влияние тренда уменьшается на 10%.
        #
        # Если не делать без "затухания", то возникнет проблема: если тренд = +5/месяц,
        # то через 12 месяцев прогноз вырастет на +60, что может быть нереалистично.
        #
        # Месяц 1: тренд × 1.0
        # Месяц 2: тренд × 0.9
        # Месяц 3: тренд × 0.81 (0.9²)
        # Месяц 6: тренд × 0.59 (0.9⁵)
        # ============================================================
        damping = 0.9

        # ============ ГЕНЕРАЦИЯ ПРОГНОЗА ============
        forecast = []
        for i in range(forecast_months):
            # # Определяем, какой это месяц в сезонном цикле
            # ────────────────────────────────────────────────────
            # n = 11 (данные янв-ноя), прогнозируем с декабря
            # i=0: month_idx = (11 + 0) % 12 = 11 → декабрь
            # i=1: month_idx = (11 + 1) % 12 = 0  → январь
            # i=2: month_idx = (11 + 2) % 12 = 1  → февраль
            # ────────────────────────────────────────────────────
            month_idx = (n + i) % self.seasonal_period
            seasonal_factor = seasonal_indices.get(month_idx, 1.0)

            # Рассчитываем прогноз
            # Прогноз = база × сезонность + затухающий тренд
            # ────────────────────────────────────────────────────
            # 1. База × сезонность = учёт сезонных колебаний
            # 2. + затухающий тренд = учёт общего направления
            #
            # damping ** i:
            #   i=0: 0.9^0 = 1.0   (полный тренд)
            #   i=1: 0.9^1 = 0.9   (90% тренда)
            #   i=2: 0.9^2 = 0.81  (81% тренда)
            # ────────────────────────────────────────────────────
            months_ahead = i + 1
            trend_adjustment = monthly_trend * months_ahead * (damping**i)

            predicted = base_value * seasonal_factor + trend_adjustment

            predicted = max(0, predicted)  # Значение не может быть отрицательным

            # Округление
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
        # 1. ВАЛИДАЦИЯ ДАННЫХ
        is_valid, error = self._validate_data(historical_data)
        if not is_valid:
            return [0 if round_decimals == 0 else 0.0] * forecast_months

        # 2. ОБРАБОТКА НЕДОСТАТОЧНЫХ ДАННЫХ
        # Если данных совсем мало (1-2 точки), используем упрощённый прогноз
        simple_forecast = self._handle_insufficient_data(
            historical_data, forecast_months, round_decimals
        )
        if simple_forecast is not None:
            return simple_forecast

        # 3. ОСНОВНОЙ ПРОГНОЗ
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

        Возвращает не только прогноз, но и метаданные:
        - Какой метод использован
        - Сезонные индексы
        - Информация об ошибках

        Returns:
            Словарь с ключами:
            - forecast: список прогнозных значений
            - method: название использованного метода
            - seasonal_indices: индексы по месяцам
            - error: сообщение об ошибке (если есть)
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
        Используется для отображения блока "Сезонность" в UI, где показываются индексы по месяцам с цветовой кодировкой.

        Args:
            historical_data: Исторические данные

        Returns:
            Словарь {номер_месяца: индекс}
            Пример: {0: 2.2, 1: 0.5, 2: 1.2, 3: 0.5, ...}
        """
        return self._calculate_seasonal_indices(historical_data)

    def __repr__(self):
        return (
            f"SeasonalForecast(method='seasonal_naive', period={self.seasonal_period})"
        )
