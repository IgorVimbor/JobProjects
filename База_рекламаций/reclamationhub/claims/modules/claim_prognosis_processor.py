# claims/modules/claim_prognosis_processor.py

"""Процессор для прогнозирования претензий с разными методами"""

from datetime import date
from dateutil.relativedelta import relativedelta
import numpy as np

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from claims.modules.forecast import StatisticalForecast, MachineLearningForecast
from reports.config.paths import (
    get_claim_prognosis_chart_path,
    BASE_REPORTS_DIR,
)


class ClaimPrognosisProcessor:
    """
    Процессор прогнозирования претензий (оркестратор)

    Поддерживает 6 методов:
    1-3. Статистические (консервативный, сбалансированный, агрессивный)
    4-6. Машинное обучение (linear, ridge, polynomial)
    """

    # ========== КОНСТАНТЫ ==========

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
    ):
        """
        Args:
            year: год анализа исторических данных
            consumers: список потребителей (пустой = все)
            forecast_months: период прогноза (3, 6 или 12 месяцев)
            exchange_rate: курс конвертации валюты
            forecast_method: 'statistical' или 'ml'
            statistical_mode: 'conservative', 'balanced', 'aggressive'
            ml_model: 'linear', 'ridge', 'polynomial'
        """
        self.today = date.today()
        self.year = year or self.today.year
        self.consumers = consumers or []
        self.all_consumers_mode = len(self.consumers) == 0
        self.forecast_months = forecast_months or 6
        self.exchange_rate = exchange_rate or 0.03

        # Параметры методов
        self.forecast_method = forecast_method
        self.statistical_mode = statistical_mode
        self.ml_model = ml_model

        # Создаем экземпляр forecaster'а
        if forecast_method == "statistical":
            self.forecaster = StatisticalForecast(mode=statistical_mode)
        else:  # ml
            self.forecaster = MachineLearningForecast(model=ml_model)

    # ========== ИСТОРИЧЕСКИЕ ДАННЫЕ ==========

    def _get_historical_data(self):
        """
        Получение исторических данных через TimeAnalysisProcessor

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

    # ========== ПРОГНОЗЫ ПОКАЗАТЕЛЕЙ ==========

    def _forecast_reclamations(self, historical_reclamations):
        """
        Прогноз количества рекламаций

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

        historical_costs: список исторических сумм

        Returns:
            list: прогноз на forecast_months периодов
        """
        return self.forecaster.forecast(
            historical_costs, self.forecast_months, round_decimals=2
        )

    # ========== ПАРАМЕТРЫ КОНВЕРСИИ (ИНФОРМАЦИОННЫЕ) ==========

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
                "escalation_days": 120,
                "total_reclamations": 0,
                "escalated_reclamations": 0,
            }

        return {
            "conversion_rate": summary["escalation_rate"],
            "escalation_days": summary["average_days"],
            "total_reclamations": summary["total_reclamations"],
            "escalated_reclamations": summary["escalated_reclamations"],
        }

    # ========== ГЕНЕРАЦИЯ МЕТОК ==========

    def _generate_forecast_labels(self, start_year, start_month, months_count):
        """
        Генерация меток для прогнозных месяцев

        start_year: стартовый год
        start_month: стартовый месяц
        months_count: количество месяцев

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

    # ========== ОБЪЕДИНЕНИЕ ДАННЫХ ==========

    def get_combined_data(self):
        """
        Объединение исторических и прогнозных данных

        ЛОГИКА:
        1. Определяем ТЕКУЩИЙ месяц через date.today()
        2. Рекламации: факт до ПРОШЛОГО месяца, прогноз с ТЕКУЩЕГО
        3. Претензии: факт до позапрошлого месяца, прогноз с ПРОШЛОГО

        Returns:
            dict: объединенные данные для визуализации
        """
        # 1. Получаем исторические данные
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
                "table_data": [],
            }

        # 2. Определяем ТЕКУЩИЙ месяц динамически
        today = date.today()
        current_month_label = today.strftime("%Y-%m")

        # Ищем индекс текущего месяца в истории
        try:
            current_index = historical["labels"].index(current_month_label)
        except ValueError:
            # Если текущего месяца нет в истории, считаем что история до конца
            current_index = len(historical["labels"])

        # 3. Определяем границы факт/прогноз
        # Рекламации: факт до текущего месяца (не включая)
        recl_fact_end = current_index

        # Претензии: факт до прошлого месяца (не включая)
        claim_fact_end = max(0, current_index - 1)

        # 4. Прогнозируем на основе ФАКТИЧЕСКИХ данных (до границы)
        recl_historical = (
            historical["reclamations"][:recl_fact_end] if recl_fact_end > 0 else []
        )
        reclamations_forecast = self._forecast_reclamations(recl_historical)

        claim_historical = (
            historical["claims"][:claim_fact_end] if claim_fact_end > 0 else []
        )
        claims_count_forecast = self._forecast_claims_count(claim_historical)

        cost_historical = (
            historical["claims_costs"][:claim_fact_end] if claim_fact_end > 0 else []
        )
        claims_costs_forecast = self._forecast_claim_costs(cost_historical)

        # 5. Генерируем метки для НОВЫХ месяцев (после последнего исторического)
        last_label = historical["labels"][-1]
        last_year, last_month = map(int, last_label.split("-"))
        next_month_date = date(last_year, last_month, 1) + relativedelta(months=1)

        # Сколько прогнозных месяцев уже "влезает" в историю?
        months_in_history = len(historical["labels"]) - current_index
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

        # 6. Объединяем метки
        all_labels = historical["labels"] + new_labels
        all_labels_formatted = historical["labels_formatted"] + new_labels_formatted
        total_length = len(all_labels)

        # 7. Формируем массивы БЕЗОПАСНО с правильными границами
        # РЕКЛАМАЦИИ
        reclamations_fact = []
        reclamations_forecast_padded = []

        for i in range(total_length):
            if i < recl_fact_end:
                # Факт
                reclamations_fact.append(
                    historical["reclamations"][i]
                    if i < len(historical["reclamations"])
                    else 0
                )
                reclamations_forecast_padded.append(0)
            else:
                # Прогноз
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
                # Факт
                claims_fact.append(
                    historical["claims"][i] if i < len(historical["claims"]) else 0
                )
                claims_forecast_padded.append(0)
            else:
                # Прогноз
                claims_fact.append(0)
                forecast_index = i - claim_fact_end
                claims_forecast_padded.append(
                    claims_count_forecast[forecast_index]
                    if forecast_index < len(claims_count_forecast)
                    else 0
                )

        # ПРЕТЕНЗИИ (суммы)
        claims_costs_fact = []
        claims_costs_forecast_padded = []

        for i in range(total_length):
            if i < claim_fact_end:
                # Факт
                claims_costs_fact.append(
                    historical["claims_costs"][i]
                    if i < len(historical["claims_costs"])
                    else 0.0
                )
                claims_costs_forecast_padded.append(0.0)
            else:
                # Прогноз
                claims_costs_fact.append(0.0)
                forecast_index = i - claim_fact_end
                claims_costs_forecast_padded.append(
                    claims_costs_forecast[forecast_index]
                    if forecast_index < len(claims_costs_forecast)
                    else 0.0
                )

        # 8. Формируем данные для ТАБЛИЦЫ
        table_data = []
        for i in range(total_length):
            table_data.append(
                {
                    "label": all_labels[i],
                    "label_formatted": all_labels_formatted[i],
                    "reclamation_fact": reclamations_fact[i],
                    "reclamation_forecast": reclamations_forecast_padded[i],
                    "claim_fact": claims_fact[i],
                    "claim_forecast": claims_forecast_padded[i],
                    "claim_cost_fact": claims_costs_fact[i],
                    "claim_cost_forecast": claims_costs_forecast_padded[i],
                }
            )

        return {
            "labels": all_labels,
            "labels_formatted": all_labels_formatted,
            "reclamations_fact": reclamations_fact,
            "reclamations_forecast": reclamations_forecast_padded,
            "claims_fact": claims_fact,
            "claims_forecast": claims_forecast_padded,
            "claims_costs_fact": claims_costs_fact,
            "claims_costs_forecast": claims_costs_forecast_padded,
            "table_data": table_data,
        }

    # ========== ГЛАВНЫЙ МЕТОД ==========

    def generate_analysis(self):
        """Главный метод генерации прогноза"""
        try:
            # Получаем все данные
            historical = self._get_historical_data()
            conversion_params = self._get_conversion_params()
            combined_data = self.get_combined_data()

            # Проверяем наличие исторических данных
            if not historical["labels"]:
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

            # Определяем текст для отображения
            if self.all_consumers_mode:
                consumer_display = "всех потребителей"
            elif len(self.consumers) == 1:
                consumer_display = self.consumers[0]
            else:
                consumer_display = f"{len(self.consumers)} потребителей"

            return {
                "success": True,
                "year": self.year,
                "consumers": self.consumers,
                "consumer_display": consumer_display,
                "all_consumers_mode": self.all_consumers_mode,
                "forecast_months": self.forecast_months,
                "exchange_rate": str(self.exchange_rate),
                "forecast_method": self.forecast_method,
                "statistical_mode": (
                    self.statistical_mode
                    if self.forecast_method == "statistical"
                    else None
                ),
                "ml_model": self.ml_model if self.forecast_method == "ml" else None,
                "historical": historical,
                "conversion_params": conversion_params,
                "combined_data": combined_data,
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Ошибка при генерации прогноза: {str(e)}",
            }

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
