# claims/modules/reclamation_to_claim_processor.py
"""
Процессор для анализа конверсии рекламация → претензия

Включает класс:
- `ReclamationToClaimProcessor` - Анализ связи рекламация → претензия
"""

from datetime import date
from decimal import Decimal
from django.db.models import Prefetch
from django.db.models import Q

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

        # Кэш для выборок
        self._group_a_claims_cache = None
        self._group_b_claims_cache = None
        self._reclamations_cache = None

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

    def _extract_consumer_prefix(self, consumer_name):
        """Извлечение префикса потребителя ("ПАЗ - АСП" → "ПАЗ")"""
        return Claim.extract_consumer_prefix(consumer_name)

    def _consumer_matches_filter(self, consumer_name):
        """Проверка, соответствует ли потребитель фильтру
        Учитывает префиксы:
        Фильтр: "ПАЗ"
        Потребитель: "ПАЗ - АСП" → True
        Потребитель: "ПАЗ - эксплуатация" → True
        Потребитель: "ЯМЗ" → False
        """
        if self.all_consumers_mode:
            return True

        consumer_prefix = self._extract_consumer_prefix(consumer_name)

        # Проверяем точное совпадение
        if consumer_name in self.consumers:
            return True

        # Проверяем совпадение префикса
        for filter_consumer in self.consumers:
            filter_prefix = self._extract_consumer_prefix(filter_consumer)
            if consumer_prefix == filter_prefix:
                return True

        return False

    def _get_base_claims_data(self):
        """Фильтрация на SQL уровне"""
        if (
            self._group_a_claims_cache is not None
            and self._group_b_claims_cache is not None
        ):
            return self._group_a_claims_cache, self._group_b_claims_cache

        # Формируем SQL фильтр по потребителям
        consumer_filter = Q()
        if not self.all_consumers_mode:
            for consumer in self.consumers:
                consumer_filter |= Q(consumer_name__istartswith=consumer)

        reclamations_prefetch = Prefetch(
            "reclamations",
            queryset=Reclamation.objects.filter(year=self.year).only(  # Фильтр по году!
                "id",
                "year",
                "consumer_act_date",
                "end_consumer_act_date",
                "message_received_date",
            ),
        )

        # Группа А: претензии со связанными рекламациями + фильтр потребителей
        group_a_filter = Q(result_claim="ACCEPTED", reclamations__isnull=False)
        if not self.all_consumers_mode:
            group_a_filter &= consumer_filter

        self._group_a_claims_cache = (
            Claim.objects.filter(group_a_filter)
            .prefetch_related(reclamations_prefetch)
            .distinct()
        )

        # Группа Б: претензии без связей за выбранный год + фильтр потребителей
        group_b_filter = Q(
            result_claim="ACCEPTED",
            claim_date__year=self.year,
            reclamations__isnull=True,
        )
        if not self.all_consumers_mode:
            group_b_filter &= consumer_filter

        self._group_b_claims_cache = Claim.objects.filter(group_b_filter)

        return self._group_a_claims_cache, self._group_b_claims_cache

    # Убираем методы фильтрации Python!
    def _get_filtered_group_a_claims(self):
        """Теперь данные уже отфильтрованы на SQL уровне"""
        group_a_claims, _ = self._get_base_claims_data()
        return list(group_a_claims)  # Просто возвращаем как есть

    def _get_filtered_group_b_claims(self):
        """Теперь данные уже отфильтрованы на SQL уровне"""
        _, group_b_claims = self._get_base_claims_data()
        return list(group_b_claims)

    def _get_filtered_reclamations(self):
        """Единый метод получения рекламаций с кэшированием"""
        if self._reclamations_cache is not None:
            return self._reclamations_cache

        if not self.all_consumers_mode:
            q_filters = Q()
            for consumer in self.consumers:
                q_filters |= Q(defect_period__name__istartswith=consumer)

            self._reclamations_cache = (
                Reclamation.objects.filter(q_filters)
                .filter(year=self.year)
                .only(
                    "id",
                    "year",
                    "message_received_date",
                    "consumer_act_date",
                    "end_consumer_act_date",
                    "defect_period__name",
                )
                .select_related("defect_period")
            )
        else:
            self._reclamations_cache = (
                Reclamation.objects.filter(year=self.year)
                .only(
                    "id",
                    "year",
                    "message_received_date",
                    "consumer_act_date",
                    "end_consumer_act_date",
                    "defect_period__name",
                )
                .select_related("defect_period")
            )

        return self._reclamations_cache

    def _count_reclamations_by_consumer(self):
        """Подсчет рекламаций по потребителям (фильтрация на уровне БД)"""

        reclamations_all = self._get_filtered_reclamations()  # используем кэш

        consumer_reclamation_count = {}

        for reclamation in reclamations_all:
            # Получаем имя потребителя из defect_period
            if not reclamation.defect_period or not reclamation.defect_period.name:
                continue

            period_name = reclamation.defect_period.name
            consumer_prefix = self._extract_consumer_prefix(period_name)

            consumer_reclamation_count[consumer_prefix] = (
                consumer_reclamation_count.get(consumer_prefix, 0) + 1
            )

        return consumer_reclamation_count

        # ========== ГРУППА A: Претензии со связанными рекламациями ==========

    def get_group_a_summary(self):
        """Карточки для Группы A (учитывает фильтр по потребителям)"""
        # Считаем рекламации с учетом фильтра по потребителям
        consumer_reclamation_count = self._count_reclamations_by_consumer()

        # Общее количество рекламаций (с учетом фильтра)
        total_reclamations = sum(consumer_reclamation_count.values())

        if total_reclamations == 0:
            return {
                "total_reclamations": 0,
                "escalated_reclamations": 0,
                "escalation_rate": 0,
                "average_days": 0,
                "claim_amount_byn": "0.00",
            }

        # Получаем отфильтрованные претензии Группы А
        filtered_claims = self._get_filtered_group_a_claims()

        if not filtered_claims:
            # Есть рекламации, но нет претензий
            return {
                "total_reclamations": total_reclamations,
                "escalated_reclamations": 0,
                "escalation_rate": 0,
                "average_days": 0,
                "claim_amount_byn": "0.00",
            }

        # Считаем уникальные рекламации и прочую статистику
        unique_reclamations = set()
        total_claim_amount = Decimal("0.00")
        days_list = []

        for claim in filtered_claims:
            # Собираем уникальные рекламации
            for reclamation in claim.reclamations.all():
                unique_reclamations.add(reclamation.id)

            # Сумма претензии
            if claim.costs_act:
                total_claim_amount += self._convert_to_byn(
                    claim.costs_act, claim.type_money
                )

            # Срок эскалации (берем первую связанную рекламацию)
            first_rec = claim.reclamations.first()
            if first_rec:
                rec_date = self._get_reclamation_date(
                    first_rec.consumer_act_date, first_rec.end_consumer_act_date
                )
                if rec_date and claim.claim_date:
                    days = (claim.claim_date - rec_date).days
                    if days >= 0:
                        days_list.append(days)

        escalated_count = len(unique_reclamations)

        # Средний срок и конверсия
        average_days = round(sum(days_list) / len(days_list)) if days_list else 0
        escalation_rate = round((escalated_count / total_reclamations) * 100, 1)

        return {
            "total_reclamations": total_reclamations,
            "escalated_reclamations": escalated_count,
            "escalation_rate": escalation_rate,
            "average_days": average_days,
            "claim_amount_byn": f"{total_claim_amount:.2f}",
        }

    def get_group_a_monthly_conversion(self):
        """График динамики конверсии по месяцам (учитывает фильтр по потребителям)"""
        # Считаем рекламации с учетом фильтра
        consumer_reclamation_count = self._count_reclamations_by_consumer()

        if not consumer_reclamation_count:
            return {"labels": [], "conversion_rates": []}

        # Получаем рекламации для месячного анализа
        reclamations_all = self._get_filtered_reclamations()  # используем кэш

        # Получаем отфильтрованные претензии Группы А
        filtered_claims = self._get_filtered_group_a_claims()

        # Считаем количество рекламаций по месяцам
        monthly_total = {}
        for reclamation in reclamations_all:
            if reclamation.message_received_date:
                month = reclamation.message_received_date.month
                monthly_total[month] = monthly_total.get(month, 0) + 1

        if not monthly_total:
            return {"labels": [], "conversion_rates": []}

        # Считаем эскалации по месяцам
        monthly_escalated = {}
        for claim in filtered_claims:
            for reclamation in claim.reclamations.all():
                if reclamation.message_received_date:
                    month = reclamation.message_received_date.month
                    if month not in monthly_escalated:
                        monthly_escalated[month] = set()
                    monthly_escalated[month].add(reclamation.id)

        # Преобразуем sets в counts
        monthly_escalated_counts = {
            month: len(rec_set) for month, rec_set in monthly_escalated.items()
        }

        # Формируем данные для графика
        labels = []
        conversion_rates = []

        for month in sorted(monthly_total.keys()):
            labels.append(self.MONTH_NAMES[month])

            total = monthly_total[month]
            escalated = monthly_escalated_counts.get(month, 0)

            conversion = round((escalated / total) * 100, 1) if total > 0 else 0
            conversion_rates.append(conversion)

        return {"labels": labels, "conversion_rates": conversion_rates}

    def get_group_a_time_distribution(self):
        """График: Распределение по срокам эскалации"""
        filtered_claims = self._get_filtered_group_a_claims()

        intervals_labels = [
            "0-90 дней",
            "91-180 дней",
            "181-270 дней",
            "271-360 дней",
            ">360 дней",
        ]
        intervals_counts = [0, 0, 0, 0, 0]

        for claim in filtered_claims:
            # Берем первую связанную рекламацию
            first_rec = claim.reclamations.first()
            if first_rec:
                rec_date = self._get_reclamation_date(
                    first_rec.consumer_act_date, first_rec.end_consumer_act_date
                )

                if rec_date and claim.claim_date:
                    days = (claim.claim_date - rec_date).days

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

    def get_group_a_top_consumers(self):
        """Таблица TOP потребителей"""
        filtered_claims = self._get_filtered_group_a_claims()

        if not filtered_claims:
            return []

        # Сбор статистики по потребителям
        consumer_stats = {}

        for claim in filtered_claims:
            consumer = claim.consumer_name
            consumer_prefix = self._extract_consumer_prefix(consumer)

            if consumer_prefix not in consumer_stats:
                consumer_stats[consumer_prefix] = {
                    "escalated_reclamations": set(),
                    "days_list": [],
                }

            # Добавляем уникальные рекламации
            for reclamation in claim.reclamations.all():
                consumer_stats[consumer_prefix]["escalated_reclamations"].add(
                    reclamation.id
                )

            # Добавляем дни (берем первую рекламацию)
            first_rec = claim.reclamations.first()
            if first_rec:
                rec_date = self._get_reclamation_date(
                    first_rec.consumer_act_date, first_rec.end_consumer_act_date
                )
                if rec_date and claim.claim_date:
                    days = (claim.claim_date - rec_date).days
                    if days >= 0:
                        consumer_stats[consumer_prefix]["days_list"].append(days)

        # Используем общий метод для подсчета ВСЕХ рекламаций
        consumer_reclamation_count = self._count_reclamations_by_consumer()

        # Формируем итоговую таблицу
        result = []
        for consumer, stats in consumer_stats.items():
            escalated = len(stats["escalated_reclamations"])
            total = consumer_reclamation_count.get(consumer, 0)
            average_days = (
                round(sum(stats["days_list"]) / len(stats["days_list"]))
                if stats["days_list"]
                else 0
            )
            conversion_rate = round((escalated / total) * 100, 1) if total > 0 else 0

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

        # ========== ГРУППА B: Претензии без связанных рекламаций ==========

    def get_group_b_summary(self):
        """Карточки для Группы B"""
        filtered_claims = self._get_filtered_group_b_claims()

        # Общее количество претензий без связи
        total_claims = len(filtered_claims)

        # Количество претензий без даты рекламации
        claims_without_date = sum(
            1 for claim in filtered_claims if not claim.reclamation_act_date
        )

        # Общая сумма в BYN по претензиям Группы В
        total_amount_byn = Decimal("0.00")
        for claim in filtered_claims:
            if claim.costs_act:
                total_amount_byn += self._convert_to_byn(
                    claim.costs_act, claim.type_money
                )

        return {
            "claims_without_link": total_claims,
            "claims_without_date": claims_without_date,
            "total_amount_byn": f"{total_amount_byn:.2f}",
        }

    def get_group_b_time_distribution(self):
        """График: Распределение по срокам (претензии без связи)"""
        filtered_claims = self._get_filtered_group_b_claims()

        intervals_labels = [
            "0-90 дней",
            "91-180 дней",
            "181-270 дней",
            "271-360 дней",
            ">360 дней",
        ]
        intervals_counts = [0, 0, 0, 0, 0]

        for claim in filtered_claims:
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

    # ========== Главный метод генерации анализа ==========

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

    # ============ Метод сохранения файлов  ====================

    def save_to_files(self, analysis_data=None):
        """Сохранение графиков и таблиц в файлы"""
        try:
            # Используем переданные данные или генерируем заново
            if analysis_data is None:
                analysis_data = self.generate_analysis()

            if not analysis_data["success"]:
                return {"success": False, "error": "Не удалось сгенерировать данные"}

            group_a = analysis_data["group_a"]
            group_b = analysis_data["group_b"]

            if self.all_consumers_mode:
                file_suffix = "все_потребители"
            elif len(self.consumers) == 1:
                file_suffix = self.consumers[0].replace(" ", "_").replace("-", "_")
            else:
                file_suffix = f"{len(self.consumers)}_потребителей"

            # График 1: Динамика конверсии
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

            # График 2: Распределение по срокам (Группа A)
            chart2_path = get_reclamation_to_claim_chart_path(
                self.year, f"{file_suffix}_сроки_A"
            )

            if sum(group_a["time_distribution"]["counts"]) > 0:
                fig, ax = plt.subplots(figsize=(10, 6))

                labels = group_a["time_distribution"]["labels"]
                counts = group_a["time_distribution"]["counts"]

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

            # График 3: Распределение по срокам (Группа B)
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

            # Таблица
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
