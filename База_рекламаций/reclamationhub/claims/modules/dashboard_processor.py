# claims/modules/dashboard_processor.py

from reports.config.paths import (
    get_claims_dashboard_chart_path,
    get_claims_dashboard_table_path,
    BASE_REPORTS_DIR,
)
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from datetime import date
from decimal import Decimal

from claims.models import Claim


class DashboardProcessor:
    """Обработка данных для Dashboard претензий"""

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

    def __init__(self, year=None, exchange_rate=None):
        self.today = date.today()
        self.year = year or self.today.year  # год анализа (по умолчанию текущий)
        self.exchange_rate = exchange_rate or Decimal("0.035")  # курс RUR → BYN

    def _convert_to_byn(self, amount, currency):
        """Конвертация суммы в BYN (currency: 'RUR' или 'BYN')"""
        if not amount:
            return Decimal("0.00")

        amount_decimal = Decimal(str(amount))

        if currency == "BYN":
            return amount_decimal
        elif currency == "RUR":
            return amount_decimal * self.exchange_rate
        else:
            return Decimal("0.00")

    def _get_unique_claims_df(self):
        """Получение DataFrame с УНИКАЛЬНЫМИ претензиями (группировка по claim_number)"""
        # Получаем все записи за год
        claims = Claim.objects.filter(claim_date__year=self.year).values(
            "claim_number",
            "claim_date",
            "claim_amount_all",
            "costs_all",
            "type_money",
            "consumer_name",
        )

        if not claims.exists():
            return pd.DataFrame()

        # Создаем DataFrame
        df = pd.DataFrame(list(claims))

        # Группируем по claim_number и берем первую запись
        # (т.к. все строки одной претензии имеют одинаковые суммы)
        df_unique = df.groupby("claim_number").first().reset_index()

        return df_unique

    def get_summary_cards(self):
        """Данные для карточек на странице Dashboard претензий
        Возвращает:
        {
            "total_claims": 47,
            "total_acts": 217,
            "total_amount_byn": "125000.00",
            "total_costs_byn": "87500.00",
            "acceptance_percent": 70.0
        }
        """
        # Получаем DataFrame с уникальными претензиями
        df = self._get_unique_claims_df()

        if df.empty:
            return {
                "total_claims": 0,
                "total_acts": 0,
                "total_amount_byn": "0.00",
                "total_costs_byn": "0.00",
                "acceptance_percent": 0,
            }

        # Количество УНИКАЛЬНЫХ претензий
        total_claims = len(df)

        # Количество ВСЕГО строк (актов)
        total_acts = Claim.objects.filter(claim_date__year=self.year).count()

        # Конвертируем суммы в BYN
        total_amount_byn = Decimal("0.00")
        total_costs_byn = Decimal("0.00")

        for _, row in df.iterrows():
            currency = row["type_money"] or "BYN"

            # Общая выставленная сумма
            if row["claim_amount_all"]:
                total_amount_byn += self._convert_to_byn(
                    row["claim_amount_all"], currency
                )

            # Общая признанная сумма
            if row["costs_all"]:
                total_costs_byn += self._convert_to_byn(row["costs_all"], currency)

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

    def get_monthly_dynamics(self):
        """Данные для графика динамики по месяцам
        Возвращает:
        {
            "labels": ["Январь", "Февраль", ...],
            "amounts": [12500.50, 18900.00, ...],
            "costs": [8750.35, 13230.00, ...]
        }
        """
        # Получаем DataFrame с уникальными претензиями
        df = self._get_unique_claims_df()

        if df.empty:
            return {"labels": [], "amounts": [], "costs": []}

        # Преобразуем claim_date в datetime
        df["claim_date"] = pd.to_datetime(df["claim_date"])

        # Группируем по месяцам
        monthly_data = {}

        for _, row in df.iterrows():
            month = row["claim_date"].month
            currency = row["type_money"] or "BYN"

            if month not in monthly_data:
                monthly_data[month] = {
                    "amount": Decimal("0.00"),
                    "cost": Decimal("0.00"),
                }

            # Общая выставленная сумма
            if row["claim_amount_all"]:
                monthly_data[month]["amount"] += self._convert_to_byn(
                    row["claim_amount_all"], currency
                )

            # Общая признанная сумма
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

    def get_top_consumers(self):  # def get_top_consumers(self, limit=5):
        """TOP потребителей по суммам претензий
        Возвращает:
        [
            {
                "consumer": "ЯМЗ",
                "amount": "45000.00",
                "costs": "31500.00",
                "acceptance_percent": 70.0,
                "count": 12
            },
            ...
        ]
        """
        # Получаем DataFrame с уникальными претензиями
        df = self._get_unique_claims_df()

        if df.empty:
            return []

        # Исключаем записи без потребителя
        df = df[df["consumer_name"].notna() & (df["consumer_name"] != "")]

        if df.empty:
            return []

        # Группируем по потребителям
        consumer_data = {}

        for _, row in df.iterrows():
            consumer = row["consumer_name"]
            currency = row["type_money"] or "BYN"

            if consumer not in consumer_data:
                consumer_data[consumer] = {
                    "amount": Decimal("0.00"),
                    "costs": Decimal("0.00"),
                    "count": 0,
                }

            # Общая выставленная сумма
            if row["claim_amount_all"]:
                consumer_data[consumer]["amount"] += self._convert_to_byn(
                    row["claim_amount_all"], currency
                )

            # Общая признанная сумма
            if row["costs_all"]:
                consumer_data[consumer]["costs"] += self._convert_to_byn(
                    row["costs_all"], currency
                )

            consumer_data[consumer]["count"] += 1

        # Сортируем по сумме (по убыванию)
        sorted_consumers = sorted(
            consumer_data.items(), key=lambda x: x[1]["amount"], reverse=True
        )  # [:limit]  # если нужен ТОП-5 добавить в функциии limit=5 и [:limit]

        # Формируем результат
        result = []
        for consumer, data in sorted_consumers:
            # Процент признания
            acceptance_percent = 0
            if data["amount"] > 0:
                acceptance_percent = round((data["costs"] / data["amount"]) * 100, 1)

            result.append(
                {
                    "consumer": consumer,
                    "amount": f"{data['amount']:.2f}",
                    "costs": f"{data['costs']:.2f}",
                    "acceptance_percent": acceptance_percent,
                    "count": data["count"],
                }
            )

        return result

    def generate_dashboard(self):
        """Главный метод генерации Dashboard"""
        try:
            # Получаем все данные
            summary_cards = self.get_summary_cards()
            monthly_dynamics = self.get_monthly_dynamics()
            top_consumers = self.get_top_consumers()

            return {
                "success": True,
                "year": self.year,
                "exchange_rate": str(self.exchange_rate),
                "summary_cards": summary_cards,
                "monthly_dynamics": monthly_dynamics,
                "top_consumers": top_consumers,
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Ошибка при генерации Dashboard: {str(e)}",
            }

    def save_to_files(self):
        """Сохранение графика и таблицы Dashboard в файлы"""
        try:
            # Получаем данные для сохранения
            summary_cards = self.get_summary_cards()
            monthly_dynamics = self.get_monthly_dynamics()
            top_consumers = self.get_top_consumers()

            # 1. Сохраняем график
            chart_path = get_claims_dashboard_chart_path(self.year)

            if monthly_dynamics["labels"]:
                plt.figure(figsize=(12, 6))

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

                plt.title(
                    f"Динамика претензий за {self.year} год (BYN)",
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
            table_path = get_claims_dashboard_table_path(self.year)

            with open(table_path, "w", encoding="utf-8") as f:
                f.write(f"TOP ПОТРЕБИТЕЛЕЙ ПО СУММАМ ПРЕТЕНЗИЙ ЗА {self.year} ГОД\n")
                f.write(f"Курс: 1 RUR = {self.exchange_rate} BYN\n")
                f.write("=" * 100 + "\n\n")

                # Заголовок таблицы
                f.write(
                    f"{'№':<5}{'Потребитель':<30}{'Претензий':<15}"
                    f"{'Выставлено':<20}{'Признано':<20}{'%':<10}\n"
                )
                f.write("-" * 100 + "\n")

                # Данные
                for idx, consumer in enumerate(top_consumers, 1):
                    f.write(
                        f"{idx:<5}"
                        f"{consumer['consumer']:<30}"
                        f"{consumer['count']:<15}"
                        f"{consumer['amount']:<20}"
                        f"{consumer['costs']:<20}"
                        f"{consumer['acceptance_percent']:<10}\n"
                    )

                f.write("\n" + "=" * 100 + "\n")
                f.write(f"Всего претензий: {summary_cards['total_claims']}\n")
                f.write(f"Выставлено: {summary_cards['total_amount_byn']} BYN\n")
                f.write(f"Признано: {summary_cards['total_costs_byn']} BYN\n")

            return {
                "success": True,
                "chart_path": chart_path,
                "table_path": table_path,
                "base_dir": BASE_REPORTS_DIR,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}
