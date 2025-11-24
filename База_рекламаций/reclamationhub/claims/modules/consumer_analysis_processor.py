# claims/modules/consumer_analysis_processor.py
"""Процессор для анализа претензий по потребителям"""

import pandas as pd
from datetime import date
from decimal import Decimal

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from reports.config.paths import (
    get_consumer_analysis_chart_path,
    get_consumer_analysis_table_path,
    BASE_REPORTS_DIR,
)

from claims.models import Claim


class ConsumerAnalysisProcessor:
    """Анализ претензий по выбранному потребителю"""

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
        year: год анализа
        consumers: список потребителей (пустой список = все потребители)
        exchange_rate: курс RUR → BYN
        """
        self.today = date.today()
        self.year = year or self.today.year
        self.consumers = consumers or []  # список потребителей
        self.all_consumers_mode = len(self.consumers) == 0  # режим "все"
        self.exchange_rate = exchange_rate or Decimal("0.03")
        self.df = pd.DataFrame()  # общий DataFrame

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

    def _get_unique_claims_df(self, specific_consumer=None):
        """Получение DataFrame с уникальными претензиями"""
        # Базовый фильтр по году
        queryset_filter = {"claim_date__year": self.year}

        # Фильтр по потребителям
        if specific_consumer:
            # Для конкретного потребителя
            queryset_filter["consumer_name"] = specific_consumer
        elif not self.all_consumers_mode:
            # Для выбранных потребителей
            queryset_filter["consumer_name__in"] = self.consumers
        # Если all_consumers_mode=True, то фильтр по потребителям не добавляем

        # Получаем все записи
        claims = Claim.objects.filter(**queryset_filter).values(
            "claim_number",
            "claim_date",
            "claim_amount_all",
            "claim_amount_act",
            "costs_act",
            "costs_all",
            "type_money",
            "consumer_name",
        )

        if not claims.exists():
            return pd.DataFrame()

        # Создаем общий DataFrame из полученных записей
        self.df = pd.DataFrame(list(claims))

        # Группируем по claim_number и берем первую запись
        # df_unique = df.groupby("claim_number").first().reset_index()

        # Из общего датафрейма убираем дублирование претензий, т.к. суммы дублируются
        df_unique = self.df.drop_duplicates(subset="claim_number")

        return df_unique

    def get_summary_data(self):
        """Сводная информация по потребителю/потребителям"""

        # Датафрейм по уникальным номерам претензий
        df_unique = self._get_unique_claims_df()

        if df_unique.empty:
            return {
                "total_claims": 0,
                "total_acts": 0,
                "total_amount_byn": "0.00",
                "total_costs_byn": "0.00",
                "acceptance_percent": 0,
            }

        # Количество УНИКАЛЬНЫХ претензий
        total_claims = len(df_unique)

        # Количество ВСЕГО строк (актов) с учетом фильтрации по потребителям
        queryset_filter = {"claim_date__year": self.year}

        # Применяем ту же логику фильтрации, что и в _get_unique_claims_df
        if not self.all_consumers_mode:
            # Для выбранных потребителей
            queryset_filter["consumer_name__in"] = self.consumers
        # Если all_consumers_mode=True, то фильтр по потребителям не добавляем

        total_acts = Claim.objects.filter(**queryset_filter).count()

        # Подсчет сумм (считаем по актам рекламаций)
        total_amount_byn = self.df.apply(
            lambda row: self._convert_to_byn(
                row["claim_amount_act"], row["type_money"]
            ),
            axis=1,
        ).sum()

        total_costs_byn = self.df.apply(
            lambda row: self._convert_to_byn(row["costs_act"], row["type_money"]),
            axis=1,
        ).sum()

        # Процент признания
        acceptance_percent = 0
        if total_amount_byn > 0:
            acceptance_percent = round((total_costs_byn / total_amount_byn) * 100, 1)

        return {
            "total_claims": total_claims,
            "total_acts": total_acts,
            "total_amount_byn": f"{total_amount_byn:.2f}",
            "total_costs_byn": f"{total_costs_byn:.2f}",
            "acceptance_percent": acceptance_percent,
        }

    def get_consumers_monthly_table(self):
        """Генерация таблицы: потребители → месяцы с группировкой по строкам"""

        # Определяем список потребителей для анализа
        if self.all_consumers_mode:
            # Получаем всех потребителей из базы
            all_consumers = list(
                Claim.objects.filter(claim_date__year=self.year)
                .exclude(consumer_name__isnull=True)
                .exclude(consumer_name="")
                .values_list("consumer_name", flat=True)
                .distinct()
                .order_by("consumer_name")
            )
            consumers_to_analyze = all_consumers
        else:
            # Используем выбранных потребителей
            consumers_to_analyze = self.consumers

        if not consumers_to_analyze:
            return {
                "consumers": [],
                "totals": [],
                "month_names": list(self.MONTH_NAMES.values()),
                "has_data": False,
            }

        # Инициализируем структуру данных
        consumers_data = []
        totals_count = [0] * 12  # Количество по месяцам
        totals_amount = [Decimal("0.00")] * 12  # Выставлено по месяцам
        totals_costs = [Decimal("0.00")] * 12  # Признано по месяцам

        # Обрабатываем каждого потребителя
        for consumer in consumers_to_analyze:
            consumer_data = self._process_consumer_monthly_data(consumer)
            consumers_data.append(consumer_data)

            # Добавляем к итогам
            for month_idx in range(12):
                totals_count[month_idx] += consumer_data["rows"][0]["months"][month_idx]
                totals_amount[month_idx] += consumer_data["rows"][1]["months"][
                    month_idx
                ]
                totals_costs[month_idx] += consumer_data["rows"][2]["months"][month_idx]

        # Конвертируем в float только для шаблона
        def convert_row_to_float(row_data):
            return {
                "type": row_data["type"],
                "months": [
                    float(val) if isinstance(val, Decimal) else val
                    for val in row_data["months"]
                ],
            }

        # Конвертируем данные потребителей
        for consumer_data in consumers_data:
            consumer_data["rows"] = [
                convert_row_to_float(row) for row in consumer_data["rows"]
            ]

        # Формируем итоговые строки
        totals_data = [
            {"type": "Количество", "months": totals_count},
            {
                "type": "Выставлено",
                "months": [float(amount) for amount in totals_amount],
            },
            {"type": "Признано", "months": [float(costs) for costs in totals_costs]},
        ]

        return {
            "consumers": consumers_data,
            "totals": totals_data,
            "month_names": list(self.MONTH_NAMES.values()),
            "has_data": len(consumers_data) > 0,
        }

    def _process_consumer_monthly_data(self, consumer):
        """Обработка данных одного потребителя по месяцам для таблицы"""
        # Получаем данные конкретного потребителя
        df = self._get_unique_claims_df(specific_consumer=consumer)

        # Инициализируем массивы для 12 месяцев
        monthly_count = [0] * 12
        monthly_amount = [Decimal("0.00")] * 12
        monthly_costs = [Decimal("0.00")] * 12

        if not df.empty:
            # Преобразуем claim_date в datetime
            df["claim_date"] = pd.to_datetime(df["claim_date"])

            # Обрабатываем каждую претензию
            for _, row in df.iterrows():
                month_idx = row["claim_date"].month - 1  # 0-11 для индексации массива
                currency = row["type_money"] or "BYN"

                # Количество
                monthly_count[month_idx] += 1

                # Выставленная сумма
                if row["claim_amount_all"]:
                    monthly_amount[month_idx] += self._convert_to_byn(
                        row["claim_amount_all"], currency
                    )

                # Признанная сумма
                if row["costs_all"]:
                    monthly_costs[month_idx] += self._convert_to_byn(
                        row["costs_all"], currency
                    )

        return {
            "name": consumer,
            "rows": [
                {"type": "Количество", "months": monthly_count},
                {"type": "Выставлено", "months": monthly_amount},
                {"type": "Признано", "months": monthly_costs},
            ],
        }

    def generate_analysis(self):
        """Главный метод генерации анализа"""
        try:
            summary_data = self.get_summary_data()
            monthly_table = self.get_consumers_monthly_table()  # НОВОЕ

            # Определяем какие данные возвращать для графиков
            if self.all_consumers_mode:
                # Для всех потребителей - график по итоговым данным
                monthly_dynamics = self._get_total_monthly_dynamics(monthly_table)
                consumer_display = "всех потребителей"
            elif len(self.consumers) == 1:
                # Для одного потребителя - детальная динамика
                monthly_dynamics = self.get_monthly_dynamics()
                consumer_display = self.consumers[0]
            else:
                # Для нескольких выбранных потребителей - суммарная динамика
                monthly_dynamics = self._get_total_monthly_dynamics(monthly_table)
                consumer_display = f"{len(self.consumers)} потребителей"

            return {
                "success": True,
                "year": self.year,
                "consumers": self.consumers,  # список потребителей
                "consumer_display": consumer_display,  # для отображения
                "all_consumers_mode": self.all_consumers_mode,
                "exchange_rate": str(self.exchange_rate),
                "summary_data": summary_data,
                "monthly_dynamics": monthly_dynamics,
                "monthly_table": monthly_table,  # данные таблицы
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Ошибка при генерации анализа: {str(e)}",
            }

    def _get_total_monthly_dynamics(self, monthly_table):
        """Формирует данные для графика из итоговых данных таблицы"""
        if not monthly_table["has_data"]:
            return {"labels": [], "amounts": [], "costs": []}

        labels = []
        amounts = []
        costs = []

        # Берем данные из итогов таблицы
        totals = monthly_table["totals"]
        amounts_row = totals[1]["months"]  # Выставлено
        costs_row = totals[2]["months"]  # Признано

        # Формируем данные только для месяцев с данными
        for month_idx, month_name in enumerate(monthly_table["month_names"]):
            if amounts_row[month_idx] > 0 or costs_row[month_idx] > 0:
                labels.append(month_name)
                amounts.append(amounts_row[month_idx])
                costs.append(costs_row[month_idx])

        return {"labels": labels, "amounts": amounts, "costs": costs}

    def get_monthly_dynamics(self):
        """Динамика по месяцам для одного потребителя"""
        # Адаптируем для работы с новой логикой
        if self.all_consumers_mode:
            df = self._get_unique_claims_df()
        elif len(self.consumers) == 1:
            df = self._get_unique_claims_df(specific_consumer=self.consumers[0])
        else:
            df = self._get_unique_claims_df()

        if df.empty:
            return {"labels": [], "amounts": [], "costs": []}

        # Остальная логика метода остается без изменений
        df["claim_date"] = pd.to_datetime(df["claim_date"])

        monthly_data = {}

        for _, row in df.iterrows():
            month = row["claim_date"].month
            currency = row["type_money"] or "BYN"

            if month not in monthly_data:
                monthly_data[month] = {
                    "amount": Decimal("0.00"),
                    "cost": Decimal("0.00"),
                }

            if row["claim_amount_all"]:
                monthly_data[month]["amount"] += self._convert_to_byn(
                    row["claim_amount_all"], currency
                )

            if row["costs_all"]:
                monthly_data[month]["cost"] += self._convert_to_byn(
                    row["costs_all"], currency
                )

        # Формируем данные для графика
        labels = []
        amounts = []
        costs = []

        for month in sorted(monthly_data.keys()):
            labels.append(self.MONTH_NAMES[month])
            amounts.append(float(monthly_data[month]["amount"]))
            costs.append(float(monthly_data[month]["cost"]))

        return {"labels": labels, "amounts": amounts, "costs": costs}

    # def save_to_files(self):
    def save_to_files(self, analysis_data=None):
        """Сохранение графика и таблицы анализа потребителя в файлы"""
        try:
            # Используем переданные данные или генерируем заново
            if analysis_data is None:
                analysis_data = self.generate_analysis()

            if not analysis_data["success"]:
                return {
                    "success": False,
                    "error": "Не удалось сгенерировать данные для сохранения",
                }

            # Определяем название файлов в зависимости от режима
            if self.all_consumers_mode:
                file_suffix = "все_потребители"
            elif len(self.consumers) == 1:
                file_suffix = self.consumers[0].replace(" ", "_").replace("-", "_")
            else:
                file_suffix = f"{len(self.consumers)}_потребителей"

            # 1. Сохраняем график
            chart_path = get_consumer_analysis_chart_path(self.year, file_suffix)

            monthly_dynamics = analysis_data["monthly_dynamics"]

            if monthly_dynamics["labels"]:
                plt.figure(figsize=(12, 6))

                # Линии графика
                plt.plot(
                    monthly_dynamics["labels"],
                    monthly_dynamics["amounts"],
                    marker="o",
                    label="Выставлено (BYN)",
                    color="orange",
                    linewidth=2,
                )
                plt.plot(
                    monthly_dynamics["labels"],
                    monthly_dynamics["costs"],
                    marker="o",
                    label="Признано (BYN)",
                    color="green",
                    linewidth=2,
                )

                # Добавляем подписи данных
                for i, (label, amount, cost) in enumerate(
                    zip(
                        monthly_dynamics["labels"],
                        monthly_dynamics["amounts"],
                        monthly_dynamics["costs"],
                    )
                ):
                    plt.annotate(
                        f"{amount:,.0f}".replace(",", "."),
                        (i, amount),
                        textcoords="offset points",
                        xytext=(0, 10),
                        ha="center",
                        fontsize=8,
                        bbox=dict(
                            boxstyle="round,pad=0.3", facecolor="white", alpha=0.7
                        ),
                        color="orange",
                        fontweight="bold",
                    )

                    plt.annotate(
                        f"{cost:,.0f}".replace(",", "."),
                        (i, cost),
                        textcoords="offset points",
                        xytext=(0, -15),
                        ha="center",
                        fontsize=8,
                        bbox=dict(
                            boxstyle="round,pad=0.3", facecolor="white", alpha=0.7
                        ),
                        color="green",
                        fontweight="bold",
                    )

                plt.title(
                    f"Динамика претензий {analysis_data['consumer_display']} за {self.year} год (BYN)",
                    fontsize=14,
                    fontweight="bold",
                )
                plt.xlabel("Месяц")
                plt.ylabel("Сумма (BYN)")
                plt.legend()
                plt.grid(True, alpha=0.3)
                plt.tight_layout()

                plt.savefig(chart_path, dpi=300, bbox_inches="tight")
                plt.close()

            # 2. Сохраняем таблицу
            table_path = get_consumer_analysis_table_path(self.year, file_suffix)

            with open(table_path, "w", encoding="utf-8") as f:
                f.write(
                    f"АНАЛИЗ ПРЕТЕНЗИЙ {analysis_data['consumer_display'].upper()} ЗА {self.year} ГОД\n"
                )
                f.write(f"Курс: 1 RUR = {self.exchange_rate} BYN\n")
                f.write("=" * 120 + "\n\n")

                # Сводная информация
                f.write("СВОДНАЯ ИНФОРМАЦИЯ:\n")
                f.write("-" * 50 + "\n")
                f.write(
                    f"Всего претензий: {analysis_data['summary_data']['total_claims']}\n"
                )
                f.write(
                    f"Выставлено: {analysis_data['summary_data']['total_amount_byn']} BYN\n"
                )
                f.write(
                    f"Признано: {analysis_data['summary_data']['total_costs_byn']} BYN\n"
                )
                f.write(
                    f"Процент признания: {analysis_data['summary_data']['acceptance_percent']}%\n"
                )
                f.write("\n" + "=" * 120 + "\n\n")

                # Детализированная таблица по месяцам
                monthly_table = analysis_data["monthly_table"]

                if monthly_table["has_data"]:
                    f.write("ДЕТАЛИЗАЦИЯ ПО МЕСЯЦАМ:\n")
                    f.write("-" * 50 + "\n\n")

                    # Заголовок таблицы
                    header = f"{'Потребитель':<20} {'Показатель':<12}"
                    for month_name in monthly_table["month_names"]:
                        header += f"{month_name:<10}"
                    f.write(header + "\n")
                    f.write("-" * len(header) + "\n")

                    # Данные по потребителям
                    for consumer_data in monthly_table["consumers"]:
                        for row_idx, row in enumerate(consumer_data["rows"]):
                            if row_idx == 0:
                                # Обрезаем длинные названия
                                consumer_name = consumer_data["name"][:19]
                            else:
                                consumer_name = ""

                            line = f"{consumer_name:<20} {row['type']:<12}"
                            for month_value in row["months"]:
                                if row["type"] == "Количество":
                                    value_str = (
                                        str(int(month_value))
                                        if month_value > 0
                                        else "-"
                                    )
                                else:
                                    value_str = (
                                        f"{month_value:.2f}" if month_value > 0 else "-"
                                    )
                                line += f"{value_str:<10}"
                            f.write(line + "\n")
                        f.write("\n")  # Пустая строка между потребителями

                    # Итоговые данные - только если больше одного потребителя
                    if len(monthly_table["consumers"]) > 1:
                        f.write("-" * len(header) + "\n")
                        for row_idx, row in enumerate(monthly_table["totals"]):
                            if row_idx == 0:
                                itogo_name = "ИТОГО"
                            else:
                                itogo_name = ""

                            line = f"{itogo_name:<20} {row['type']:<12}"
                            for month_value in row["months"]:
                                if row["type"] == "Количество":
                                    value_str = (
                                        str(int(month_value))
                                        if month_value > 0
                                        else "-"
                                    )
                                else:
                                    value_str = (
                                        f"{month_value:.2f}" if month_value > 0 else "-"
                                    )
                                line += f"{value_str:<10}"
                            f.write(line + "\n")

            return {
                "success": True,
                "base_dir": BASE_REPORTS_DIR,
                "chart_path": chart_path,
                "table_path": table_path,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}
