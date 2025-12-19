# claims/modules/forecast/correlation.py
"""
Модуль кросс-корреляции временных рядов.

Включает класс:
- `TimeSeriesCorrelation` - Анализ корреляции с учётом временного лага
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class LagCorrelationResult:
    """Результат корреляции для конкретного лага"""

    lag: int
    correlation: float
    p_value: float
    is_significant: bool
    sample_size: int


@dataclass
class OptimalLagResult:
    """Результат поиска оптимального лага"""

    optimal_lag: int
    correlation: float
    p_value: float
    all_results: List[LagCorrelationResult]


class TimeSeriesCorrelation:
    """
    Анализ кросс-корреляции временных рядов с поиском оптимального лага.

    Используется для определения временной задержки между:
    - Количеством рекламаций
    - Суммами претензий

    Типичный лаг: 2-4 месяца (рекламация → претензия)
    """

    def __init__(
        self,
        series_x: List[float],
        series_y: List[float],
        significance_level: float = 0.05,
    ):
        """
        Args:
            series_x: Первый временной ряд (рекламации)
            series_y: Второй временной ряд (претензии)
            significance_level: Уровень значимости (по умолчанию 0.05)
        """
        self.series_x = np.array(series_x, dtype=float)
        self.series_y = np.array(series_y, dtype=float)
        self.significance_level = significance_level

        # Проверяем scipy для p-value
        try:
            from scipy import stats

            self._stats = stats
            self._has_scipy = True
        except ImportError:
            self._has_scipy = False

    def _pearson_correlation(self, x: np.ndarray, y: np.ndarray) -> Tuple[float, float]:
        """
        Расчёт коэффициента корреляции Пирсона.

        Returns:
            Tuple[correlation, p_value]
        """
        if len(x) < 3:
            return 0.0, 1.0

        if self._has_scipy:
            corr, p_value = self._stats.pearsonr(x, y)
            return float(corr), float(p_value)
        else:
            # Ручной расчёт без scipy
            n = len(x)
            mean_x, mean_y = np.mean(x), np.mean(y)

            numerator = np.sum((x - mean_x) * (y - mean_y))
            denominator = np.sqrt(np.sum((x - mean_x) ** 2) * np.sum((y - mean_y) ** 2))

            if denominator == 0:
                return 0.0, 1.0

            corr = numerator / denominator

            # Приближённый p-value через t-статистику
            if abs(corr) >= 1:
                p_value = 0.0
            else:
                t_stat = corr * np.sqrt((n - 2) / (1 - corr**2))
                # Грубое приближение p-value
                p_value = 2 * (1 - min(0.99, abs(t_stat) / 10))

            return float(corr), float(p_value)

    # def calculate_correlation_at_lag(self, lag: int) -> LagCorrelationResult:
    #     """
    #     Расчёт корреляции при заданном лаге.

    #     lag > 0: series_x опережает series_y на lag периодов
    #     (рекламации в момент t влияют на претензии в момент t+lag)

    #     Args:
    #         lag: Временной сдвиг в периодах (месяцах)

    #     Returns:
    #         LagCorrelationResult
    #     """
    #     if lag == 0:
    #         x, y = self.series_x, self.series_y
    #     elif lag > 0:
    #         # X опережает Y: X[:-lag] соответствует Y[lag:]
    #         x = self.series_x[:-lag] if lag < len(self.series_x) else np.array([])
    #         y = self.series_y[lag:] if lag < len(self.series_y) else np.array([])
    #     else:
    #         # Y опережает X (редкий случай)
    #         abs_lag = abs(lag)
    #         x = (
    #             self.series_x[abs_lag:]
    #             if abs_lag < len(self.series_x)
    #             else np.array([])
    #         )
    #         y = (
    #             self.series_y[:-abs_lag]
    #             if abs_lag < len(self.series_y)
    #             else np.array([])
    #         )

    #     if len(x) < 3 or len(y) < 3:
    #         return LagCorrelationResult(
    #             lag=lag,
    #             correlation=0.0,
    #             p_value=1.0,
    #             is_significant=False,
    #             sample_size=min(len(x), len(y)),
    #         )

    #     # Убеждаемся, что длины равны
    #     min_len = min(len(x), len(y))
    #     x, y = x[:min_len], y[:min_len]

    #     corr, p_value = self._pearson_correlation(x, y)

    #     return LagCorrelationResult(
    #         lag=lag,
    #         correlation=corr,
    #         p_value=p_value,
    #         is_significant=p_value < self.significance_level,
    #         sample_size=min_len,
    #     )

    def calculate_correlation_at_lag(self, lag: int) -> LagCorrelationResult:
        """
        Расчёт корреляции при заданном лаге.

        lag > 0: series_x опережает series_y на lag периодов
        (рекламации в момент t влияют на претензии в момент t+lag)
        """
        n_x = len(self.series_x)
        n_y = len(self.series_y)

        if lag == 0:
            # Без сдвига — берём минимальную длину
            min_len = min(n_x, n_y)
            x = self.series_x[:min_len]
            y = self.series_y[:min_len]
        elif lag > 0:
            # X опережает Y: X[:-lag] соответствует Y[lag:]
            if lag >= n_x or lag >= n_y:
                return LagCorrelationResult(
                    lag=lag,
                    correlation=0.0,
                    p_value=1.0,
                    is_significant=False,
                    sample_size=0,
                )
            x = self.series_x[:-lag]
            y = self.series_y[lag:]
        else:
            # Y опережает X (редкий случай)
            abs_lag = abs(lag)
            if abs_lag >= n_x or abs_lag >= n_y:
                return LagCorrelationResult(
                    lag=lag,
                    correlation=0.0,
                    p_value=1.0,
                    is_significant=False,
                    sample_size=0,
                )
            x = self.series_x[abs_lag:]
            y = self.series_y[:-abs_lag]

        # Синхронизируем длины (защита от рассинхрона)
        min_len = min(len(x), len(y))
        if min_len < 3:
            return LagCorrelationResult(
                lag=lag,
                correlation=0.0,
                p_value=1.0,
                is_significant=False,
                sample_size=min_len,
            )

        x = x[:min_len]
        y = y[:min_len]

        corr, p_value = self._pearson_correlation(x, y)

        return LagCorrelationResult(
            lag=lag,
            correlation=corr,
            p_value=p_value,
            is_significant=p_value < self.significance_level,
            sample_size=min_len,
        )

    def find_optimal_lag(self, max_lag: int = 6, min_lag: int = 0) -> OptimalLagResult:
        """
        Поиск оптимального лага с максимальной корреляцией.

        Args:
            max_lag: Максимальный лаг для проверки
            min_lag: Минимальный лаг (обычно 0)

        Returns:
            OptimalLagResult с оптимальным лагом и всеми результатами
        """
        results = []

        for lag in range(min_lag, max_lag + 1):
            result = self.calculate_correlation_at_lag(lag)
            results.append(result)

        # Находим лаг с максимальной абсолютной корреляцией
        best = max(results, key=lambda r: abs(r.correlation))

        return OptimalLagResult(
            optimal_lag=best.lag,
            correlation=best.correlation,
            p_value=best.p_value,
            all_results=results,
        )

    def get_correlation_matrix(self, max_lag: int = 6) -> Dict[int, float]:
        """
        Возвращает словарь {lag: correlation} для визуализации.

        Returns:
            Dict[lag, correlation]
        """
        return {
            lag: self.calculate_correlation_at_lag(lag).correlation
            for lag in range(max_lag + 1)
        }

    def analyze(self, max_lag: int = 6) -> Dict:
        """
        Полный анализ корреляции.

        Returns:
            Dict с результатами анализа для JSON-сериализации
        """
        optimal = self.find_optimal_lag(max_lag)

        return {
            "optimal_lag": optimal.optimal_lag,
            "optimal_correlation": round(optimal.correlation, 4),
            "p_value": round(optimal.p_value, 4),
            "is_significant": optimal.p_value < self.significance_level,
            "interpretation": self._interpret_correlation(optimal.correlation),
            "all_lags": [
                {
                    "lag": r.lag,
                    "correlation": round(r.correlation, 4),
                    "p_value": round(r.p_value, 4),
                    "significant": r.is_significant,
                    "sample_size": r.sample_size,
                }
                for r in optimal.all_results
            ],
        }

    def _interpret_correlation(self, corr: float) -> str:
        """Текстовая интерпретация коэффициента корреляции"""
        abs_corr = abs(corr)

        if abs_corr >= 0.9:
            strength = "очень сильная"
        elif abs_corr >= 0.7:
            strength = "сильная"
        elif abs_corr >= 0.5:
            strength = "умеренная"
        elif abs_corr >= 0.3:
            strength = "слабая"
        else:
            strength = "очень слабая"

        direction = "положительная" if corr >= 0 else "отрицательная"

        return f"{strength} {direction} связь"

    def __repr__(self):
        return f"TimeSeriesCorrelation(x_len={len(self.series_x)}, y_len={len(self.series_y)})"
