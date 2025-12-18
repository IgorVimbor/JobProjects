# claims/modules/forecast/claims_predictor.py
"""
Модуль прогнозирования сумм претензий на основе рекламаций.

Включает класс:
- `ClaimsPredictor` - Связанный прогноз: рекламации → претензии
"""

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

        Returns:
            self (для цепочки вызовов)
        """
        # 1. Определяем оптимальный лаг (если не задан)
        if self.lag_months is None:
            correlation_analyzer = TimeSeriesCorrelation(
                self.reclamations.tolist(), self.claims_sum.tolist()
            )
            optimal = correlation_analyzer.find_optimal_lag(max_lag=6)
            self.lag_months = optimal.optimal_lag
            correlation = optimal.correlation
        else:
            correlation_analyzer = TimeSeriesCorrelation(
                self.reclamations.tolist(), self.claims_sum.tolist()
            )
            result = correlation_analyzer.calculate_correlation_at_lag(self.lag_months)
            correlation = result.correlation

        # 2. Рассчитываем коэффициент конверсии
        conversion_rate, conversion_std = self._calculate_conversion_rate()

        # 3. Рассчитываем среднюю сумму претензии
        avg_amount, avg_std = self._calculate_average_amount()

        # 4. Обучаем регрессию
        slope, intercept, r_squared, residual_std = self._fit_regression()

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

        self._residual_std = residual_std
        self._is_fitted = True

        return self

    def _calculate_conversion_rate(self) -> Tuple[float, float]:
        """
        Расчёт коэффициента конверсии рекламаций в претензии.

        Returns:
            Tuple[mean_rate, std_rate]
        """
        lag = self.lag_months or 0

        if lag > 0 and lag < len(self.reclamations):
            lagged_recl = self.reclamations[:-lag]
            lagged_claims = self.claims_count[lag:]
        else:
            lagged_recl = self.reclamations
            lagged_claims = self.claims_count

        # Избегаем деления на ноль
        safe_recl = np.maximum(lagged_recl, 1)
        conversion_rates = lagged_claims / safe_recl

        return float(np.mean(conversion_rates)), float(np.std(conversion_rates))

    def _calculate_average_amount(self) -> Tuple[float, float]:
        """
        Расчёт средней суммы претензии.

        Returns:
            Tuple[mean_amount, std_amount]
        """
        # Избегаем деления на ноль
        safe_claims = np.maximum(self.claims_count, 1)
        avg_amounts = self.claims_sum / safe_claims

        # Фильтруем выбросы (значения вне 3 сигм)
        mean_amt = np.mean(avg_amounts)
        std_amt = np.std(avg_amounts)

        if std_amt > 0:
            mask = np.abs(avg_amounts - mean_amt) <= 3 * std_amt
            filtered = avg_amounts[mask]
            if len(filtered) > 0:
                return float(np.mean(filtered)), float(np.std(filtered))

        return float(mean_amt), float(std_amt)

    def _fit_regression(self) -> Tuple[float, float, float, float]:
        """
        Обучение линейной регрессии: рекламации → сумма претензий.

        Returns:
            Tuple[slope, intercept, r_squared, residual_std]
        """
        lag = self.lag_months or 0

        if lag > 0 and lag < len(self.reclamations):
            X = self.reclamations[:-lag]
            y = self.claims_sum[lag:]
        else:
            X = self.reclamations
            y = self.claims_sum

        if len(X) < 2:
            return 0.0, float(np.mean(y)) if len(y) > 0 else 0.0, 0.0, 0.0

        # Линейная регрессия через numpy
        X_with_bias = np.vstack([X, np.ones(len(X))]).T
        coeffs, residuals, rank, s = np.linalg.lstsq(X_with_bias, y, rcond=None)

        slope, intercept = coeffs[0], coeffs[1]

        # R² (коэффициент детерминации)
        y_pred = slope * X + intercept
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

        # Стандартное отклонение остатков
        residual_std = np.std(y - y_pred)

        return float(slope), float(intercept), float(r_squared), float(residual_std)

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

        # Z-score для доверительного интервала
        if self.confidence_level == 0.95:
            z_score = 1.96
        elif self.confidence_level == 0.99:
            z_score = 2.576
        else:
            z_score = 1.96

        predictions = []

        for i, recl_count in enumerate(future_reclamations):
            # Основной прогноз через регрессию
            predicted_sum = (
                coef.regression_slope * recl_count + coef.regression_intercept
            )
            predicted_sum = max(0, predicted_sum)

            # Доверительный интервал
            margin = z_score * self._residual_std
            ci_lower = max(0, predicted_sum - margin)
            ci_upper = predicted_sum + margin

            # Ожидаемое количество претензий
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
                "formula": f"Сумма = {coef.regression_slope:.2f} × Рекламации + {coef.regression_intercept:.0f}",
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
