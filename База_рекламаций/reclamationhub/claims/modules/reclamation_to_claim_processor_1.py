# claims/modules/reclamation_to_claim_processor.py
"""Процессор для анализа конверсии рекламация → претензия"""

import pandas as pd
from datetime import date
from decimal import Decimal

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from reports.config.paths import (
    get_reclamation_to_claim_chart_path,
    get_reclamation_to_claim_table_path,
    BASE_REPORTS_DIR,
)

from claims.models import Claim
from reclamations.models import Reclamation


class ReclamationToClaimProcessor:
    """Анализ связи рекламация → претензия"""

    # Названия месяцев
    MONTH_NAMES = {
        1: "Январь",
        2: "Февраль",
        3: "Март",
        4: "Апрель",
        5: "Май",
        6: "Июнь",
        7: "Июль",
        8: "Август",
        9: "Сентябрь",
        10: "Октябрь",
        11: "Ноябрь",
        12: "Декабрь",
    }

    def __init__(self, year=None, consumers=None, exchange_rate=None):
        """
        year: год анализа рекламаций
        consumers: список потребителей (пустой = все)
        exchange_rate: курс RUR → BYN
        """
        self.today = date.today()
        self.year = year or self.today.year
        self.consumers = consumers or []
        self.all_consumers_mode = len(self.consumers) == 0
        self.exchange_rate = exchange_rate or Decimal("0.03")

    def _convert_to_byn(self, amount, currency):
        """Конвертация суммы в BYN"""
        if not amount:
            return Decimal("0.00")

        amount_decimal = Decimal(str(amount))

        if currency == "BYN":
            return amount_decimal
        elif currency == "RUR":
            return amount_decimal * self.exchange_rate
        else:
            return Decimal("0.00")

    def _get_reclamation_date(self, reclamation):
        """
        Получение даты рекламации с приоритетом:
        1. consumer_act_date
        2. end_consumer_act_date
        """
        return reclamation.consumer_act_date or reclamation.end_consumer_act_date

    # ========== ГРУППА A: Рекламации из базы ==========

    def get_group_a_summary(self):
        """
        Карточки для Группы A (всегда для ВСЕХ потребителей)

        Возвращает:
        {
            "total_reclamations": 150,
            "escalated_reclamations": 45,
            "escalation_rate": 30.0,
            "average_days": 18
        }
        """
        # Берем рекламации за выбранный год
        reclamations = Reclamation.objects.filter(year=self.year)
        total_reclamations = reclamations.count()

        if total_reclamations == 0:
            return {
                "total_reclamations": 0,
                "escalated_reclamations": 0,
                "escalation_rate": 0,
                "average_days": 0,
            }

        # Для каждой рекламации проверяем наличие признанных претензий
        escalated_count = 0
        days_list = []

        for reclamation in reclamations:
            # Ищем признанные претензии к этой рекламации
            claims = reclamation.claims.filter(
                result_claim="ACCEPTED",
                response_number__isnull=False,
                response_date__isnull=False,
                claim_date__lte=self.today,  # До текущей даты (динамический срез)
            )

            if claims.exists():
                escalated_count += 1

                # Считаем срок эскалации
                reclamation_date = self._get_reclamation_date(reclamation)
                if reclamation_date:
                    for claim in claims:
                        if claim.claim_date:
                            days = (claim.claim_date - reclamation_date).days
                            if days >= 0:  # Только положительные сроки
                                days_list.append(days)

        # Средний срок эскалации
        average_days = round(sum(days_list) / len(days_list)) if days_list else 0

        # Процент эскалации
        escalation_rate = (
            round((escalated_count / total_reclamations) * 100, 1)
            if total_reclamations > 0
            else 0
        )

        return {
            "total_reclamations": total_reclamations,
            "escalated_reclamations": escalated_count,
            "escalation_rate": escalation_rate,
            "average_days": average_days,
        }

    def get_group_a_monthly_conversion(self):
        """
        График: Динамика конверсии по месяцам (для выбранных потребителей или всех)

        Возвращает:
        {
            "labels": ["Январь", "Февраль", ...],
            "conversion_rates": [33.3, 25.0, ...]
        }
        """
        # Берем рекламации за выбранный год
        reclamations = Reclamation.objects.filter(year=self.year)

        if not reclamations.exists():
            return {"labels": [], "conversion_rates": []}

        # Группируем по месяцам даты поступления сообщения
        monthly_data = {}

        for reclamation in reclamations:
            if not reclamation.message_received_date:
                continue

            month = reclamation.message_received_date.month

            if month not in monthly_data:
                monthly_data[month] = {"total": 0, "escalated": 0}

            # Проверяем признанные претензии
            claims = reclamation.claims.filter(
                result_claim="ACCEPTED",
                response_number__isnull=False,
                claim_date__lte=self.today,
            )

            # Фильтр по потребителям
            if not self.all_consumers_mode:
                claims = claims.filter(consumer_name__in=self.consumers)

            monthly_data[month]["total"] += 1
            if claims.exists():
                monthly_data[month]["escalated"] += 1

        # Формируем данные для графика
        labels = []
        conversion_rates = []

        for month in sorted(monthly_data.keys()):
            labels.append(self.MONTH_NAMES[month])

            total = monthly_data[month]["total"]
            escalated = monthly_data[month]["escalated"]

            conversion = round((escalated / total) * 100, 1) if total > 0 else 0
            conversion_rates.append(conversion)

        return {"labels": labels, "conversion_rates": conversion_rates}

    def get_group_a_time_distribution(self):
        """
        График: Распределение по срокам эскалации (для выбранных или всех)

        Возвращает:
        {
            "labels": ["0-90 дней", "91-180 дней", "181-270 дней", "271-360 дней", ">360 дней"],
            "counts": [5, 12, 18, 10]
        }
        """
        reclamations = Reclamation.objects.filter(year=self.year)

        if not reclamations.exists():
            return {
                "labels": [
                    "0-90 дней",
                    "91-180 дней",
                    "181-270 дней",
                    "271-360 дней",
                    ">360 дней",
                ],
                "counts": [0, 0, 0, 0],
            }

        # Распределение по интервалам
        intervals = {"0-90": 0, "91-180": 0, "181-270": 0, "271-360": 0, ">360": 0}

        for reclamation in reclamations:
            claims = reclamation.claims.filter(
                result_claim="ACCEPTED",
                response_number__isnull=False,
                claim_date__lte=self.today,
            )

            # Фильтр по потребителям
            if not self.all_consumers_mode:
                claims = claims.filter(consumer_name__in=self.consumers)

            reclamation_date = self._get_reclamation_date(reclamation)

            if claims.exists() and reclamation_date:
                for claim in claims:
                    if claim.claim_date:
                        days = (claim.claim_date - reclamation_date).days

                        if days < 0:
                            continue
                        elif days <= 90:
                            intervals["0-90"] += 1
                        elif 90 < days <= 180:
                            intervals["91-180"] += 1
                        elif 180 < days <= 270:
                            intervals["181-270"] += 1
                        elif 270 < days <= 360:
                            intervals["271-360"] += 1
                        else:
                            intervals[">360"] += 1

        return {
            "labels": [
                "0-90 дней",
                "91-180 дней",
                "181-270 дней",
                "271-360 дней",
                ">360 дней",
            ],
            "counts": [
                intervals["0-90"],
                intervals["91-180"],
                intervals["181-270"],
                intervals["271-360"],
                intervals[">360"],
            ],
        }

    def get_group_a_top_consumers(self):
        """
        Таблица: TOP потребителей (для выбранных или всех)

        Возвращает:
        [
            {
                "consumer": "ЯМЗ",
                "total_reclamations": 25,
                "escalated": 12,
                "conversion_rate": 48.0,
                "average_days": 21
            },
            ...
        ]
        """
        reclamations = Reclamation.objects.filter(year=self.year)

        if not reclamations.exists():
            return []

        # Собираем данные по потребителям
        consumer_data = {}

        for reclamation in reclamations:
            # Получаем признанные претензии
            claims = reclamation.claims.filter(
                result_claim="ACCEPTED",
                response_number__isnull=False,
                claim_date__lte=self.today,
            )

            if not claims.exists():
                continue

            # Группируем по потребителям из претензий
            for claim in claims:
                consumer = claim.consumer_name

                if not consumer:
                    continue

                # Фильтр по выбранным потребителям
                if not self.all_consumers_mode and consumer not in self.consumers:
                    continue

                if consumer not in consumer_data:
                    consumer_data[consumer] = {
                        "total_reclamations": 0,
                        "escalated": 0,
                        "days_list": [],
                    }

                # Считаем срок
                reclamation_date = self._get_reclamation_date(reclamation)
                if reclamation_date and claim.claim_date:
                    days = (claim.claim_date - reclamation_date).days
                    if days >= 0:
                        consumer_data[consumer]["days_list"].append(days)

                consumer_data[consumer]["escalated"] += 1

        # Считаем общее количество рекламаций по потребителям
        # (для этого нужно пройтись по всем рекламациям еще раз)
        for reclamation in reclamations:
            for claim in reclamation.claims.all():
                consumer = claim.consumer_name

                if not consumer:
                    continue

                if not self.all_consumers_mode and consumer not in self.consumers:
                    continue

                if consumer in consumer_data:
                    consumer_data[consumer]["total_reclamations"] += 1

        # Формируем результат
        result = []
        for consumer, data in consumer_data.items():
            total = data["total_reclamations"]
            escalated = data["escalated"]
            days_list = data["days_list"]

            conversion_rate = round((escalated / total) * 100, 1) if total > 0 else 0
            average_days = round(sum(days_list) / len(days_list)) if days_list else 0

            result.append(
                {
                    "consumer": consumer,
                    "total_reclamations": total,
                    "escalated": escalated,
                    "conversion_rate": conversion_rate,
                    "average_days": average_days,
                }
            )

        # Сортируем по конверсии (убыв.)
        result.sort(key=lambda x: x["conversion_rate"], reverse=True)

        return result

    # ========== ГРУППА B: Претензии без связи ==========

    def get_group_b_summary(self):
        """
        Карточки для Группы B

        Возвращает:
        {
            "claims_without_link": 12,
            "claims_without_date": 3,
            "total_amount_byn": "125000.00"
        }
        """
        # Берем признанные претензии за выбранный год БЕЗ связи с рекламациями
        claims_filter = {
            "claim_date__year": self.year,
            "result_claim": "ACCEPTED",
            "response_number__isnull": False,
        }

        claims_without_link = Claim.objects.filter(**claims_filter)

        # Проверяем отсутствие связи через ManyToMany
        claims_without_link = [
            claim for claim in claims_without_link if not claim.reclamations.exists()
        ]

        # Фильтр по потребителям
        if not self.all_consumers_mode:
            claims_without_link = [
                claim
                for claim in claims_without_link
                if claim.consumer_name in self.consumers
            ]

        total_claims = len(claims_without_link)

        # Считаем претензии без даты рекламации
        claims_without_date = sum(
            1 for claim in claims_without_link if not claim.reclamation_act_date
        )

        # Считаем общую сумму
        total_amount_byn = Decimal("0.00")
        for claim in claims_without_link:
            currency = claim.type_money or "BYN"
            if claim.costs_all:
                total_amount_byn += self._convert_to_byn(claim.costs_all, currency)

        return {
            "claims_without_link": total_claims,
            "claims_without_date": claims_without_date,
            "total_amount_byn": f"{total_amount_byn:.2f}",
        }

    def get_group_b_time_distribution(self):
        """
        График: Распределение по срокам (претензии без связи, но с датой рекламации)

        Возвращает:
        {
            "labels": ["0-90 дней", "91-180 дней", "181-270 дней", "271-360 дней", ">360 дней"],
            "counts": [2, 5, 3, 2]
        }
        """
        # Берем претензии без связи
        claims_filter = {
            "claim_date__year": self.year,
            "result_claim": "ACCEPTED",
            "response_number__isnull": False,
        }

        claims_without_link = Claim.objects.filter(**claims_filter)
        claims_without_link = [
            claim for claim in claims_without_link if not claim.reclamations.exists()
        ]

        # Фильтр по потребителям
        if not self.all_consumers_mode:
            claims_without_link = [
                claim
                for claim in claims_without_link
                if claim.consumer_name in self.consumers
            ]

        # Распределение по интервалам
        intervals = {"0-90": 0, "91-180": 0, "181-270": 0, "271-360": 0, ">360": 0}

        for claim in claims_without_link:
            # Берем дату из поля claim
            if claim.reclamation_act_date and claim.claim_date:
                days = (claim.claim_date - claim.reclamation_act_date).days

                if days < 0:
                    continue
                elif days <= 90:
                    intervals["0-90"] += 1
                elif 90 < days <= 180:
                    intervals["91-180"] += 1
                elif 180 < days <= 270:
                    intervals["181-270"] += 1
                elif 270 < days <= 360:
                    intervals["271-360"] += 1
                else:
                    intervals[">360"] += 1

        return {
            "labels": [
                "0-90 дней",
                "91-180 дней",
                "181-270 дней",
                "271-360 дней",
                ">360 дней",
            ],
            "counts": [
                intervals["0-90"],
                intervals["91-180"],
                intervals["181-270"],
                intervals["271-360"],
                intervals[">360"],
            ],
        }

    # ========== Главный метод ==========

    def generate_analysis(self):
        """Главный метод генерации анализа"""
        try:
            # Группа A
            group_a_summary = self.get_group_a_summary()
            group_a_monthly = self.get_group_a_monthly_conversion()
            group_a_time_dist = self.get_group_a_time_distribution()
            group_a_consumers = self.get_group_a_top_consumers()

            # Группа B
            group_b_summary = self.get_group_b_summary()
            group_b_time_dist = self.get_group_b_time_distribution()

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
                "exchange_rate": str(self.exchange_rate),
                "group_a": {
                    "summary_cards": group_a_summary,
                    "monthly_conversion": group_a_monthly,
                    "time_distribution": group_a_time_dist,
                    "top_consumers": group_a_consumers,
                },
                "group_b": {
                    "summary_cards": group_b_summary,
                    "time_distribution": group_b_time_dist,
                },
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Ошибка при генерации анализа: {str(e)}",
            }

    def save_to_files(self):
        """Сохранение графиков и таблиц в файлы"""
        try:
            # Получаем данные
            analysis_data = self.generate_analysis()

            if not analysis_data["success"]:
                return {"success": False, "error": "Не удалось сгенерировать данные"}

            group_a = analysis_data["group_a"]
            group_b = analysis_data["group_b"]

            # Определяем суффикс для файлов
            if self.all_consumers_mode:
                file_suffix = "все_потребители"
            elif len(self.consumers) == 1:
                file_suffix = self.consumers[0].replace(" ", "_").replace("-", "_")
            else:
                file_suffix = f"{len(self.consumers)}_потребителей"

            # === График 1: Динамика конверсии ===
            chart1_path = get_reclamation_to_claim_chart_path(
                self.year, f"{file_suffix}_динамика"
            )

            if group_a["monthly_conversion"]["labels"]:
                fig, ax = plt.subplots(figsize=(12, 6))

                labels = group_a["monthly_conversion"]["labels"]
                rates = group_a["monthly_conversion"]["conversion_rates"]

                ax.plot(
                    labels,
                    rates,
                    marker="o",
                    linewidth=2.5,
                    markersize=8,
                    color="orange",
                )

                # Подписи данных
                for i, value in enumerate(rates):
                    if value > 0:
                        ax.text(
                            i,
                            value,
                            f"{value:.1f}%",
                            ha="center",
                            va="bottom",
                            fontsize=9,
                            color="darkorange",
                            fontweight="bold",
                            bbox=dict(
                                boxstyle="round,pad=0.4",
                                facecolor="white",
                                edgecolor="orange",
                                alpha=0.8,
                            ),
                        )

                ax.set_title(
                    f"Динамика конверсии рекламация → претензия за {self.year} год (%)",
                    fontsize=14,
                    fontweight="bold",
                    pad=20,
                )
                ax.set_xlabel("Месяц", fontsize=11, fontweight="bold")
                ax.set_ylabel("Конверсия (%)", fontsize=11, fontweight="bold")
                ax.grid(True, alpha=0.3, linestyle="--")
                plt.xticks(rotation=45, ha="right")
                plt.tight_layout()
                plt.savefig(chart1_path, dpi=300, bbox_inches="tight")
                plt.close()

            # === График 2: Распределение по срокам (Группа A) ===
            chart2_path = get_reclamation_to_claim_chart_path(
                self.year, f"{file_suffix}_сроки_A"
            )

            if sum(group_a["time_distribution"]["counts"]) > 0:
                fig, ax = plt.subplots(figsize=(10, 6))

                labels = group_a["time_distribution"]["labels"]
                counts = group_a["time_distribution"]["counts"]

                bars = ax.bar(
                    labels, counts, color=["red", "orange", "green", "blue"], alpha=0.7
                )

                # Подписи на столбцах
                for bar, count in zip(bars, counts):
                    if count > 0:
                        height = bar.get_height()
                        ax.text(
                            bar.get_x() + bar.get_width() / 2.0,
                            height,
                            f"{int(count)}",
                            ha="center",
                            va="bottom",
                            fontsize=10,
                            fontweight="bold",
                        )

                ax.set_title(
                    f"Распределение по срокам эскалации (Группа A) - {self.year} год",
                    fontsize=14,
                    fontweight="bold",
                    pad=20,
                )
                ax.set_xlabel("Интервал (дней)", fontsize=11, fontweight="bold")
                ax.set_ylabel("Количество претензий", fontsize=11, fontweight="bold")
                ax.grid(True, alpha=0.3, axis="y")
                plt.tight_layout()
                plt.savefig(chart2_path, dpi=300, bbox_inches="tight")
                plt.close()

            # === График 3: Распределение по срокам (Группа B) ===
            chart3_path = get_reclamation_to_claim_chart_path(
                self.year, f"{file_suffix}_сроки_B"
            )

            if sum(group_b["time_distribution"]["counts"]) > 0:
                fig, ax = plt.subplots(figsize=(10, 6))

                labels = group_b["time_distribution"]["labels"]
                counts = group_b["time_distribution"]["counts"]

                bars = ax.bar(
                    labels, counts, color=["red", "orange", "green", "blue"], alpha=0.7
                )

                for bar, count in zip(bars, counts):
                    if count > 0:
                        height = bar.get_height()
                        ax.text(
                            bar.get_x() + bar.get_width() / 2.0,
                            height,
                            f"{int(count)}",
                            ha="center",
                            va="bottom",
                            fontsize=10,
                            fontweight="bold",
                        )

                ax.set_title(
                    f"Распределение по срокам (Группа B - претензии без связи) - {self.year} год",
                    fontsize=14,
                    fontweight="bold",
                    pad=20,
                )
                ax.set_xlabel("Интервал (дней)", fontsize=11, fontweight="bold")
                ax.set_ylabel("Количество претензий", fontsize=11, fontweight="bold")
                ax.grid(True, alpha=0.3, axis="y")
                plt.tight_layout()
                plt.savefig(chart3_path, dpi=300, bbox_inches="tight")
                plt.close()

            # === Таблица ===
            table_path = get_reclamation_to_claim_table_path(self.year, file_suffix)

            with open(table_path, "w", encoding="utf-8") as f:
                f.write(f"АНАЛИЗ КОНВЕРСИИ РЕКЛАМАЦИЯ → ПРЕТЕНЗИЯ ЗА {self.year} ГОД\n")
                f.write(f"Курс: 1 RUR = {self.exchange_rate} BYN\n")
                f.write("=" * 100 + "\n\n")

                # Группа A
                f.write("ГРУППА A: РЕКЛАМАЦИИ ИЗ БАЗЫ\n")
                f.write("-" * 100 + "\n")
                f.write(
                    f"Всего рекламаций: {group_a['summary_cards']['total_reclamations']}\n"
                )
                f.write(
                    f"Переросли в претензии: {group_a['summary_cards']['escalated_reclamations']} "
                    f"({group_a['summary_cards']['escalation_rate']}%)\n"
                )
                f.write(
                    f"Средний срок эскалации: {group_a['summary_cards']['average_days']} дней\n\n"
                )

                # Таблица потребителей
                if group_a["top_consumers"]:
                    f.write("TOP ПОТРЕБИТЕЛЕЙ:\n")
                    f.write(
                        f"{'№':<5}{'Потребитель':<30}{'Рекламаций':<15}{'Претензий':<15}"
                        f"{'Конверсия':<15}{'Средний срок':<15}\n"
                    )
                    f.write("-" * 100 + "\n")

                    for idx, consumer in enumerate(group_a["top_consumers"], 1):
                        f.write(
                            f"{idx:<5}{consumer['consumer']:<30}{consumer['total_reclamations']:<15}"
                            f"{consumer['escalated']:<15}{consumer['conversion_rate']:<15}"
                            f"{consumer['average_days']:<15}\n"
                        )

                f.write("\n" + "=" * 100 + "\n\n")

                # Группа B
                f.write("ГРУППА B: ПРЕТЕНЗИИ БЕЗ СВЯЗИ\n")
                f.write("-" * 100 + "\n")
                f.write(
                    f"Претензий без связи: {group_b['summary_cards']['claims_without_link']}\n"
                )
                f.write(
                    f"Претензий без даты рекламации: {group_b['summary_cards']['claims_without_date']}\n"
                )
                f.write(
                    f"Общая сумма: {group_b['summary_cards']['total_amount_byn']} BYN\n"
                )

            return {
                "success": True,
                "base_dir": BASE_REPORTS_DIR,
                "chart1_path": chart1_path,
                "chart2_path": chart2_path,
                "chart3_path": chart3_path,
                "table_path": table_path,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}
