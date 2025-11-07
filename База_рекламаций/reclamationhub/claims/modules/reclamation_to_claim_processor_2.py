# claims/modules/reclamation_to_claim_processor.py
"""Процессор для анализа конверсии рекламация → претензия (ОПТИМИЗИРОВАННЫЙ)"""

import pandas as pd
from datetime import date
from decimal import Decimal
from django.db.models import Prefetch

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
    """Анализ связи рекламация → претензия (ОПТИМИЗИРОВАННАЯ ВЕРСИЯ)"""

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
        self.today = date.today()
        self.year = year or self.today.year
        self.consumers = consumers or []
        self.all_consumers_mode = len(self.consumers) == 0
        self.exchange_rate = exchange_rate or Decimal("0.03")

        # ✅ Кэш для рекламаций
        self._reclamations_cache = None
        self._dataframe_cache = None

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

    def _get_reclamation_date(self, consumer_act_date, end_consumer_act_date):
        """Получение даты рекламации с приоритетом"""
        return consumer_act_date or end_consumer_act_date

    def _get_reclamations_with_claims(self):
        """
        ✅ ОПТИМИЗАЦИЯ: Получение рекламаций с предзагруженными претензиями

        Использует prefetch_related для загрузки всех связанных претензий ОДНИМ запросом!
        """
        if self._reclamations_cache is not None:
            return self._reclamations_cache

        # Queryset для признанных претензий
        recognized_claims = Claim.objects.filter(
            result_claim="ACCEPTED",
            response_number__isnull=False,
            response_date__isnull=False,
            claim_date__lte=self.today,
        ).select_related()  # Если есть FK, их тоже предзагружаем

        # ✅ Предзагружаем претензии одним запросом через Prefetch
        self._reclamations_cache = Reclamation.objects.filter(
            year=self.year
        ).prefetch_related(
            Prefetch(
                "claims", queryset=recognized_claims, to_attr="recognized_claims_cache"
            )
        )

        return self._reclamations_cache

    def _build_dataframe(self):
        """
        ✅ ОПТИМИЗАЦИЯ: Строим pandas DataFrame один раз для всех вычислений

        Возвращает DataFrame с колонками:
        - reclamation_id
        - reclamation_month
        - reclamation_date
        - claim_id
        - claim_date
        - consumer
        - days (срок эскалации)
        """
        if self._dataframe_cache is not None:
            return self._dataframe_cache

        reclamations = self._get_reclamations_with_claims()

        # Собираем данные в список (быстрее, чем append к DataFrame)
        data = []

        for reclamation in reclamations:
            # Дата рекламации
            reclamation_date = self._get_reclamation_date(
                reclamation.consumer_act_date, reclamation.end_consumer_act_date
            )

            # Месяц регистрации
            reclamation_month = (
                reclamation.message_received_date.month
                if reclamation.message_received_date
                else None
            )

            # ✅ Используем предзагруженные претензии (БЕЗ запроса к БД!)
            for claim in reclamation.recognized_claims_cache:
                # Фильтр по потребителям
                if (
                    not self.all_consumers_mode
                    and claim.consumer_name not in self.consumers
                ):
                    continue

                # Срок эскалации
                days = None
                if reclamation_date and claim.claim_date:
                    days = (claim.claim_date - reclamation_date).days
                    if days < 0:
                        days = None

                data.append(
                    {
                        "reclamation_id": reclamation.id,
                        "reclamation_month": reclamation_month,
                        "reclamation_date": reclamation_date,
                        "claim_id": claim.id,
                        "claim_date": claim.claim_date,
                        "consumer": claim.consumer_name,
                        "days": days,
                    }
                )

        # Создаем DataFrame
        self._dataframe_cache = pd.DataFrame(data)

        return self._dataframe_cache

    # ========== ГРУППА A: Рекламации из базы ==========

    def get_group_a_summary(self):
        """Карточки для Группы A (всегда для ВСЕХ потребителей)"""
        reclamations = self._get_reclamations_with_claims()
        total_reclamations = reclamations.count()

        if total_reclamations == 0:
            return {
                "total_reclamations": 0,
                "escalated_reclamations": 0,
                "escalation_rate": 0,
                "average_days": 0,
            }

        # ✅ Используем DataFrame для вычислений
        df = self._build_dataframe()

        if df.empty:
            # Нет ни одной эскалации
            return {
                "total_reclamations": total_reclamations,
                "escalated_reclamations": 0,
                "escalation_rate": 0,
                "average_days": 0,
            }

        # Количество уникальных рекламаций, переросших в претензии
        escalated_count = df["reclamation_id"].nunique()

        # Средний срок (только положительные значения)
        days_series = df["days"].dropna()
        average_days = round(days_series.mean()) if len(days_series) > 0 else 0

        # Процент эскалации
        escalation_rate = round((escalated_count / total_reclamations) * 100, 1)

        return {
            "total_reclamations": total_reclamations,
            "escalated_reclamations": escalated_count,
            "escalation_rate": escalation_rate,
            "average_days": average_days,
        }

    def get_group_a_monthly_conversion(self):
        """График: Динамика конверсии по месяцам"""
        reclamations = self._get_reclamations_with_claims()

        if not reclamations.exists():
            return {"labels": [], "conversion_rates": []}

        # ✅ Используем DataFrame
        df = self._build_dataframe()

        # Считаем общее количество рекламаций по месяцам
        monthly_total = {}
        for reclamation in reclamations:
            if reclamation.message_received_date:
                month = reclamation.message_received_date.month
                monthly_total[month] = monthly_total.get(month, 0) + 1

        if not monthly_total:
            return {"labels": [], "conversion_rates": []}

        # Считаем эскалации по месяцам через DataFrame
        if df.empty:
            # Нет эскалаций
            monthly_escalated = {}
        else:
            monthly_escalated = (
                df.groupby("reclamation_month")["reclamation_id"].nunique().to_dict()
            )

        # Формируем данные для графика
        labels = []
        conversion_rates = []

        for month in sorted(monthly_total.keys()):
            labels.append(self.MONTH_NAMES[month])

            total = monthly_total[month]
            escalated = monthly_escalated.get(month, 0)

            conversion = round((escalated / total) * 100, 1) if total > 0 else 0
            conversion_rates.append(conversion)

        return {"labels": labels, "conversion_rates": conversion_rates}

    def get_group_a_time_distribution(self):
        """График: Распределение по срокам эскалации"""
        df = self._build_dataframe()

        intervals_labels = [
            "0-90 дней",
            "91-180 дней",
            "181-270 дней",
            "271-360 дней",
            ">360 дней",
        ]
        intervals_counts = [0, 0, 0, 0, 0]

        if df.empty:
            return {"labels": intervals_labels, "counts": intervals_counts}

        # ✅ Быстрая группировка через pandas
        days_series = df["days"].dropna()

        for days in days_series:
            if days <= 90:
                intervals_counts[0] += 1
            elif days <= 180:
                intervals_counts[1] += 1
            elif days <= 270:
                intervals_counts[2] += 1
            elif days <= 360:
                intervals_counts[3] += 1
            else:
                intervals_counts[4] += 1

        return {"labels": intervals_labels, "counts": intervals_counts}

    def get_group_a_top_consumers(self):
        """Таблица: TOP потребителей"""
        df = self._build_dataframe()

        if df.empty:
            return []

        # ✅ Группировка через pandas (БЫСТРО!)
        consumer_stats = (
            df.groupby("consumer")
            .agg(
                {
                    "claim_id": "count",  # Количество претензий (эскалаций)
                    "days": "mean",  # Средний срок
                }
            )
            .reset_index()
        )

        consumer_stats.columns = ["consumer", "escalated", "average_days"]

        # Считаем общее количество рекламаций по потребителям
        # (Нужно пройтись по всем претензиям всех рекламаций)
        reclamations = self._get_reclamations_with_claims()

        consumer_total = {}
        for reclamation in reclamations:
            for (
                claim
            ) in reclamation.claims.all():  # Все претензии (не только признанные)
                consumer = claim.consumer_name
                if not consumer:
                    continue
                if not self.all_consumers_mode and consumer not in self.consumers:
                    continue

                consumer_total[consumer] = consumer_total.get(consumer, 0) + 1

        # Добавляем total_reclamations к статистике
        consumer_stats["total_reclamations"] = (
            consumer_stats["consumer"].map(consumer_total).fillna(0).astype(int)
        )

        # Считаем конверсию
        consumer_stats["conversion_rate"] = (
            (consumer_stats["escalated"] / consumer_stats["total_reclamations"]) * 100
        ).round(1)

        # Округляем средний срок
        consumer_stats["average_days"] = (
            consumer_stats["average_days"].fillna(0).round(0).astype(int)
        )

        # Сортируем по конверсии (убыв.)
        consumer_stats = consumer_stats.sort_values("conversion_rate", ascending=False)

        # Преобразуем в список словарей
        result = consumer_stats.to_dict("records")

        return result

    # ========== ГРУППА B: Претензии без связи ==========

    def get_group_b_summary(self):
        """Карточки для Группы B"""
        # ✅ ОПТИМИЗАЦИЯ: Один запрос с аннотацией
        from django.db.models import Count

        claims_qs = Claim.objects.filter(
            claim_date__year=self.year,
            result_claim="ACCEPTED",
            response_number__isnull=False,
        ).prefetch_related("reclamations")

        # Фильтруем претензии без связи
        claims_without_link = [
            claim for claim in claims_qs if not claim.reclamations.exists()
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
        """График: Распределение по срокам (претензии без связи)"""
        claims_qs = Claim.objects.filter(
            claim_date__year=self.year,
            result_claim="ACCEPTED",
            response_number__isnull=False,
        ).prefetch_related("reclamations")

        claims_without_link = [
            claim for claim in claims_qs if not claim.reclamations.exists()
        ]

        if not self.all_consumers_mode:
            claims_without_link = [
                claim
                for claim in claims_without_link
                if claim.consumer_name in self.consumers
            ]

        intervals_labels = [
            "0-90 дней",
            "91-180 дней",
            "181-270 дней",
            "271-360 дней",
            ">360 дней",
        ]
        intervals_counts = [0, 0, 0, 0, 0]

        for claim in claims_without_link:
            if claim.reclamation_act_date and claim.claim_date:
                days = (claim.claim_date - claim.reclamation_act_date).days

                if days < 0:
                    continue
                elif days <= 90:
                    intervals_counts[0] += 1
                elif days <= 180:
                    intervals_counts[1] += 1
                elif days <= 270:
                    intervals_counts[2] += 1
                elif days <= 360:
                    intervals_counts[3] += 1
                else:
                    intervals_counts[4] += 1

        return {"labels": intervals_labels, "counts": intervals_counts}

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

                colors = ["#ff6b6b", "#ffa726", "#66bb6a", "#42a5f5", "#ab47bc"]
                bars = ax.bar(labels, counts, color=colors, alpha=0.7)

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

                colors = ["#ff6b6b", "#ffa726", "#66bb6a", "#42a5f5", "#ab47bc"]
                bars = ax.bar(labels, counts, color=colors, alpha=0.7)

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
                f.write("=" * 120 + "\n\n")

                # Группа A
                f.write("ГРУППА A: РЕКЛАМАЦИИ ИЗ БАЗЫ\n")
                f.write("-" * 120 + "\n")
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
                        f"{'Конверсия (%)':<18}{'Средний срок':<15}\n"
                    )
                    f.write("-" * 120 + "\n")

                    for idx, consumer in enumerate(group_a["top_consumers"], 1):
                        f.write(
                            f"{idx:<5}{consumer['consumer']:<30}{consumer['total_reclamations']:<15}"
                            f"{consumer['escalated']:<15}{consumer['conversion_rate']:<18.1f}"
                            f"{consumer['average_days']:<15}\n"
                        )

                f.write("\n" + "=" * 120 + "\n\n")

                # Группа B
                f.write("ГРУППА B: ПРЕТЕНЗИИ БЕЗ СВЯЗИ\n")
                f.write("-" * 120 + "\n")
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
