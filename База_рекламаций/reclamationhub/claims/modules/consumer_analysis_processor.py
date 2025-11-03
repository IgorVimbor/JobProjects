# claims/modules/consumer_analysis_processor.py
"""Процессор для анализа претензий по конкретному потребителю"""

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

    def __init__(self, year=None, consumer=None, exchange_rate=None):
        """
        year: год анализа
        consumer: название потребителя
        exchange_rate: курс RUR → BYN
        """
        self.today = date.today()
        self.year = year or self.today.year
        self.consumer = consumer
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

    def _get_unique_claims_df(self):
        """Получение DataFrame с уникальными претензиями по потребителю"""
        # Получаем все записи за год для выбранного потребителя
        claims = Claim.objects.filter(
            claim_date__year=self.year, consumer_name=self.consumer
        ).values(
            "claim_number", "claim_date", "claim_amount_all", "costs_all", "type_money"
        )

        if not claims.exists():
            return pd.DataFrame()

        # Создаем DataFrame
        df = pd.DataFrame(list(claims))

        # Группируем по claim_number и берем первую запись
        df_unique = df.groupby("claim_number").first().reset_index()

        return df_unique

    def get_summary_data(self):
        """Сводная информация по потребителю"""
        df = self._get_unique_claims_df()

        if df.empty:
            return {
                "total_claims": 0,
                "total_amount_byn": "0.00",
                "total_costs_byn": "0.00",
                "acceptance_percent": 0,
            }

        total_claims = len(df)
        total_amount_byn = Decimal("0.00")
        total_costs_byn = Decimal("0.00")

        for _, row in df.iterrows():
            currency = row["type_money"] or "BYN"

            if row["claim_amount_all"]:
                total_amount_byn += self._convert_to_byn(
                    row["claim_amount_all"], currency
                )

            if row["costs_all"]:
                total_costs_byn += self._convert_to_byn(row["costs_all"], currency)

        # Процент признания
        acceptance_percent = 0
        if total_amount_byn > 0:
            acceptance_percent = round((total_costs_byn / total_amount_byn) * 100, 1)

        return {
            "total_claims": total_claims,
            "total_amount_byn": f"{total_amount_byn:.2f}",
            "total_costs_byn": f"{total_costs_byn:.2f}",
            "acceptance_percent": acceptance_percent,
        }

    def get_monthly_dynamics(self):
        """Динамика по месяцам для потребителя"""
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

    def generate_analysis(self):
        """Главный метод генерации анализа"""
        try:
            summary_data = self.get_summary_data()
            monthly_dynamics = self.get_monthly_dynamics()

            return {
                "success": True,
                "year": self.year,
                "consumer": self.consumer,
                "exchange_rate": str(self.exchange_rate),
                "summary_data": summary_data,
                "monthly_dynamics": monthly_dynamics,
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Ошибка при генерации анализа: {str(e)}",
            }

    def save_to_files(self):
        """Сохранение графика и таблицы анализа потребителя в файлы"""
        try:
            # Получаем данные для сохранения
            analysis_data = self.generate_analysis()

            if not analysis_data["success"]:
                return {
                    "success": False,
                    "error": "Не удалось сгенерировать данные для сохранения",
                }

            # 1. Сохраняем график
            chart_path = get_consumer_analysis_chart_path(self.year, self.consumer)

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
                    f"Динамика претензий по потребителю '{self.consumer}' за {self.year} год (BYN)",
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

            # 2. Сохраняем таблицу по месяцам
            table_path = get_consumer_analysis_table_path(self.year, self.consumer)

            with open(table_path, "w", encoding="utf-8") as f:
                f.write(
                    f"АНАЛИЗ ПРЕТЕНЗИЙ ПО ПОТРЕБИТЕЛЮ '{self.consumer}' ЗА {self.year} ГОД\n"
                )
                f.write(f"Курс: 1 RUR = {self.exchange_rate} BYN\n")
                f.write("=" * 80 + "\n\n")

                # Таблица по месяцам - используем данные из monthly_dynamics
                f.write(
                    f"{'Месяц':<15}{'Выставлено (BYN)':<20}{'Признано (BYN)':<20}\n"
                )
                f.write("-" * 55 + "\n")

                monthly_dynamics = analysis_data["monthly_dynamics"]
                total_amount = 0
                total_costs = 0

                for month, amount, cost in zip(
                    monthly_dynamics["labels"],
                    monthly_dynamics["amounts"],
                    monthly_dynamics["costs"],
                ):
                    f.write(f"{month:<15}{amount:<20.2f}{cost:<20.2f}\n")
                    total_amount += amount
                    total_costs += cost

                f.write("\n" + "=" * 55 + "\n")
                f.write(f"ИТОГО:\n")
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

            return {
                "success": True,
                "base_dir": BASE_REPORTS_DIR,
                "chart_path": chart_path,
                "table_path": table_path,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}
