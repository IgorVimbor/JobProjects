# claims/modules/claim_prognosis_processor.py
"""
Процессор для прогнозирования методами статистического анализа и машинного обучения.

Методы прогнозирования:
1. statistical — Скользящее среднее + тренд (3 режима: conservative/balanced/aggressive)
2. ml — Машинное обучение (3 модели: linear/ridge/polynomial)
3. seasonal — Сезонный прогноз с учётом колебаний
4. linked — Связанный прогноз: рекламации → претензии с учётом лага

Включает класс:
- `ClaimPrognosisProcessor` - Оркестратор: главный "дирижёр" прогнозирования.
Собирает данные, выбирает метод, запускает расчёты, форматирует результаты.
"""

from datetime import date
from dateutil.relativedelta import relativedelta
import numpy as np

import matplotlib

matplotlib.use("Agg")  # Бэкенд без GUI для серверного рендеринга
import matplotlib.pyplot as plt

from claims.modules.forecast import (
    StatisticalForecast,
    MachineLearningForecast,
    SeasonalForecast,
    ClaimsPredictor,
    TimeSeriesCorrelation,
)

from reports.config.paths import (
    get_claim_prognosis_chart_path,
    BASE_REPORTS_DIR,
)


class ClaimPrognosisProcessor:
    """
    Процессор прогнозирования претензий (оркестратор)

    ЗАДАЧИ:
    1. Получить исторические данные из БД
    2. Выбрать и настроить метод прогнозирования
    3. Запустить расчёты
    4. Объединить факт и прогноз для графика
    5. Сформировать результат для отображения

    Поддерживает методы:
    1-3. Статистические (консервативный, сбалансированный, агрессивный)
    4-6. Машинное обучение (linear, ridge, polynomial)
    7.   Сезонный (пока только наивный прогноз naive)
    8.   Связанный (рекламации → претензии с лагом)
    """

    # ========== КОНСТАНТЫ ==========

    # Названия месяцев для отображения на графике и в таблице
    MONTH_NAMES = {
        1: "Янв",
        2: "Фев",
        3: "Мар",
        4: "Апр",
        5: "Май",
        6: "Июн",
        7: "Июл",
        8: "Авг",
        9: "Сен",
        10: "Окт",
        11: "Ноя",
        12: "Дек",
    }

    # Описания методов для UI (форма выбора)
    METHOD_DESCRIPTIONS = {
        "statistical": "Скользящее среднее + тренд",
        "ml": "Машинное обучение",
        "seasonal": "Сезонный прогноз (учёт колебаний)",
        "linked": "Связанный прогноз (рекламации → претензии)",
    }

    # ========== ИНИЦИАЛИЗАЦИЯ ==========

    def __init__(
        self,
        year=None,
        consumers=None,
        forecast_months=6,
        exchange_rate=None,
        forecast_method="statistical",
        statistical_mode="balanced",
        ml_model="linear",
        seasonal_type="mul",
    ):
        """
        Args:
            year (int): Год исторических данных для анализа. По умолчанию: текущий год
            consumers (list): Список потребителей для фильтрации. Пустой список = все потребители
            forecast_months (int): Период прогноза (3, 6 или 12 месяцев). По умолчанию: 6
            exchange_rate (Decimal): Курс конвертации RUR → BYN. По умолчанию: 0.03
            forecast_method (str): Метод прогнозирования:
                - "statistical" → скользящее среднее + тренд
                - "ml" → машинное обучение
                - "seasonal" → сезонный прогноз
                - "linked" → связанный прогноз
            statistical_mode (str): Режим для statistical метода:
                - "conservative" → сглаживание, медленная реакция
                - "balanced" → универсальный (по умолчанию)
                - "aggressive" → быстрая реакция на тренд
            ml_model (str): Модель для ml метода:
                - "linear" → линейная регрессия (по умолчанию)
                - "ridge" → регуляризованная регрессия
                - "polynomial" → полиномиальный тренд
            seasonal_type (str): Тип сезонности:
                - "mul" → мультипликативная (амплитуда растёт с уровнем)
                - "add" → аддитивная (амплитуда постоянная)
        """
        # Базовые параметры
        self.today = date.today()
        self.year = year or self.today.year
        self.consumers = consumers or []
        self.all_consumers_mode = len(self.consumers) == 0  # Флаг "все потребители"
        self.forecast_months = forecast_months or 6
        self.exchange_rate = exchange_rate or 0.03

        # Параметры методов прогнозирования
        self.forecast_method = forecast_method
        self.statistical_mode = statistical_mode
        self.ml_model = ml_model
        self.seasonal_type = seasonal_type

        # Создаем экземпляр forecaster'а (прогнозировщика)
        # forecaster — это объект, который делает расчёты.
        # Тип объекта зависит от выбранного метода.
        self.forecaster = self._create_forecaster()

        # Результаты анализа корреляции (заполняется при linked)
        self._correlation_analysis = None  # Результат корреляционного анализа
        self._linked_model_info = None  # Информация о модели связанного прогноза

    def _create_forecaster(self):
        """
        Фабричный метод создания forecaster'а (прогнозировщика) нужного типа.
        Это паттерн проектирования.

        Returns:
            BaseForecast: экземпляр прогнозировщика нужного типа
        """
        if self.forecast_method == "statistical":
            # ────────────────────────────────────────────────────
            # Статистический: скользящее среднее + линейный тренд
            # Подходит для: стабильных данных без резких скачков
            # ────────────────────────────────────────────────────
            return StatisticalForecast(mode=self.statistical_mode)
        elif self.forecast_method == "ml":
            # ────────────────────────────────────────────────────
            # Машинное обучение: регрессионные модели sklearn
            # Подходит для: данных с чётким трендом
            # ────────────────────────────────────────────────────
            return MachineLearningForecast(model=self.ml_model)
        elif self.forecast_method == "seasonal":
            # ────────────────────────────────────────────────────
            # Сезонный: учитывает повторяющиеся пики и спады
            # Подходит для: данных с явной сезонностью
            # ────────────────────────────────────────────────────
            return SeasonalForecast(
                method="auto", seasonal_period=12, seasonal_type=self.seasonal_type
            )
        elif self.forecast_method == "linked":
            # ────────────────────────────────────────────────────
            # Связанный: прогноз претензий на основе рекламаций
            # Подходит для: когда претензии "следуют" за рекламациями
            #
            # Для рекламаций используем SeasonalForecast
            # ClaimsPredictor будет создан позже с данными
            # ────────────────────────────────────────────────────
            return SeasonalForecast(
                method="auto", seasonal_period=12, seasonal_type=self.seasonal_type
            )
        else:
            # Fallback
            return StatisticalForecast(mode="balanced")

    # ========== ПОЛУЧЕНИЕ ИСТОРИЧЕСКИХ ДАННЫХ ==========

    def _get_historical_data(self):
        """
        Получение исторических данных из БД через TimeAnalysisProcessor

        Returns:
            dict: данные по месяцам (рекламации, претензии количество, претензии суммы)
        """
        from claims.modules.time_analysis_processor import TimeAnalysisProcessor

        time_processor = TimeAnalysisProcessor(
            year=self.year,
            consumers=self.consumers,
            exchange_rate=float(self.exchange_rate),
        )

        monthly_data = time_processor.get_monthly_distribution()

        return {
            "labels": monthly_data["labels"],
            "labels_formatted": monthly_data["labels_formatted"],
            "reclamations": monthly_data["reclamations"],
            "claims": monthly_data["claims_counts"],
            "claims_costs": monthly_data["claims_costs"],
        }

    # ========== БАЗОВЫЕ МЕТОДЫ ПРОГНОЗИРОВАНИЯ ==========
    # Эти методы используют self.forecaster — объект, созданный в _create_forecaster()

    def _forecast_reclamations(self, historical_reclamations):
        """
        Прогноз количества рекламаций.

        Используется во ВСЕХ методах прогнозирования.
        Рекламации прогнозируются независимо от претензий.

        Args:
            historical_reclamations: список исторических значений

        Returns:
            list: прогноз на forecast_months периодов
        """
        return self.forecaster.forecast(
            historical_reclamations, self.forecast_months, round_decimals=0
        )

    def _forecast_claims_count(self, historical_claims):
        """
        Прогноз количества претензий (НЕЗАВИСИМЫЙ)

        Используется в методах: statistical, ml, seasonal.
        НЕ используется в linked (там количество = рекламации × расчитанную конверсию).

        Args:
            historical_claims: список исторических значений

        Returns:
            list: прогноз на forecast_months периодов
        """
        return self.forecaster.forecast(
            historical_claims, self.forecast_months, round_decimals=0
        )

    def _forecast_claim_costs(self, historical_costs):
        """
        Прогноз сумм претензий (НЕЗАВИСИМЫЙ)

        Используется в методах: statistical, ml, seasonal.
        НЕ используется в linked (там суммы через регрессию от рекламаций).

        Args:
            historical_costs: список исторических сумм

        Returns:
            list: прогноз на forecast_months периодов
        """
        return self.forecaster.forecast(
            historical_costs, self.forecast_months, round_decimals=2
        )

    # =========== СВЯЗАННЫЙ ПРОГНОЗ (LINKED) =============

    def _analyze_correlation(self, reclamations, claims_costs):
        """
        Анализ корреляции между рекламациями и суммами претензий.

        Корреляция показывает:
            1. Есть ли связь между рекламациями и претензиями?
            2. Насколько она сильная?
            3. Какой временной лаг (через сколько месяцев)?

        Если корреляция низкая — linked метод не имеет смысла.

        Args:
            reclamations: список количества рекламаций
            claims_costs: список сумм претензий

        Returns:
            dict с результатами анализа
        """
        # Минимум 6 точек для осмысленного анализа
        if len(reclamations) < 6 or len(claims_costs) < 6:
            return {
                "optimal_lag": 3,  # Значение по умолчанию
                "correlation": 0.0,
                "is_significant": False,
                "error": "Недостаточно данных для анализа корреляции",
            }

        # Создаём анализатор и запускаем анализ
        correlation_analyzer = TimeSeriesCorrelation(reclamations, claims_costs)

        return correlation_analyzer.analyze(max_lag=6)

    def _forecast_linked(self, historical_data):
        """
        Связанный прогноз: рекламации → претензии.

        Алгоритм:
            1. Анализируем корреляцию и находим оптимальный лаг
            2. Прогнозируем рекламации сезонным методом
            3. На основе прогноза рекламаций прогнозируем претензии

        Args:
            historical_data: dict с историческими данными

        Returns:
            dict: прогнозы рекламаций, претензий и сумм
        """
        reclamations = historical_data["reclamations"]
        claims_count = historical_data["claims"]
        claims_costs = historical_data["claims_costs"]

        # ПРОВЕРКА МИНИМУМА ДАННЫХ
        # Для linked нужно минимум 6 месяцев данных.
        # При меньшем количестве — fallback на сезонный прогноз.
        min_data_points = 6
        if len(reclamations) < min_data_points or len(claims_costs) < min_data_points:
            # Fallback на сезонный прогноз
            seasonal_forecaster = SeasonalForecast(
                method="auto", seasonal_period=12, seasonal_type=self.seasonal_type
            )

            reclamations_forecast = seasonal_forecaster.forecast(
                reclamations, self.forecast_months, round_decimals=0
            )
            claims_count_forecast = seasonal_forecaster.forecast(
                claims_count, self.forecast_months, round_decimals=0
            )
            claims_costs_forecast = seasonal_forecaster.forecast(
                claims_costs, self.forecast_months, round_decimals=2
            )

            # Пустые CI — данных недостаточно. Сохраняем информацию об ошибке
            self._correlation_analysis = {
                "optimal_lag": 0,
                "correlation": 0.0,
                "is_significant": False,
                "error": f"Недостаточно данных (нужно минимум {min_data_points} месяцев)",
            }
            self._linked_model_info = None

            return {
                "reclamations": reclamations_forecast,
                "claims_count": claims_count_forecast,
                "claims_costs": claims_costs_forecast,
                "claims_costs_ci_lower": [],  # Пустой CI — данных недостаточно
                "claims_costs_ci_upper": [],
            }

        # ШАГ 1: АНАЛИЗ КОРРЕЛЯЦИИ
        self._correlation_analysis = self._analyze_correlation(
            reclamations, claims_costs
        )
        optimal_lag = self._correlation_analysis.get("optimal_lag", 3)

        # ШАГ 2: ПРОГНОЗ РЕКЛАМАЦИЙ (сезонный метод)
        # Прогнозируем на forecast_months + lag для расчёта претензий
        # Дополнительные месяцы нужны т.к. претензии "отстают" от рекламаций на lag месяцев
        extended_forecast_months = self.forecast_months + optimal_lag

        seasonal_forecaster = SeasonalForecast(
            method="auto", seasonal_period=12, seasonal_type=self.seasonal_type
        )

        reclamations_forecast_extended = seasonal_forecaster.forecast(
            reclamations, extended_forecast_months, round_decimals=0
        )

        # Основной прогноз рекламаций (без расширения)
        reclamations_forecast = reclamations_forecast_extended[: self.forecast_months]

        # ШАГ 3: ОБУЧЕНИЕ МОДЕЛИ СВЯЗАННОГО ПРОГНОЗА
        claims_predictor = ClaimsPredictor(
            reclamations_history=reclamations,
            claims_count_history=claims_count,
            claims_sum_history=claims_costs,
            lag_months=optimal_lag,
        )
        claims_predictor.fit()

        # Сохраняем информацию о модели для UI
        self._linked_model_info = claims_predictor.get_full_analysis()

        # ШАГ 4: ПРОГНОЗ ПРЕТЕНЗИЙ
        claims_predictions = claims_predictor.predict(reclamations_forecast)

        claims_count_forecast = [
            int(round(p.expected_claims_count)) for p in claims_predictions
        ]
        claims_costs_forecast = [p.predicted_sum for p in claims_predictions]

        # Доверительные интервалы для сумм
        claims_costs_ci_lower = [p.confidence_lower for p in claims_predictions]
        claims_costs_ci_upper = [p.confidence_upper for p in claims_predictions]

        return {
            "reclamations": reclamations_forecast,
            "claims_count": claims_count_forecast,
            "claims_costs": claims_costs_forecast,
            "claims_costs_ci_lower": claims_costs_ci_lower,
            "claims_costs_ci_upper": claims_costs_ci_upper,
        }

    # ========== ПАРАМЕТРЫ КОНВЕРСИИ (информационные карточки) ==========

    def _get_conversion_params(self):
        """
        Получение параметров конверсии через ReclamationToClaimProcessor
        (Только для отображения в карточках. Не используется для расчета прогноза.)

        Returns:
            dict: параметры конверсии (процент, среднее время эскалации)
        """
        from claims.modules.reclamation_to_claim_processor import (
            ReclamationToClaimProcessor,
        )

        conversion_processor = ReclamationToClaimProcessor(
            year=self.year,
            consumers=self.consumers,
            exchange_rate=self.exchange_rate,
        )

        summary = conversion_processor.get_group_a_summary()

        if summary["total_reclamations"] == 0:
            return {
                "conversion_rate": 0,
                "escalation_days": 120,  # Значение по умолчанию
                "total_reclamations": 0,
                "escalated_reclamations": 0,
            }

        return {
            "conversion_rate": summary["escalation_rate"],
            "escalation_days": summary["average_days"],
            "total_reclamations": summary["total_reclamations"],
            "escalated_reclamations": summary["escalated_reclamations"],
        }

    # ========== ГЕНЕРАЦИЯ МЕТОК ДЛЯ ОСИ X ==========

    def _generate_forecast_labels(self, start_year, start_month, months_count):
        """
        Генерация меток для прогнозных месяцев

        Когда прогноз выходит за пределы исторических данных,
        нужно создать новые метки для оси X.

        Args:
            start_year: стартовый год
            start_month: стартовый месяц (1-12)
            months_count: сколько месяцев генерировать

        Returns:
            tuple: (labels, labels_formatted)
        """
        labels = []
        labels_formatted = []

        current_date = date(start_year, start_month, 1)

        for _ in range(months_count):
            labels.append(current_date.strftime("%Y-%m"))

            month_name = self.MONTH_NAMES[current_date.month]
            labels_formatted.append(f"{month_name} {current_date.year}")

            current_date += relativedelta(months=1)

        return labels, labels_formatted

    # ========== # ОБЪЕДИНЕНИЕ ФАКТА И ПРОГНОЗА ==========

    def get_combined_data(self):
        """
        Объединение исторических и прогнозных данных

        ЛОГИКА:
        1. Определяем ТЕКУЩИЙ месяц через date.today().
        2. Рекламации: факт до ПРОШЛОГО месяца, прогноз с ТЕКУЩЕГО.
           Фактические данные по РЕКЛАМАЦИЯМ за текущий месяц ещё неполные, поэтому прогноз начинается с ТЕКУЩЕГО месяца.
        3. Претензии: факт до позапрошлого месяца, прогноз с ПРОШЛОГО.
           Претензии "отстают" от рекламаций примерно на месяц. Фактических данных по ПРЕТЕНЗИЯМ за прошлый месяц ещё нет,
           поэтому прогноз начинается с ПРОШЛОГО месяца.

        Returns:
            dict: объединенные данные для визуализации
        """
        # ШАГ 1: ПОЛУЧЕНИЕ ИСТОРИЧЕСКИХ ДАННЫХ
        historical = self._get_historical_data()

        if not historical["labels"]:
            return {
                "labels": [],
                "labels_formatted": [],
                "reclamations_fact": [],
                "reclamations_forecast": [],
                "claims_fact": [],
                "claims_forecast": [],
                "claims_costs_fact": [],
                "claims_costs_forecast": [],
                "claims_costs_ci_lower": [],
                "claims_costs_ci_upper": [],
                "table_data": [],
            }

        # ШАГ 2: ОПРЕДЕЛЕНИЕ ТЕКУЩЕГО МЕСЯЦА (динамически)
        today = date.today()
        current_month_label = today.strftime("%Y-%m")  # "2025-03"

        # Ищем индекс текущего месяца в истории
        try:
            current_index = historical["labels"].index(current_month_label)
        except ValueError:
            # Текущего месяца нет в истории — вся история в прошлом
            current_index = len(historical["labels"])

        # ШАГ 3: ОПРЕДЕЛЕНИЕ ГРАНИЦ ФАКТ/ПРОГНОЗ
        # Рекламации: факт до текущего месяца (не включая)
        recl_fact_end = current_index
        # Претензии: факт до прошлого месяца (не включая)
        claim_fact_end = max(0, current_index - 1)

        # ШАГ 4: ПРОГНОЗИРОВАНИЕ (различается по методу)
        if self.forecast_method == "linked":
            # СВЯЗАННЫЙ ПРОГНОЗ
            # Все три показателя рассчитываются взаимосвязано
            recl_historical = (
                historical["reclamations"][:recl_fact_end] if recl_fact_end > 0 else []
            )
            claim_historical = (
                historical["claims"][:claim_fact_end] if claim_fact_end > 0 else []
            )
            cost_historical = (
                historical["claims_costs"][:claim_fact_end]
                if claim_fact_end > 0
                else []
            )

            linked_forecast = self._forecast_linked(
                {
                    "reclamations": recl_historical,
                    "claims": claim_historical,
                    "claims_costs": cost_historical,
                }
            )

            reclamations_forecast = linked_forecast["reclamations"]
            claims_count_forecast = linked_forecast["claims_count"]
            claims_costs_forecast = linked_forecast["claims_costs"]
            claims_costs_ci_lower = linked_forecast.get("claims_costs_ci_lower", [])
            claims_costs_ci_upper = linked_forecast.get("claims_costs_ci_upper", [])

        else:
            # СТАНДАРТНЫЙ ПРОГНОЗ (statistical, ml, seasonal)
            # Каждый показатель прогнозируется независимо
            recl_historical = (
                historical["reclamations"][:recl_fact_end] if recl_fact_end > 0 else []
            )
            reclamations_forecast = self._forecast_reclamations(recl_historical)

            claim_historical = (
                historical["claims"][:claim_fact_end] if claim_fact_end > 0 else []
            )
            claims_count_forecast = self._forecast_claims_count(claim_historical)

            cost_historical = (
                historical["claims_costs"][:claim_fact_end]
                if claim_fact_end > 0
                else []
            )
            claims_costs_forecast = self._forecast_claim_costs(cost_historical)

            # Для не-linked методов нет доверительного интервала
            claims_costs_ci_lower = []
            claims_costs_ci_upper = []

        # ШАГ 5: ГЕНЕРАЦИЯ МЕТОК ДЛЯ НОВЫХ МЕСЯЦЕВ
        # Если прогноз выходит за пределы исторических данных, то создаем новые метки
        last_label = historical["labels"][-1]
        last_year, last_month = map(int, last_label.split("-"))
        next_month_date = date(last_year, last_month, 1) + relativedelta(months=1)

        # Определяем сколько прогнозных месяцев уже есть в истории
        months_in_history = len(historical["labels"]) - current_index
        # Определяем сколько новых меток нужно создать
        new_months_needed = max(0, self.forecast_months - months_in_history)

        if new_months_needed > 0:
            new_labels, new_labels_formatted = self._generate_forecast_labels(
                next_month_date.year,
                next_month_date.month,
                new_months_needed,
            )
        else:
            new_labels = []
            new_labels_formatted = []

        # ШАГ 6: ОБЪЕДИНЕНИЕ МЕТОК
        all_labels = historical["labels"] + new_labels
        all_labels_formatted = historical["labels_formatted"] + new_labels_formatted
        total_length = len(all_labels)

        # ШАГ 7: ФОРМИРОВАНИЕ МАССИВОВ ДЛЯ ГРАФИКА
        # ────────────────────────────────────────────────────
        # Для каждого месяца определяем:
        # - Это факт или прогноз?
        # - Какое значение показать?
        #
        # Массивы формата: [value, 0, 0, value, value, ...]
        # где 0 означает "не показывать" (для графика Chart.js)
        # ────────────────────────────────────────────────────
        # РЕКЛАМАЦИИ
        reclamations_fact = []
        reclamations_forecast_padded = []

        for i in range(total_length):
            if i < recl_fact_end:
                # Факт — берём из истории
                reclamations_fact.append(
                    historical["reclamations"][i]
                    if i < len(historical["reclamations"])
                    else 0
                )
                reclamations_forecast_padded.append(0)
            else:
                # Прогноз — берём из forecast
                reclamations_fact.append(0)
                forecast_index = i - recl_fact_end
                reclamations_forecast_padded.append(
                    reclamations_forecast[forecast_index]
                    if forecast_index < len(reclamations_forecast)
                    else 0
                )

        # ПРЕТЕНЗИИ (количество)
        claims_fact = []
        claims_forecast_padded = []

        for i in range(total_length):
            if i < claim_fact_end:
                claims_fact.append(
                    historical["claims"][i] if i < len(historical["claims"]) else 0
                )
                claims_forecast_padded.append(0)
            else:
                claims_fact.append(0)
                forecast_index = i - claim_fact_end
                claims_forecast_padded.append(
                    claims_count_forecast[forecast_index]
                    if forecast_index < len(claims_count_forecast)
                    else 0
                )

        # ПРЕТЕНЗИИ (суммы) + доверительные интервалы
        claims_costs_fact = []
        claims_costs_forecast_padded = []
        ci_lower_padded = []
        ci_upper_padded = []

        for i in range(total_length):
            if i < claim_fact_end:
                claims_costs_fact.append(
                    historical["claims_costs"][i]
                    if i < len(historical["claims_costs"])
                    else 0.0
                )
                claims_costs_forecast_padded.append(0.0)
                ci_lower_padded.append(0.0)
                ci_upper_padded.append(0.0)
            else:
                claims_costs_fact.append(0.0)
                forecast_index = i - claim_fact_end
                claims_costs_forecast_padded.append(
                    claims_costs_forecast[forecast_index]
                    if forecast_index < len(claims_costs_forecast)
                    else 0.0
                )
                ci_lower_padded.append(
                    claims_costs_ci_lower[forecast_index]
                    if forecast_index < len(claims_costs_ci_lower)
                    else 0.0
                )
                ci_upper_padded.append(
                    claims_costs_ci_upper[forecast_index]
                    if forecast_index < len(claims_costs_ci_upper)
                    else 0.0
                )

        # ШАГ 8: ФОРМИРОВАНИЕ ДАННЫХ ДЛЯ ТАБЛИЦЫ
        table_data = []
        for i in range(total_length):
            row = {
                "label": all_labels[i],
                "label_formatted": all_labels_formatted[i],
                "reclamation_fact": reclamations_fact[i],
                "reclamation_forecast": reclamations_forecast_padded[i],
                "claim_fact": claims_fact[i],
                "claim_forecast": claims_forecast_padded[i],
                "claim_cost_fact": claims_costs_fact[i],
                "claim_cost_forecast": claims_costs_forecast_padded[i],
            }
            # Добавляем CI для linked метода
            if self.forecast_method == "linked" and ci_lower_padded[i] > 0:
                row["claim_cost_ci_lower"] = ci_lower_padded[i]
                row["claim_cost_ci_upper"] = ci_upper_padded[i]
            table_data.append(row)

        return {
            "labels": all_labels,
            "labels_formatted": all_labels_formatted,
            "reclamations_fact": reclamations_fact,
            "reclamations_forecast": reclamations_forecast_padded,
            "claims_fact": claims_fact,
            "claims_forecast": claims_forecast_padded,
            "claims_costs_fact": claims_costs_fact,
            "claims_costs_forecast": claims_costs_forecast_padded,
            "claims_costs_ci_lower": ci_lower_padded,
            "claims_costs_ci_upper": ci_upper_padded,
            "table_data": table_data,
        }

    # ========== ГЛАВНЫЙ МЕТОД ==========

    def generate_analysis(self):
        """
        Главный метод прогноза: собирает всё и возвращает готовый результат.

        Это точка входа для представления (view).
        Вызывает все остальные методы в правильном порядке.

        Порядок действий:
        1. Получить исторические данные
        2. Получить параметры конверсии (для карточек)
        3. Сформировать объединённые данные (факт + прогноз)
        4. Добавить метаданные (информация о модели, сезонность)
        5. Вернуть готовый результат

        Returns:
            dict с ключами:
            - success: True/False — успешно ли выполнен анализ
            - error: текст ошибки (если success=False)
            - year, consumers, forecast_months, ... — параметры
            - historical: исторические данные
            - conversion_params: параметры конверсии
            - combined_data: объединённые данные для графика
            - correlation_analysis: результат корреляции (для linked)
            - linked_model: информация о модели (для linked)
            - seasonality_pattern: сезонные индексы (для seasonal/linked)
        """
        try:
            # Получаем все данные
            historical = self._get_historical_data()
            conversion_params = self._get_conversion_params()
            combined_data = self.get_combined_data()

            # Проверяем наличие исторических данных
            if not historical["labels"]:
                # Формируем понятное сообщение об ошибке
                consumer_text = (
                    "всех потребителей"
                    if self.all_consumers_mode
                    else (
                        self.consumers[0]
                        if len(self.consumers) == 1
                        else f"{len(self.consumers)} потребителей"
                    )
                )
                return {
                    "success": False,
                    "error": f"Нет данных для {consumer_text} за {self.year} год",
                }

            # Формируем текст для отображения
            if self.all_consumers_mode:
                consumer_display = "всех потребителей"
            elif len(self.consumers) == 1:
                consumer_display = self.consumers[0]
            else:
                consumer_display = f"{len(self.consumers)} потребителей"

            # БАЗОВЫЙ РЕЗУЛЬТАТ
            result = {
                "success": True,
                "year": self.year,
                "consumers": self.consumers,
                "consumer_display": consumer_display,
                "all_consumers_mode": self.all_consumers_mode,
                "forecast_months": self.forecast_months,
                "exchange_rate": str(self.exchange_rate),
                # Информация о методе
                "forecast_method": self.forecast_method,
                "forecast_method_display": self.METHOD_DESCRIPTIONS.get(
                    self.forecast_method, self.forecast_method
                ),
                "statistical_mode": (
                    self.statistical_mode
                    if self.forecast_method == "statistical"
                    else None
                ),
                "ml_model": self.ml_model if self.forecast_method == "ml" else None,
                # Данные
                "historical": historical,
                "conversion_params": conversion_params,
                "combined_data": combined_data,
            }

            # Дополнительные данные для linked метода
            if self.forecast_method == "linked":
                result["correlation_analysis"] = self._correlation_analysis
                result["linked_model"] = self._linked_model_info

            # Сезонные индексы для seasonal и linked методов
            if self.forecast_method in ("seasonal", "linked"):
                seasonal = SeasonalForecast(method="auto", seasonal_period=12)
                result["seasonality_pattern"] = seasonal.get_seasonality_pattern(
                    historical["reclamations"]
                )

            return result

        except Exception as e:
            import traceback

            return {
                "success": False,
                "error": f"Ошибка при генерации прогноза: {str(e)}",
                "traceback": traceback.format_exc(),  # Для отладки
            }

    # ========== ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ==========

    def get_available_methods(self):
        """
        Возвращает доступные методы прогнозирования для UI.

        Используется в представлении для динамического построения формы.

        Returns:
            list[dict]: список методов с описаниями
        """
        return [
            {
                "value": "statistical",
                "label": "Статистический",
                "description": "Скользящее среднее + линейный тренд",
                "submethods": [
                    {"value": "conservative", "label": "Консервативный"},
                    {"value": "balanced", "label": "Сбалансированный"},
                    {"value": "aggressive", "label": "Агрессивный"},
                ],
            },
            {
                "value": "ml",
                "label": "Машинное обучение",
                "description": "Регрессионные модели",
                "submethods": [
                    {"value": "linear", "label": "Линейная регрессия"},
                    {"value": "ridge", "label": "Ridge регрессия"},
                    {"value": "polynomial", "label": "Полиномиальная"},
                ],
            },
            {
                "value": "seasonal",
                "label": "Сезонный",
                "description": "Holt-Winters с учётом сезонности",
                "submethods": [
                    {"value": "mul", "label": "Мультипликативный"},
                    {"value": "add", "label": "Аддитивный"},
                ],
            },
            {
                "value": "linked",
                "label": "Связанный",
                "description": "Прогноз претензий на основе рекламаций",
                "submethods": [],
                "features": [
                    "Автоопределение временного лага",
                    "Корреляционный анализ",
                    "Доверительные интервалы",
                ],
            },
        ]

    # ========== СОХРАНЕНИЕ ==========

    def save_to_files(self):
        """Сохранение графика в PNG"""
        try:
            analysis_data = self.generate_analysis()

            if not analysis_data["success"]:
                return {"success": False, "error": analysis_data.get("error")}

            combined_data = analysis_data["combined_data"]

            if not combined_data["labels"]:
                return {"success": False, "error": "Нет данных для сохранения"}

            # Определяем суффикс для файла
            if self.all_consumers_mode:
                file_suffix = "все_потребители"
            elif len(self.consumers) == 1:
                file_suffix = self.consumers[0].replace(" ", "_").replace("-", "_")
            else:
                file_suffix = f"{len(self.consumers)}_потребителей"

            chart_path = get_claim_prognosis_chart_path(self.year, file_suffix)

            # ----------------- СОЗДАНИЕ ГРАФИКА ------------------
            fig, ax = plt.subplots(figsize=(16, 8))

            x = np.arange(len(combined_data["labels"]))
            width = 0.2  # ширина столбца

            # 4 серии столбцов
            bars1 = ax.bar(
                x - 1.5 * width,
                combined_data["reclamations_fact"],
                width,
                label="Рекламации (факт)",
                color="#FF9800",
                alpha=0.9,
            )

            bars2 = ax.bar(
                x - 0.5 * width,
                combined_data["reclamations_forecast"],
                width,
                label="Рекламации (прогноз)",
                color="#FFE0B2",
                alpha=0.8,
                hatch="//",
            )

            bars3 = ax.bar(
                x + 0.5 * width,
                combined_data["claims_fact"],
                width,
                label="Претензии (факт)",
                color="#F44336",
                alpha=0.9,
            )

            bars4 = ax.bar(
                x + 1.5 * width,
                combined_data["claims_forecast"],
                width,
                label="Претензии (прогноз)",
                color="#FFCDD2",
                alpha=0.8,
                hatch="\\\\",
            )

            # Подписи данных
            def add_bar_labels(bars, data):
                """Добавление подписей значений на столбцы"""
                for i, (bar, value) in enumerate(zip(bars, data)):
                    if value > 0:
                        height = bar.get_height()
                        ax.text(
                            bar.get_x() + bar.get_width() / 2.0,
                            height,
                            f"{int(value)}",
                            ha="center",
                            va="bottom",
                            fontsize=7,
                            fontweight="bold",
                        )

            add_bar_labels(bars1, combined_data["reclamations_fact"])
            add_bar_labels(bars2, combined_data["reclamations_forecast"])
            add_bar_labels(bars3, combined_data["claims_fact"])
            add_bar_labels(bars4, combined_data["claims_forecast"])

            # Оформление
            ax.set_xlabel("Период", fontsize=12, fontweight="bold")
            ax.set_ylabel("Количество (шт.)", fontsize=12, fontweight="bold")
            ax.set_title(
                f'Прогноз претензий: {analysis_data["consumer_display"]} '
                f"({self.year} год + {self.forecast_months} мес.)",
                fontsize=14,
                fontweight="bold",
                pad=20,
                loc="left",
            )

            # Подписи оси X
            ax.set_xticks(x)
            ax.set_xticklabels(
                combined_data["labels"], rotation=45, ha="right", fontsize=9
            )

            # Легенда
            ax.legend(loc="upper left", fontsize=10, framealpha=0.9)

            # Сетка
            ax.grid(True, alpha=0.3, axis="y", linestyle="--")

            plt.tight_layout()
            plt.savefig(chart_path, dpi=300, bbox_inches="tight")
            plt.close()

            return {
                "success": True,
                "base_dir": BASE_REPORTS_DIR,
                "chart_path": chart_path,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}
