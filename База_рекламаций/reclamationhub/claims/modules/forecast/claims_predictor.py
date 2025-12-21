# claims/modules/forecast/claims_predictor.py
"""
Модуль прогнозирования сумм претензий на основе рекламаций.

Включает классы:
- `ClaimPrediction` - Датакласс результатов прогноза для одного периода
- `ModelCoefficients` - Датакласс коэффициентов модели прогноза
- `ClaimsPredictor` - Связанный прогноз: рекламации → претензии
"""
# СВЯЗАННЫЙ МЕТОД (linked):
# 1. Прогноз РЕКЛАМАЦИЙ → делается сезонным методом (независимо)
# 2. Прогноз КОЛИЧЕСТВА ПРЕТЕНЗИЙ → рекламации × коэффициент конверсии
# 3. Прогноз СУММ ПРЕТЕНЗИЙ → через регрессию от рекламаций
#    Формула: Сумма = slope × Рекламации + intercept
# 4. Доверительный интервал → только для СУММ (п.3)

import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from .base import BaseForecast
from .correlation import TimeSeriesCorrelation
from .seasonal import SeasonalForecast


@dataclass
class ClaimPrediction:
    """Результат прогноза для одного периода"""

    period_index: int
    predicted_sum: float
    confidence_lower: float
    confidence_upper: float
    base_reclamations: int
    expected_claims_count: float


@dataclass
class ModelCoefficients:
    """Коэффициенты модели прогноза"""

    lag_months: int
    correlation: float
    conversion_rate: float
    conversion_std: float
    avg_claim_amount: float
    avg_claim_std: float
    regression_slope: float
    regression_intercept: float
    r_squared: float


class ClaimsPredictor(BaseForecast):
    """
    Прогнозирование сумм претензий на основе рекламаций.

    Модель:
    Claims_sum(t + lag) = f(Reclamations(t), Conversion_rate, Avg_amount)

    Компоненты:
    1. Временной лаг (автоопределение через корреляцию)
    2. Коэффициент конверсии (рекламации → претензии)
    3. Средняя сумма претензии
    4. Линейная регрессия для корректировки

    Использование:
        predictor = ClaimsPredictor(reclamations, claims_count, claims_sum)
        predictor.fit()
        predictions = predictor.predict(future_reclamations)
    """

    def __init__(
        self,
        reclamations_history: List[int],
        claims_count_history: List[int],
        claims_sum_history: List[float],
        lag_months: Optional[int] = None,
        confidence_level: float = 0.95,
    ):
        """
        Args:
            reclamations_history: История количества рекламаций по месяцам
            claims_count_history: История количества претензий по месяцам
            claims_sum_history: История сумм претензий по месяцам
            lag_months: Фиксированный лаг (если None - определится автоматически)
            confidence_level: Уровень доверия для интервалов (0.95 = 95%)
        """
        self.reclamations = np.array(reclamations_history, dtype=float)
        self.claims_count = np.array(claims_count_history, dtype=float)
        self.claims_sum = np.array(claims_sum_history, dtype=float)

        self.lag_months = lag_months
        self.confidence_level = confidence_level

        self._is_fitted = False
        self._coefficients: Optional[ModelCoefficients] = None

    def fit(self) -> "ClaimsPredictor":
        """
        Обучение модели: расчёт всех коэффициентов.
        Это процесс анализа исторических данных для нахождения закономерностей,
        которые потом используются для прогноза.

        ЭТАПЫ ОБУЧЕНИЯ:
        1. НАЙТИ ЛАГ
            Через сколько месяцев после рекламации приходит претензия?
        2. РАССЧИТАТЬ КОНВЕРСИЮ
            Какой % рекламаций становится претензиями?
        3. РАССЧИТАТЬ СРЕДНЮЮ СУММУ
            Сколько в среднем стоит одна претензия?
        4. ОБУЧИТЬ РЕГРЕССИЮ
            Найти формулу: Сумма = slope × Рекламации + intercept

        Returns:
            self — для возможности цепочки вызовов: predictor.fit().predict(data)
        """
        # ============ ЭТАП 1: ОПРЕДЕЛЕНИЕ ОПТИМАЛЬНОГО ЛАГА ============
        if self.lag_months is None:
            # Создаём анализатор корреляции
            correlation_analyzer = TimeSeriesCorrelation(
                self.reclamations.tolist(),  # Причина (X)
                self.claims_sum.tolist(),  # Следствие (Y)
            )
            # Ищем лаг с максимальной корреляцией (от 0 до 6 месяцев)
            optimal = correlation_analyzer.find_optimal_lag(max_lag=6)
            self.lag_months = optimal.optimal_lag
            correlation = optimal.correlation
        else:
            # Лаг задан вручную — просто считаем корреляцию для него
            correlation_analyzer = TimeSeriesCorrelation(
                self.reclamations.tolist(), self.claims_sum.tolist()
            )
            result = correlation_analyzer.calculate_correlation_at_lag(self.lag_months)
            correlation = result.correlation

        # ============ ЭТАП 2: РАСЧЁТ КОЭФФИЦИЕНТА КОНВЕРСИИ ============
        conversion_rate, conversion_std = self._calculate_conversion_rate()

        # ============ ЭТАП 3: РАСЧЁТ СРЕДНЕЙ СУММЫ ПРЕТЕНЗИИ ============
        # Средняя сумма —> сколько в среднем "стоит" одна претензия.
        # Средняя_сумма = Общая_сумма_претензий / Количество_претензий
        avg_amount, avg_std = self._calculate_average_amount()

        # ============ ЭТАП 4: ОБУЧЕНИЕ ЛИНЕЙНОЙ РЕГРЕССИИ ============
        # Находим формулу прямой линии:
        # Сумма_претензий = slope × Рекламации + intercept

        # slope — наклон (сколько BYN на 1 рекламацию)
        # intercept — базовый уровень (сумма при 0 рекламаций)
        # r_squared — качество модели (0-1, чем больше тем лучше)
        # residual_std — средняя ошибка (для доверительного интервала)
        slope, intercept, r_squared, residual_std = self._fit_regression()

        # ============ СОХРАНЕНИЕ КОЭФФИЦИЕНТОВ ============
        self._coefficients = ModelCoefficients(
            lag_months=self.lag_months,
            correlation=correlation,
            conversion_rate=conversion_rate,
            conversion_std=conversion_std,
            avg_claim_amount=avg_amount,
            avg_claim_std=avg_std,
            regression_slope=slope,
            regression_intercept=intercept,
            r_squared=r_squared,
        )

        # Сохраняем ошибку для расчёта доверительного интервала
        self._residual_std = residual_std

        self._is_fitted = True  # Отмечаем, что модель обучена

        return self

    def _calculate_conversion_rate(self) -> Tuple[float, float]:
        """
        Расчёт коэффициента конверсии рекламаций в претензии.

        Returns:
            Tuple[mean_rate, std_rate]
        """
        lag = self.lag_months or 0

        if lag > 0 and lag < len(self.reclamations) and lag < len(self.claims_count):
            lagged_recl = self.reclamations[:-lag]
            lagged_claims = self.claims_count[lag:]
        else:
            lagged_recl = self.reclamations
            lagged_claims = self.claims_count

        # Синхронизируем длины
        min_len = min(len(lagged_recl), len(lagged_claims))
        if min_len == 0:
            return 0.0, 0.0

        lagged_recl = lagged_recl[:min_len]
        lagged_claims = lagged_claims[:min_len]

        # Избегаем деления на ноль
        safe_recl = np.maximum(lagged_recl, 1)
        conversion_rates = lagged_claims / safe_recl

        return float(np.mean(conversion_rates)), float(np.std(conversion_rates))

    def _calculate_average_amount(self) -> Tuple[float, float]:
        """
        Расчёт средней суммы претензии.

        -------- АЛГОРИТМ --------
        1. Для каждого месяца считаем: сумма_претензий / количество_претензий
        2. Находим среднее этих значений
        3. Отфильтровываем выбросы (значения вне 3 сигм)

        Returns:
            Tuple[средняя_сумма, стандартное_отклонение]
        """

        # ============= СЧИТАЕМ СРЕДНЮЮ СУММУ для каждого месяца ===============
        # safe_claims — защита от деления на 0
        # Если в месяце 0 претензий, считаем как 1 (чтобы не было inf)
        # ──────────────────────────────────────────────────────────────────────
        safe_claims = np.maximum(self.claims_count, 1)  # Избегаем деления на ноль
        avg_amounts = self.claims_sum / safe_claims

        # ======== Фильтрация выбросов по правилу "3 сигм" (исключаем выбросы вне 3 сигм) =========
        # Выброс — это аномально большое или малое значение.

        # Правило 3 сигм:
        # 99.7% нормальных данных лежат в пределах: среднее ± 3 × стандартное_отклонение

        # Пример:
        # Средняя сумма = 10 000, std = 2 000
        # Границы: 10000 - 6000 = 4000 ... 10000 + 6000 = 16000
        # Значение 50 000 — выброс (исключаем)
        # ────────────────────────────────────────────────────────────
        mean_amt = np.mean(avg_amounts)
        std_amt = np.std(avg_amounts)

        if std_amt > 0:
            # Маска: True для значений в пределах 3 сигм
            mask = np.abs(avg_amounts - mean_amt) <= 3 * std_amt
            filtered = avg_amounts[mask]
            if len(filtered) > 0:
                return float(np.mean(filtered)), float(np.std(filtered))

        return float(mean_amt), float(std_amt)

    def _fit_regression(self) -> Tuple[float, float, float, float]:
        """
        Обучение линейной регрессии: рекламации → сумма претензий.

        Находит оптимальные slope и intercept для формулы:
        Сумма претензий = slope × Рекламации + intercept
        """
        lag = self.lag_months or 0

        # =========== ПОДГОТОВКА ДАННЫХ С УЧЁТОМ ЛАГА ==============
        # Если лаг = 3, то:
        # - Берём рекламации БЕЗ последних 3 месяцев (X)
        # - Берём претензии БЕЗ первых 3 месяцев (y)
        # Так мы сопоставляем: рекламации января → претензии апреля
        # ==========================================================
        if lag > 0 and lag < len(self.reclamations) and lag < len(self.claims_sum):
            X = self.reclamations[:-lag]  # Рекламации (причина)
            y = self.claims_sum[lag:]  # Претензии (позже рекламаций на lag месяцев)
        else:
            X = self.reclamations
            y = self.claims_sum

        # Синхронизируем длины массивов
        min_len = min(len(X), len(y))
        if min_len < 2:
            return 0.0, float(np.mean(y)) if len(y) > 0 else 0.0, 0.0, 0.0

        X = X[:min_len]
        y = y[:min_len]

        # ===== ЛИНЕЙНАЯ РЕГРЕССИЯ через метод наименьших квадратов (numpy) ======
        # Задача: найти slope и intercept, чтобы линия y = slope ꞏ X + intercept
        # была максимально близка ко всем точкам данных.
        #
        # X_with_bias — добавляем столбец единиц для расчёта intercept
        # [[x1, 1],
        #  [x2, 1],
        #  [x3, 1], ...]
        # ========================================================================
        X_with_bias = np.vstack([X, np.ones(len(X))]).T

        try:
            # np.linalg.lstsq — "least squares" (наименьшие квадраты)
            # Находит коэффициенты, минимизирующие сумму квадратов ошибок
            coeffs, residuals, rank, s = np.linalg.lstsq(X_with_bias, y, rcond=None)
            slope, intercept = coeffs[0], coeffs[1]
        except Exception:
            # Fallback при ошибке
            slope = 0.0
            intercept = float(np.mean(y))

        # ============ R² (R-SQUARED) — КОЭФФИЦИЕНТ ДЕТЕРМИНАЦИИ =================
        # Показывает, какую долю вариации Y объясняет модель.
        # R² = 1 - (SS_res / SS_tot)
        #    SS_res — сумма квадратов остатков (ошибок модели)
        #    SS_tot — общая сумма квадратов (разброс данных)
        # R² = 1.0 → модель идеально предсказывает (все точки на линии)
        # R² = 0.7 → модель объясняет 70% вариации (хорошо)
        # R² = 0.3 → модель объясняет 30% (слабо, много "шума")
        # ========================================================================
        y_pred = slope * X + intercept  # Предсказанные значения
        ss_res = np.sum((y - y_pred) ** 2)  # Сумма квадратов ошибок
        ss_tot = np.sum((y - np.mean(y)) ** 2)  # Общий разброс данных
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

        # ============ СТАНДАРТНОЕ ОТКЛОНЕНИЕ ОСТАТКОВ (residual_std) ============
        # Это "средняя ошибка" модели — на сколько в среднем реальные значения
        # отличаются от предсказанных.
        # Используется для расчёта доверительного интервала:
        #    CI = прогноз ± (1.96 × residual_std)
        # ========================================================================
        residual_std = float(np.std(y - y_pred))

        return float(slope), float(intercept), float(r_squared), residual_std

    def predict(self, future_reclamations: List[int]) -> List[ClaimPrediction]:
        """
        Прогноз сумм претензий на основе прогноза рекламаций.

        Args:
            future_reclamations: Прогноз количества рекламаций на будущие периоды

        Returns:
            List[ClaimPrediction]
        """
        if not self._is_fitted:
            self.fit()

        coef = self._coefficients

        # =========== Z-score для доверительного интервала ==============
        # 1.96 — это значение из таблицы нормального распределения
        # При 95% доверии: 2.5% вероятности слева, 2.5% справа
        # Интервал: [прогноз - 1.96×ошибка, прогноз + 1.96×ошибка]
        # ===============================================================
        if self.confidence_level == 0.95:
            z_score = 1.96
        elif self.confidence_level == 0.99:
            z_score = 2.576  # Для 99% доверия — шире интервал
        else:
            z_score = 1.96

        predictions = []

        for i, recl_count in enumerate(future_reclamations):
            # =========== ОСНОВНОЙ ПРОГНОЗ: линейная регрессия ===========
            # Формула: y = slope × x + intercept
            #
            # slope (наклон) — сколько BYN добавляет каждая рекламация
            # intercept — базовый уровень претензий при 0 рекламаций
            #
            # Пример: slope=500, intercept=5000, рекламаций=50
            #         прогноз = 500 × 50 + 5000 = 30000 BYN
            # ============================================================
            predicted_sum = (
                coef.regression_slope * recl_count + coef.regression_intercept
            )
            predicted_sum = max(0, predicted_sum)  # Сумма не может быть отрицательной

            # =========== ДОВЕРИТЕЛЬНЫЙ ИНТЕРВАЛ =========================
            # margin = z_score × стандартная_ошибка_модели
            #
            # Это "запас погрешности" — насколько реальное значение может отличаться от прогноза.
            #
            # Пример: прогноз=30000, margin=5000, интервал = [25000, 35000]
            #         "С вероятностью 95% сумма будет от 25000 до 35000"
            # ============================================================
            margin = z_score * self._residual_std
            ci_lower = max(0, predicted_sum - margin)
            ci_upper = predicted_sum + margin

            # =========== ОЖИДАЕМОЕ КОЛИЧЕСТВО ПРЕТЕНЗИЙ =================
            # claims = количество рекламаций × коэффициент конверсии
            #
            # Пример: 50 рекламаций × 0.15 (15%) = 7.5 претензий
            # ============================================================
            expected_claims = recl_count * coef.conversion_rate

            predictions.append(
                ClaimPrediction(
                    period_index=i,
                    predicted_sum=round(predicted_sum, 2),
                    confidence_lower=round(ci_lower, 2),
                    confidence_upper=round(ci_upper, 2),
                    base_reclamations=int(recl_count),
                    expected_claims_count=round(expected_claims, 1),
                )
            )

        return predictions

    def forecast(
        self,
        historical_data: List[float],
        forecast_months: int,
        round_decimals: int = 2,
    ) -> List[float]:
        """
        Реализация абстрактного метода из BaseForecast.

        Для полноценного прогноза используйте predict() с прогнозом рекламаций.
        Этот метод делает прогноз на основе продолжения последних рекламаций.
        """
        if not self._is_fitted:
            self.fit()

        # Прогнозируем рекламации сезонным методом
        seasonal = SeasonalForecast(method="auto")
        future_recl = seasonal.forecast(
            self.reclamations.tolist(), forecast_months, round_decimals=0
        )

        # Прогнозируем претензии
        predictions = self.predict(future_recl)

        return [p.predicted_sum for p in predictions]

    def get_coefficients(self) -> Dict:
        """
        Возвращает коэффициенты модели для отображения.

        Returns:
            Dict с коэффициентами
        """
        if not self._is_fitted:
            self.fit()

        coef = self._coefficients
        return {
            "lag_months": coef.lag_months,
            "correlation": round(coef.correlation, 4),
            "conversion_rate": round(coef.conversion_rate, 4),
            "conversion_rate_pct": f"{coef.conversion_rate * 100:.1f}%",
            "avg_claim_amount": round(coef.avg_claim_amount, 2),
            "r_squared": round(coef.r_squared, 4),
            "r_squared_pct": f"{coef.r_squared * 100:.1f}%",
            "regression_formula": f"y = {coef.regression_slope:.2f} × x + {coef.regression_intercept:.2f}",
        }

    def get_full_analysis(self) -> Dict:
        """
        Полный анализ модели для API/шаблонов.
        """
        if not self._is_fitted:
            self.fit()

        coef = self._coefficients

        return {
            "model_quality": {
                "r_squared": round(coef.r_squared, 4),
                "quality_interpretation": self._interpret_r_squared(coef.r_squared),
            },
            "time_lag": {
                "months": coef.lag_months,
                "correlation": round(coef.correlation, 4),
                "interpretation": f"Рекламации влияют на претензии через {coef.lag_months} мес.",
            },
            "conversion": {
                "rate": round(coef.conversion_rate, 4),
                "rate_pct": f"{coef.conversion_rate * 100:.1f}%",
                "std": round(coef.conversion_std, 4),
            },
            "claim_amount": {
                "average": round(coef.avg_claim_amount, 2),
                "std": round(coef.avg_claim_std, 2),
            },
            "regression": {
                "slope": round(coef.regression_slope, 4),
                "intercept": round(coef.regression_intercept, 2),
                "formula": f"СУММА ПРЕТЕНЗИЙ = {coef.regression_slope:.2f} × Рекламации + {coef.regression_intercept:.0f}",
            },
        }

    def _interpret_r_squared(self, r2: float) -> str:
        """Интерпретация R²"""
        if r2 >= 0.9:
            return "отличное качество модели"
        elif r2 >= 0.7:
            return "хорошее качество модели"
        elif r2 >= 0.5:
            return "удовлетворительное качество"
        elif r2 >= 0.3:
            return "слабая предсказательная способность"
        else:
            return "модель не объясняет вариацию данных"

    def __repr__(self):
        status = "fitted" if self._is_fitted else "not fitted"
        return f"ClaimsPredictor({status}, lag={self.lag_months})"
