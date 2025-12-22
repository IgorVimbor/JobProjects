# claims/modules/forecast/correlation.py
"""
Модуль кросс-корреляции временных рядов.

Включает классы:
- `TimeSeriesCorrelation` - Анализ корреляции с учётом лага
- `LagCorrelationResult` - Результат для одного лага
- `OptimalLagResult` - Результат поиска оптимального лага
"""

"""
Что делает:
    Анализирует СВЯЗЬ между двумя временными рядами
    (например, рекламации и суммы претензий) и находит
    ВРЕМЕННОЙ СДВИГ (лаг) между ними.

Зачем это нужно:
    Рекламация сегодня → Претензия через 3 месяца
    Чтобы прогнозировать претензии, нужно знать этот сдвиг.

Что такое корреляция:
    Это число от -1 до +1, показывающее силу связи:

    +1.0 = идеальная прямая связь (больше X → больше Y)
     0.0 = нет связи (X и Y независимы)
    -1.0 = идеальная обратная связь (больше X → меньше Y)
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class LagCorrelationResult:
    """
    Результат корреляции для конкретного лага

    Атрибуты:
        lag: Временной сдвиг в месяцах (0, 1, 2, ...)
        correlation: Коэффициент корреляции (-1 до +1)
        p_value: Статистическая значимость (меньше 0.05 = значимо)
        is_significant: True если p_value < 0.05
        sample_size: Количество пар точек для расчёта
    """

    lag: int
    correlation: float
    p_value: float
    is_significant: bool
    sample_size: int


@dataclass
class OptimalLagResult:
    """
    Результат поиска оптимального лага.

    Атрибуты:
        optimal_lag: Лаг с максимальной корреляцией
        correlation: Значение корреляции при оптимальном лаге
        p_value: Статистическая значимость
        all_results: Результаты для всех проверенных лагов
    """

    optimal_lag: int
    correlation: float
    p_value: float
    all_results: List[LagCorrelationResult]


class TimeSeriesCorrelation:
    """
    Анализ кросс-корреляции временных рядов с поиском оптимального лага.

    Кросс-корреляция - способ измерить, насколько один ряд "похож" на другой
    при разных сдвигах во времени.

    Используется для определения временной задержки между количеством рекламаций
    и суммами претензий.
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
            significance_level: Уровень значимости для статистических тестов (по умолчанию 0.05).
                0.05 = 95% уверенность (стандарт)
                0.01 = 99% уверенность (строже)
        """
        self.series_x = np.array(series_x, dtype=float)
        self.series_y = np.array(series_y, dtype=float)
        self.significance_level = significance_level

        # ============ ПРОВЕРКА НАЛИЧИЯ SCIPY ============
        # scipy даёт точный p-value для корреляции.
        # Если scipy нет — используем приближённый расчёт.
        try:
            from scipy import stats

            self._stats = stats
            self._has_scipy = True
        except ImportError:
            self._has_scipy = False

    def _pearson_correlation(self, x: np.ndarray, y: np.ndarray) -> Tuple[float, float]:
        """
        Расчёт коэффициента корреляции Пирсона.

        Корреляция Пирсона измеряет ЛИНЕЙНУЮ связь между двумя переменными.
        Формула (упрощённо):
        r = Σ((x - x̄)(y - ȳ)) / √(Σ(x - x̄)² × Σ(y - ȳ)²)

        Где:
        - x̄, ȳ — средние значения
        - Числитель — "совместное отклонение" (ковариация)
        - Знаменатель — произведение стандартных отклонений

        Args:
            x: Первый массив значений
            y: Второй массив значений (той же длины)

        Returns:
            Tuple[correlation, p_value]
            - correlation: от -1 до +1
            - p_value: вероятность, что связь случайна (< 0.05 = связь статистически значима)
        """
        # Нужно минимум 3 точки для осмысленной корреляции
        if len(x) < 3:
            return 0.0, 1.0

        if self._has_scipy:
            # Точный расчёт через scipy
            corr, p_value = self._stats.pearsonr(x, y)
            return float(corr), float(p_value)
        else:
            # Ручной расчёт без scipy
            n = len(x)
            mean_x, mean_y = np.mean(x), np.mean(y)

            # Числитель: сумма произведений отклонений
            numerator = np.sum((x - mean_x) * (y - mean_y))
            # Знаменатель: произведение "размахов"
            denominator = np.sqrt(np.sum((x - mean_x) ** 2) * np.sum((y - mean_y) ** 2))

            if denominator == 0:
                return 0.0, 1.0

            corr = numerator / denominator

            # Приближённый p-value через t-статистику: t = r × √((n-2) / (1-r²))
            # Чем больше t, тем меньше p-value (значимее связь)
            if abs(corr) >= 1:
                p_value = 0.0
            else:
                t_stat = corr * np.sqrt((n - 2) / (1 - corr**2))
                # Грубое приближение p-value
                p_value = 2 * (1 - min(0.99, abs(t_stat) / 10))

            return float(corr), float(p_value)

    def calculate_correlation_at_lag(self, lag: int) -> LagCorrelationResult:
        """
        Расчёт корреляции при заданном лаге.

        Лаг — это сдвиг во времени (период времиени) между двумя рядами.
        lag > 0: series_x опережает series_y на lag (рекламации в момент t влияют на претензии t+lag)

        Args:
            lag: Временной сдвиг (положительный = X опережает Y)

        Returns:
            LagCorrelationResult с корреляцией и статистикой
        """
        n_x = len(self.series_x)  # Длина массива series_x
        n_y = len(self.series_y)  # Длина массива series_y

        # ФОРМИРОВАНИЕ СОПОСТАВИМЫХ МАССИВОВ
        if lag == 0:
            # Без сдвига — берём минимальную длину
            min_len = min(n_x, n_y)
            x = self.series_x[:min_len]
            y = self.series_y[:min_len]
        elif lag > 0:
            # ───────────────────────────────────────────────────────────────────────────────
            # X опережает Y: рекламации РАНЬШЕ, претензии ПОЗЖЕ. X[:-lag] соответствует Y[lag:]
            # X[:-lag] = все элементы кроме последних lag
            # Y[lag:]  = все элементы начиная с индекса lag
            # ───────────────────────────────────────────────────────────────────────────────
            if lag >= n_x or lag >= n_y:
                # Лаг слишком большой — данных не хватает
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
            # Y опережает X (отрицательный лаг) — редкий случай
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

        # СИНХРОНИЗАЦИЯ ДЛИН (защита от рассинхрона)
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

        # РАСЧЁТ КОРРЕЛЯЦИИ
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

        Перебирает все лаги от min_lag до max_lag и находит тот, при котором корреляция максимальна.

        Args:
            max_lag: Максимальный лаг для проверки (обычно 6)
            min_lag: Минимальный лаг (обычно 0)

        Returns:
            OptimalLagResult с лучшим лагом и всеми результатами
        """
        results = []

        # ПЕРЕБОР ВСЕХ ЛАГОВ
        for lag in range(min_lag, max_lag + 1):
            result = self.calculate_correlation_at_lag(lag)
            results.append(result)

        # ПОИСК МАКСИМУМА (лаг с максимальной абсолютной корреляцией)
        # ───────────────────────────────────────────────────────────────────────
        # Используем abs() потому что сильная отрицательнаякорреляция тоже важна
        # (хотя для рекламаций/претензий ожидаем положительную)
        # ───────────────────────────────────────────────────────────────────────
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

        Возвращает все результаты в формате, готовом для JSON-сериализации и отображения в UI.

        Returns:
            Словарь с ключами:
            - optimal_lag: лучший лаг
            - optimal_correlation: корреляция при лучшем лаге
            - p_value: статистическая значимость
            - is_significant: значима ли связь
            - interpretation: текстовое описание силы связи
            - all_lags: список результатов для всех лагов
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
        """
        Текстовая интерпретация коэффициента корреляции

        Шкала (общепринятая):
            |r| >= 0.9  — очень сильная связь
            |r| >= 0.7  — сильная связь
            |r| >= 0.5  — умеренная связь
            |r| >= 0.3  — слабая связь
            |r| <  0.3  — очень слабая связь

        Знак:
            r > 0 — положительная (X↑ → Y↑)
            r < 0 — отрицательная (X↑ → Y↓)
        """
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
