# claims/modules/time_analysis_processor.py
"""Процессор для временного анализа: количество рекламаций → сумма претензий"""

import pandas as pd
import matplotlib
from datetime import date

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from django.db.models import Q, Prefetch

from claims.models import Claim
from reclamations.models import Reclamation
from reports.config.paths import (
    get_time_analysis_chart_path,
    BASE_REPORTS_DIR,
)


class TimeAnalysisProcessor:
    """Временной анализ конверсии: количество рекламаций → сумма претензий"""

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

    def __init__(self, year=None, consumers=None, exchange_rate=None):
        """
        year: год анализа
        consumers: список потребителей (пустой = все)
        all_consumers_mode: флаг - все потребители
        exchange_rate: курс конвертации валюты
        """
        self.today = date.today()
        self.year = year or self.today.year
        self.consumers = consumers or []
        self.all_consumers_mode = len(self.consumers) == 0
        self.exchange_rate = exchange_rate or 0.03

    def _convert_to_byn(self, amount, currency):
        """Конвертация суммы в BYN"""
        if not amount:
            return 0.00

        amount_decimal = float(str(amount))

        if currency == "BYN":
            return amount_decimal
        elif currency == "RUR":
            return amount_decimal * self.exchange_rate
        else:
            return 0.00

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
        - message_date_formatted
        - claim_number
        - claim_date_formatted
        - claim_cost (признанная сумма по претензии claim.costs_all)
        - type_money
        """
        # Фильтруем рекламации на уровне БД
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
            reclamations__isnull=False,
            claim_date__year=self.year,  # Только претензии текущего года
        ).distinct()

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
                        "message_date": message_date_formatted,
                        "claim_number": claim.claim_number,
                        "claim_date": claim_date_formatted,
                        "claim_cost": claim.costs_all,
                        "type_money": claim.type_money,
                    }
                )

            # Добавляем рекламации БЕЗ претензий (для подсчета сообщений)
            if not reclamation.recognized_claims_cache:
                data.append(
                    {
                        "reclamation_id": reclamation.id,
                        "message_date": message_date_formatted,
                        "claim_number": None,
                        "claim_date": None,
                        "claim_cost": None,
                        "type_money": None,
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
            "reclamations": [0, 5, 10, ...],
            "claims_counts": [10, 4, 5, ...]
            "claims_costs": [254.23, 105745.14, 45500.98, ...]
        }
        """
        df = self._get_data_from_db()

        if df is None or df.empty:
            return {
                "labels": [],
                "labels_formatted": [],
                "reclamations": [],
                "claims_counts": [],
                "claims_costs": [],
            }

        # Определяем временной диапазон
        # Левая граница: самая ранняя дата сообщения
        min_date = df["message_date"].min()

        # Правая граница: самая поздняя дата сообщения
        max_date = df["message_date"].max()

        if min_date is None or max_date is None:
            return {
                "labels": [],
                "labels_formatted": [],
                "reclamations": [],
                "claims_counts": [],
                "claims_costs": [],
            }

        # Генерируем все месяцы между min и max
        all_months = (
            pd.date_range(start=min_date, end=max_date, freq="MS")  # Month Start
            .strftime("%Y-%m")
            .tolist()
        )

        # ----------------- Группируем по месяцам -------------------
        # Считаем количество рекламаций по месяцам и записываем в словарь ("2025-01": 12, "2025-02": 47, ...)
        message_counts = df["message_date"].value_counts().to_dict()
        # Считаем количество претензий по месяцам и записываем в словарь
        claim_counts = df["claim_date"].value_counts().to_dict()

        # Считаем признанные суммы и записываем в словарь
        # Создаем временный столбец с конвертированными признанными суммами
        df["claim_cost_byn"] = df.apply(
            lambda row: self._convert_to_byn(row["claim_cost"], row["type_money"]),
            axis=1,
        )

        # Фильтруем только строки с claim_date
        claims_only = df.dropna(subset=["claim_date"]).drop_duplicates(
            subset="claim_number"
        )
        # print("=== ГРУППЫ С ПРЕТЕНЗИЯМИ ===")
        # for date, group in claims_only.groupby("claim_date"):
        #     print(f"\n{date}:")
        #     print(group[["claim_number", "claim_cost", "claim_cost_byn"]])

        # Группируем по дате претензии, суммируем признанные суммы и записываем в словарь
        claim_costs = (
            claims_only.groupby("claim_date")["claim_cost_byn"].sum().to_dict()
        )

        # # Удаляем временный столбец
        # df = df.drop("claim_cost_byn", axis=1)

        # Заполняем данные для всех месяцев (даже если 0)
        reclamation_data = [message_counts.get(month, 0) for month in all_months]
        claim_data_counts = [claim_counts.get(month, 0) for month in all_months]
        claim_data_costs = [claim_costs.get(month, 0) for month in all_months]

        # Форматируем метки для отображения
        labels_formatted = []
        for month_str in all_months:
            year, month = month_str.split("-")
            month_name = self.MONTH_NAMES[int(month)]
            labels_formatted.append(f"{month_name} {year}")

        return {
            "labels": all_months,
            "labels_formatted": labels_formatted,
            "reclamations": reclamation_data,
            "claims_counts": claim_data_counts,
            "claims_costs": claim_data_costs,
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
        """Сохранение графика в PNG с двумя осями Y"""
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

            # ----------------- СОЗДАНИЕ ГРАФИКА ------------------
            # Создаем график с двумя осями Y
            fig, ax1 = plt.subplots(figsize=(14, 7))

            # Создаем правую ось Y
            ax2 = ax1.twinx()

            x = range(len(monthly_data["labels"]))

            # ЛЕВАЯ ОСЬ (ax1) - Количество (шт.)
            bars1 = ax1.plot(
                x,
                monthly_data["claims_counts"],
                marker="o",
                linewidth=3,
                markersize=6,
                label="Количество претензий",
                color="#F44336",
                alpha=0.8,
            )

            bars2 = ax1.plot(
                x,
                monthly_data["reclamations"],
                marker="o",
                linewidth=3,
                markersize=6,
                label="Количество рекламаций",
                color="#FF9800",
                alpha=0.8,
            )

            # ПРАВАЯ ОСЬ (ax2) - Сумма претензий (руб.)
            bars3 = ax2.plot(
                x,
                monthly_data["claims_costs"],
                marker="o",
                linewidth=3,
                markersize=6,
                label="Сумма претензий (руб.)",
                color="#2E7D32",
                alpha=0.8,
            )

            # ---------------------- ПОДПИСИ ДАННЫХ ---------------------
            # Определяем масштаб каждой оси для расчета отступов по вертикали
            max_left = max(
                max(monthly_data["claims_counts"]), max(monthly_data["reclamations"])
            )
            max_right = (
                max(monthly_data["claims_costs"]) if monthly_data["claims_costs"] else 1
            )

            # Жесткие отступы пропорционально масштабу левой или правой оси
            left_offset = max(1, max_left * 0.02)  # 2% от максимума или минимум 1
            right_offset = max(1000, max_right * 0.02)  # 2% или минимум 1000

            # ПОДПИСИ ДАННЫХ для левой оси
            # Подписи для bars1 (Количество претензий)
            for i, value in enumerate(monthly_data["claims_counts"]):
                if value > 0:
                    ax1.text(
                        i,
                        value + left_offset,  # Добавляем отступ вверх
                        f"{int(value)}",
                        ha="center",
                        va="bottom",
                        fontsize=8,
                        fontweight="bold",
                        color="#C62828",
                        bbox=dict(  # Фон для читаемости
                            boxstyle="round,pad=0.2", facecolor="white", alpha=0.8
                        ),
                    )

            # Подписи для bars2 (Количество рекламаций)
            for i, value in enumerate(monthly_data["reclamations"]):
                if value > 0:
                    ax1.text(
                        i,
                        value + left_offset,  # Добавляем отступ вверх
                        f"{int(value)}",
                        ha="center",
                        va="bottom",
                        fontsize=8,
                        fontweight="bold",
                        color="#F57C00",
                        bbox=dict(  # Фон для читаемости
                            boxstyle="round,pad=0.2", facecolor="white", alpha=0.8
                        ),
                    )

            # ПОДПИСИ для правой оси
            # Подписи для bars3 (Суммы претензий)
            for i, value in enumerate(monthly_data["claims_costs"]):
                if value > 0:
                    ax2.text(
                        i,
                        value - right_offset,  # Добавляем отступ вниз
                        # Форматируем числа с пробелами
                        f"{value:,.2f}".replace(",", " "),
                        ha="center",
                        va="top",
                        fontsize=8,
                        fontweight="bold",
                        color="#2E7D32",
                        bbox=dict(  # Фон для читаемости
                            boxstyle="round,pad=0.2", facecolor="white", alpha=0.8
                        ),
                    )

            # ------------ ОФОРМЛЕНИЕ ОСЕЙ --------------
            # Левая ось
            ax1.set_xlabel("Период", fontsize=12, fontweight="bold")
            ax1.set_ylabel(
                "Количество (шт.)", fontsize=12, fontweight="bold", color="#F57C00"
            )
            ax1.tick_params(axis="y", labelcolor="#F57C00")
            ax1.set_ylim(bottom=0)

            # Правая ось
            ax2.set_ylabel(
                "Сумма претензий (руб.)",
                fontsize=12,
                fontweight="bold",
                color="#2E7D32",
            )
            ax2.tick_params(axis="y", labelcolor="#2E7D32")
            ax2.set_ylim(bottom=0)

            # Форматирование правой оси с разделителями тысяч
            ax2.yaxis.set_major_formatter(
                plt.FuncFormatter(lambda x, p: f"{int(x):,}".replace(",", " "))
            )

            # Заголовок
            ax1.set_title(
                f'Временной анализ: {analysis_data["consumer_display"]} ({self.year} год)',
                fontsize=14,
                fontweight="bold",
                pad=20,
                loc="left",
            )

            # Подписи оси X
            ax1.set_xticks(x)
            ax1.set_xticklabels(
                monthly_data["labels"], rotation=90, ha="right", fontsize=9
            )

            # ---------------- ОБЪЕДИНЕННАЯ ЛЕГЕНДА -------------------
            # Получаем элементы легенды с обеих осей
            lines1, labels1 = ax1.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()

            # Объединяем и создаем общую легенду
            ax1.legend(
                lines1 + lines2,
                labels1 + labels2,
                loc="upper right",
                fontsize=10,
                framealpha=0.9,
            )

            # Сетка только для левой оси
            ax1.grid(True, alpha=0.3, axis="y", linestyle="--")
            ax1.grid(True, alpha=0.3, axis="x", linestyle="--")

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
