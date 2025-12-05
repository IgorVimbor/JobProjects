# claims\modules\claim_prognosis_processor.py
"""Процессор для прогнозирования претензий на основе анализа рекламаций"""

from datetime import date
from decimal import Decimal
from dateutil.relativedelta import relativedelta

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from reports.config.paths import (
    get_claim_prognosis_chart_path,
    BASE_REPORTS_DIR,
)


class ClaimPrognosisProcessor:
    """Прогнозирование претензий на основе конверсии рекламаций"""

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

    def __init__(
        self, year=None, consumers=None, forecast_months=6, exchange_rate=None
    ):
        """
        Инициализация процессора прогнозирования

        Args:
            year: год анализа исторических данных
            consumers: список потребителей (пустой = все)
            forecast_months: количество месяцев прогноза (3, 6, 12)
            exchange_rate: курс конвертации валюты
        """
        self.today = date.today()
        self.year = year or self.today.year
        self.consumers = consumers or []
        self.all_consumers_mode = len(self.consumers) == 0
        self.forecast_months = forecast_months or 6
        self.exchange_rate = exchange_rate or Decimal("0.03")

    # ========== ИСТОРИЧЕСКИЕ ДАННЫЕ ==========

    def _get_historical_data(self):
        """
        Получение исторических данных через TimeAnalysisProcessor

        Returns:
            dict: данные по месяцам (рекламации, претензии)
        """
        from claims.modules.time_analysis_processor import TimeAnalysisProcessor

        time_processor = TimeAnalysisProcessor(
            year=self.year,
            consumers=self.consumers,
            exchange_rate=self.exchange_rate,
        )

        monthly_data = time_processor.get_monthly_distribution()

        return {
            "labels": monthly_data["labels"],
            "labels_formatted": monthly_data["labels_formatted"],
            "reclamations": monthly_data["reclamations"],
            "claims": monthly_data["claims_counts"],
            "claims_costs": monthly_data["claims_costs"],
        }

    # ========== ПРОГНОЗ РЕКЛАМАЦИЙ ==========

    def _calculate_moving_average(self, data, window=3):
        """
        Расчет скользящего среднего

        Args:
            data: список значений
            window: окно усреднения (количество последних периодов)

        Returns:
            float: среднее значение
        """
        if not data:
            return 0

        if len(data) < window:
            return sum(data) / len(data)

        return sum(data[-window:]) / window

    def _calculate_trend(self, data):
        """
        Расчет линейного тренда (наклона)

        Args:
            data: список значений

        Returns:
            float: коэффициент тренда (наклон линейной регрессии)
        """
        if len(data) < 2:
            return 0

        x = np.arange(len(data))
        y = np.array(data)

        # Линейная регрессия: y = ax + b
        coefficients = np.polyfit(x, y, 1)
        slope = coefficients[0]  # тренд (наклон)

        return slope

    def _forecast_reclamations(self, historical_reclamations):
        """
        Прогноз рекламаций на N месяцев вперед

        Метод: скользящее среднее + линейный тренд

        Args:
            historical_reclamations: список исторических значений

        Returns:
            list: прогнозные значения по месяцам
        """
        if not historical_reclamations:
            return [0] * self.forecast_months

        # Скользящее среднее (базовое значение)
        base_value = self._calculate_moving_average(historical_reclamations, window=3)

        # Тренд (направление изменения)
        trend = self._calculate_trend(historical_reclamations)

        # Генерация прогноза
        forecast = []
        for i in range(self.forecast_months):
            # Базовое значение + тренд * шаг вперед
            predicted_value = base_value + trend * (i + 1)

            # Не даем уйти в отрицательные значения
            predicted_value = max(0, predicted_value)

            forecast.append(round(predicted_value))

        return forecast

    # ========== ПАРАМЕТРЫ КОНВЕРСИИ ==========

    def _get_conversion_params(self):
        """
        Получение параметров конверсии через ReclamationToClaimProcessor

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

        # Если нет данных, возвращаем дефолтные значения
        if summary["total_reclamations"] == 0:
            return {
                "conversion_rate": 0,
                "escalation_days": 120,  # среднее значение по умолчанию
                "total_reclamations": 0,
                "escalated_reclamations": 0,
            }

        return {
            "conversion_rate": summary["escalation_rate"],  # в процентах
            "escalation_days": summary["average_days"],
            "total_reclamations": summary["total_reclamations"],
            "escalated_reclamations": summary["escalated_reclamations"],
        }

    # ========== ПРОГНОЗ ПРЕТЕНЗИЙ ==========

    def _forecast_claims(self, reclamations_forecast, conversion_params):
        """
        Прогноз претензий на основе модели конверсии

        МОДЕЛЬ ПОЛЬЗОВАТЕЛЯ:
        претензии[месяц + лаг] = рекламации[месяц] * конверсия

        Args:
            reclamations_forecast: список прогнозных рекламаций по месяцам
            conversion_params: параметры конверсии (% и время эскалации)

        Returns:
            list: прогнозные претензии со сдвигом на время эскалации
        """
        conversion_rate = conversion_params["conversion_rate"] / 100  # % → 0.XX
        escalation_days = conversion_params["escalation_days"]

        # Переводим дни в месяцы (примерно)
        lag_months = round(escalation_days / 30)

        # Прогноз претензий со сдвигом
        forecast_length = len(reclamations_forecast) + lag_months
        claims_forecast = [0] * forecast_length

        for i, recl_count in enumerate(reclamations_forecast):
            # Индекс с учетом лага
            target_index = i + lag_months

            if target_index < forecast_length:
                claims_count = recl_count * conversion_rate
                claims_forecast[target_index] = round(claims_count)

        return claims_forecast

    # ========== ОБЪЕДИНЕНИЕ ДАННЫХ ==========

    def _generate_forecast_labels(self, start_year, start_month, months_count):
        """
        Генерация меток для прогнозных месяцев

        Args:
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

    def get_combined_data(self):
        """
        Объединение исторических и прогнозных данных

        Возвращает данные для графика с 4 сериями и таблицы:
        - reclamations_fact (столбцы)
        - reclamations_forecast (столбцы)
        - claims_fact (столбцы)
        - claims_forecast (столбцы со сдвигом на время эскалации)

        Returns:
            dict: объединенные данные для визуализации
        """
        # 1. Получаем исторические данные
        historical = self._get_historical_data()

        # 2. Прогнозируем рекламации
        reclamations_forecast = self._forecast_reclamations(historical["reclamations"])

        # 3. Получаем параметры конверсии
        conversion_params = self._get_conversion_params()

        # 4. Прогнозируем претензии
        claims_forecast = self._forecast_claims(
            reclamations_forecast, conversion_params
        )

        # 5. Генерируем метки для прогнозных месяцев
        if historical["labels"]:
            last_label = historical["labels"][-1]
            last_year, last_month = map(int, last_label.split("-"))

            # Начинаем со следующего месяца
            next_month_date = date(last_year, last_month, 1) + relativedelta(months=1)

            forecast_labels, forecast_labels_formatted = self._generate_forecast_labels(
                next_month_date.year,
                next_month_date.month,
                len(claims_forecast),  # используем длину прогноза претензий (с лагом)
            )
        else:
            forecast_labels = []
            forecast_labels_formatted = []

        # 6. Объединяем метки
        all_labels = historical["labels"] + forecast_labels
        all_labels_formatted = (
            historical["labels_formatted"] + forecast_labels_formatted
        )

        # 7. Объединяем данные (заполняем нулями для выравнивания)
        total_length = len(all_labels)
        historical_length = len(historical["labels"])

        # Рекламации
        reclamations_fact = historical["reclamations"] + [0] * (
            total_length - historical_length
        )
        reclamations_forecast_padded = (
            [0] * historical_length
            + reclamations_forecast
            + [0] * (total_length - historical_length - len(reclamations_forecast))
        )

        # Претензии
        claims_fact = historical["claims"] + [0] * (total_length - historical_length)
        claims_forecast_padded = (
            [0] * historical_length
            + claims_forecast
            + [0] * (total_length - historical_length - len(claims_forecast))
        )

        # Обрезаем до нужной длины
        reclamations_forecast_padded = reclamations_forecast_padded[:total_length]
        claims_forecast_padded = claims_forecast_padded[:total_length]

        # Формируем данные для ТАБЛИЦЫ (список словарей)
        table_data = []
        for i in range(len(all_labels)):
            table_data.append(
                {
                    "label": all_labels[i],
                    "label_formatted": all_labels_formatted[i],
                    "reclamation_fact": reclamations_fact[i],
                    "reclamation_forecast": reclamations_forecast_padded[i],
                    "claim_fact": claims_fact[i],
                    "claim_forecast": claims_forecast_padded[i],
                }
            )

        return {
            "labels": all_labels,
            "labels_formatted": all_labels_formatted,
            "reclamations_fact": reclamations_fact,
            "reclamations_forecast": reclamations_forecast_padded,
            "claims_fact": claims_fact,
            "claims_forecast": claims_forecast_padded,
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
