# claims/modules/time_analysis_processor.py
"""Процессор для временного анализа: изготовление → рекламация → претензия"""

import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from datetime import date
from django.db.models import Q, Prefetch

from claims.models import Claim
from reclamations.models import Reclamation
from reports.config.paths import (
    get_time_analysis_chart_path,
    BASE_REPORTS_DIR,
)


class TimeAnalysisProcessor:
    """Временной анализ дат: изготовление → рекламация → претензия"""

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

    def __init__(self, year=None, consumers=None):
        """
        year: год анализа
        consumers: список потребителей (пустой = все)
        """
        self.today = date.today()
        self.year = year or self.today.year
        self.consumers = consumers or []
        self.all_consumers_mode = len(self.consumers) == 0

    def _parse_manufacture_date(self, date_str):
        """
        Преобразование "07.24" → "2024-07"
        Возвращает None если формат неверный или NULL
        """
        if pd.isna(date_str) or not date_str:
            return None

        try:
            parts = str(date_str).strip().split(".")
            if len(parts) != 2:
                return None

            month, year_short = parts

            month_int = int(month)
            if month_int < 1 or month_int > 12:
                return None

            year_full = f"20{year_short}"
            return f"{year_full}-{month.zfill(2)}"

        except (ValueError, AttributeError):
            return None

    def _format_date_to_month(self, date_obj):
        """Преобразование DateField → "2024-03" """
        if pd.isna(date_obj) or not date_obj:
            return None

        try:
            if isinstance(date_obj, str):
                date_obj = pd.to_datetime(date_obj)
            return date_obj.strftime("%Y-%m")
        except (ValueError, AttributeError):
            return None

    def _extract_consumer_prefix(self, consumer_name):
        """Извлекает префикс потребителя (как в reclamation_to_claim)"""
        return Claim.extract_consumer_prefix(consumer_name)

    def _get_data_from_db(self):
        """
        Получение данных из БД:
        - Рекламации с фильтром по потребителям и году
        - Признанные претензии с фильтром по потребителям

        Возвращает DataFrame с колонками:
        - reclamation_id
        - manufacture_date_formatted (может быть None)
        - message_date_formatted
        - claim_date_formatted (может быть None если нет претензий)
        """
        # ✅ Фильтруем рекламации на уровне БД
        q_filters = Q(year=self.year)

        if not self.all_consumers_mode:
            consumer_q = Q()
            for consumer in self.consumers:
                consumer_prefix = self._extract_consumer_prefix(consumer)
                consumer_q |= Q(defect_period__name__exact=consumer_prefix)
                consumer_q |= Q(defect_period__name__istartswith=f"{consumer_prefix} -")
            q_filters &= consumer_q

        # Queryset для признанных претензий
        recognized_claims = Claim.objects.filter(
            result_claim="ACCEPTED",
            response_number__isnull=False,
            response_date__isnull=False,
            claim_date__year=self.year,  # Только претензии текущего года
        )

        # Предзагружаем претензии
        reclamations = (
            Reclamation.objects.filter(q_filters)
            .select_related("defect_period")
            .prefetch_related(
                Prefetch(
                    "claims",
                    queryset=recognized_claims,
                    to_attr="recognized_claims_cache",
                )
            )
        )

        if not reclamations.exists():
            return None

        # Формируем данные
        data = []

        for reclamation in reclamations:
            # Дата изготовления
            manufacture_date_formatted = self._parse_manufacture_date(
                reclamation.manufacture_date
            )

            # Дата получения сообщения
            message_date_formatted = self._format_date_to_month(
                reclamation.message_received_date
            )

            # Проверяем наличие признанных претензий
            for claim in reclamation.recognized_claims_cache:
                # Фильтр по потребителям в претензиях
                if not self.all_consumers_mode:
                    claim_prefix = self._extract_consumer_prefix(claim.consumer_name)
                    consumer_prefixes = [
                        self._extract_consumer_prefix(c) for c in self.consumers
                    ]
                    if claim_prefix not in consumer_prefixes:
                        continue

                claim_date_formatted = self._format_date_to_month(claim.claim_date)

                data.append(
                    {
                        "reclamation_id": reclamation.id,
                        "manufacture_date": manufacture_date_formatted,
                        "message_date": message_date_formatted,
                        "claim_date": claim_date_formatted,
                    }
                )

            # ✅ Добавляем рекламацию БЕЗ претензий (для группировки изготовления и сообщения)
            if not reclamation.recognized_claims_cache:
                data.append(
                    {
                        "reclamation_id": reclamation.id,
                        "manufacture_date": manufacture_date_formatted,
                        "message_date": message_date_formatted,
                        "claim_date": None,
                    }
                )

        if not data:
            return None

        df = pd.DataFrame(data)
        return df

    def get_monthly_distribution(self):
        """
        Группировка данных по месяцам

        Возвращает:
        {
            "labels": ["2024-11", "2024-12", "2025-01", ...],
            "labels_formatted": ["Ноя 2024", "Дек 2024", "Янв 2025", ...],
            "manufacture": [120, 100, 95, ...],
            "reclamations": [0, 5, 10, ...],
            "claims": [0, 0, 2, ...]
        }
        """
        df = self._get_data_from_db()

        if df is None or df.empty:
            return {
                "labels": [],
                "labels_formatted": [],
                "manufacture": [],
                "reclamations": [],
                "claims": [],
            }

        # ✅ Определяем временной диапазон
        # Левая граница: самая ранняя дата изготовления (не NULL)
        manufacture_dates = df["manufacture_date"].dropna()
        min_date = manufacture_dates.min() if not manufacture_dates.empty else None

        # Правая граница: самая поздняя дата претензии (не NULL)
        claim_dates = df["claim_date"].dropna()
        max_date = claim_dates.max() if not claim_dates.empty else None

        # Если нет дат изготовления, берем min из message_date
        if min_date is None:
            min_date = df["message_date"].min()

        # Если нет претензий, берем max из message_date
        if max_date is None:
            max_date = df["message_date"].max()

        if min_date is None or max_date is None:
            return {
                "labels": [],
                "labels_formatted": [],
                "manufacture": [],
                "reclamations": [],
                "claims": [],
            }

        # ✅ Генерируем все месяцы между min и max
        all_months = (
            pd.date_range(start=min_date, end=max_date, freq="MS")  # Month Start
            .strftime("%Y-%m")
            .tolist()
        )

        # ✅ Группируем по месяцам
        manufacture_counts = df["manufacture_date"].value_counts().to_dict()
        message_counts = df["message_date"].value_counts().to_dict()
        claim_counts = df["claim_date"].value_counts().to_dict()

        # ✅ Заполняем данные для всех месяцев (даже если 0)
        manufacture_data = [manufacture_counts.get(month, 0) for month in all_months]
        reclamation_data = [message_counts.get(month, 0) for month in all_months]
        claim_data = [claim_counts.get(month, 0) for month in all_months]

        # ✅ Форматируем метки для отображения
        labels_formatted = []
        for month_str in all_months:
            year, month = month_str.split("-")
            month_name = self.MONTH_NAMES[int(month)]
            labels_formatted.append(f"{month_name} {year}")

        return {
            "labels": all_months,
            "labels_formatted": labels_formatted,
            "manufacture": manufacture_data,
            "reclamations": reclamation_data,
            "claims": claim_data,
        }

    def generate_analysis(self):
        """Главный метод генерации анализа"""
        try:
            monthly_data = self.get_monthly_distribution()

            if not monthly_data["labels"]:
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
                "monthly_data": monthly_data,
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Ошибка при генерации временного анализа: {str(e)}",
            }

    def save_to_files(self):
        """Сохранение графика в PNG"""
        try:
            analysis_data = self.generate_analysis()

            if not analysis_data["success"]:
                return {"success": False, "error": analysis_data.get("error")}

            monthly_data = analysis_data["monthly_data"]

            if not monthly_data["labels"]:
                return {"success": False, "error": "Нет данных для сохранения"}

            # Определяем суффикс для файла
            if self.all_consumers_mode:
                file_suffix = "все_потребители"
            elif len(self.consumers) == 1:
                file_suffix = self.consumers[0].replace(" ", "_").replace("-", "_")
            else:
                file_suffix = f"{len(self.consumers)}_потребителей"

            chart_path = get_time_analysis_chart_path(self.year, file_suffix)

            # Строим график
            fig, ax = plt.subplots(figsize=(14, 7))

            x = range(len(monthly_data["labels"]))
            width = 0.25

            # Три серии столбцов
            bars1 = ax.bar(
                [i - width for i in x],
                monthly_data["manufacture"],
                width,
                label="Изготовлено",
                color="#4CAF50",
                alpha=0.8,
                edgecolor="#388E3C",
                linewidth=1,
            )
            bars2 = ax.bar(
                x,
                monthly_data["reclamations"],
                width,
                label="Рекламации",
                color="#FF9800",
                alpha=0.8,
                edgecolor="#F57C00",
                linewidth=1,
            )
            bars3 = ax.bar(
                [i + width for i in x],
                monthly_data["claims"],
                width,
                label="Претензии",
                color="#F44336",
                alpha=0.8,
                edgecolor="#D32F2F",
                linewidth=1,
            )

            # ПОДПИСИ ДАННЫХ (скрываем нули)

            # Подписи для bars1 (Изготовлено)
            for bar, value in zip(bars1, monthly_data["manufacture"]):
                if value > 0:
                    height = bar.get_height()
                    ax.text(
                        bar.get_x() + bar.get_width() / 2.0,
                        height,
                        f"{int(value)}",
                        ha="center",
                        va="bottom",
                        fontsize=8,
                        fontweight="bold",
                        color="#2E7D32",
                    )

            # Подписи для bars2 (Рекламации)
            for bar, value in zip(bars2, monthly_data["reclamations"]):
                if value > 0:
                    height = bar.get_height()
                    ax.text(
                        bar.get_x() + bar.get_width() / 2.0,
                        height,
                        f"{int(value)}",
                        ha="center",
                        va="bottom",
                        fontsize=8,
                        fontweight="bold",
                        color="#E65100",
                    )

            # Подписи для bars3 (Претензии)
            for bar, value in zip(bars3, monthly_data["claims"]):
                if value > 0:
                    height = bar.get_height()
                    ax.text(
                        bar.get_x() + bar.get_width() / 2.0,
                        height,
                        f"{int(value)}",
                        ha="center",
                        va="bottom",
                        fontsize=8,
                        fontweight="bold",
                        color="#C62828",
                    )

            # Оформление
            ax.set_xlabel("Период", fontsize=12, fontweight="bold")
            ax.set_ylabel("Количество", fontsize=12, fontweight="bold")
            ax.set_title(
                f'Временной анализ: {analysis_data["consumer_display"]} ({self.year} год)',
                fontsize=14,
                fontweight="bold",
                pad=20,
                loc="left",
            )

            ax.set_xticks(x)
            ax.set_xticklabels(
                monthly_data["labels"], rotation=90, ha="right", fontsize=9
            )

            ax.legend(loc="upper left", fontsize=10, framealpha=0.9)
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

    # def save_to_files(self):
    #     """Сохранение графика в PNG"""
    #     try:
    #         analysis_data = self.generate_analysis()

    #         if not analysis_data["success"]:
    #             return {"success": False, "error": analysis_data.get("error")}

    #         monthly_data = analysis_data["monthly_data"]

    #         if not monthly_data["labels"]:
    #             return {"success": False, "error": "Нет данных для сохранения"}

    #         # Определяем суффикс для файла
    #         if self.all_consumers_mode:
    #             file_suffix = "все_потребители"
    #         elif len(self.consumers) == 1:
    #             file_suffix = self.consumers[0].replace(" ", "_").replace("-", "_")
    #         else:
    #             file_suffix = f"{len(self.consumers)}_потребителей"

    #         chart_path = get_time_analysis_chart_path(self.year, file_suffix)

    #         # ✅ Строим график (grouped bar chart)
    #         fig, ax = plt.subplots(figsize=(14, 7))

    #         x = range(len(monthly_data["labels_formatted"]))
    #         width = 0.25  # Ширина столбца

    #         # Три серии столбцов
    #         bars1 = ax.bar(
    #             [i - width for i in x],
    #             monthly_data["manufacture"],
    #             width,
    #             label="Изготовлено",
    #             color="#4CAF50",
    #             alpha=0.8,
    #         )
    #         bars2 = ax.bar(
    #             x,
    #             monthly_data["reclamations"],
    #             width,
    #             label="Рекламации",
    #             color="#FF9800",
    #             alpha=0.8,
    #         )
    #         bars3 = ax.bar(
    #             [i + width for i in x],
    #             monthly_data["claims"],
    #             width,
    #             label="Претензии",
    #             color="#F44336",
    #             alpha=0.8,
    #         )

    #         # Подписи на столбцах
    #         ax.bar_label(bars1, padding=3, fontsize=8)
    #         ax.bar_label(bars2, padding=3, fontsize=8)
    #         ax.bar_label(bars3, padding=3, fontsize=8)

    #         ax.set_xlabel("Период", fontsize=12, fontweight="bold")
    #         ax.set_ylabel("Количество", fontsize=12, fontweight="bold")
    #         ax.set_title(
    #             f'Временной анализ: {analysis_data["consumer_display"]} ({self.year} год)',
    #             fontsize=14,
    #             fontweight="bold",
    #             pad=20,
    #         )
    #         ax.set_xticks(x)
    #         ax.set_xticklabels(
    #             monthly_data["labels_formatted"], rotation=45, ha="right"
    #         )
    #         ax.legend(loc="upper left", fontsize=10)
    #         ax.grid(True, alpha=0.3, axis="y")

    #         plt.tight_layout()
    #         plt.savefig(chart_path, dpi=300, bbox_inches="tight")
    #         plt.close()

    #         return {
    #             "success": True,
    #             "base_dir": BASE_REPORTS_DIR,
    #             "chart_path": chart_path,
    #         }

    #     except Exception as e:
    #         return {"success": False, "error": str(e)}
