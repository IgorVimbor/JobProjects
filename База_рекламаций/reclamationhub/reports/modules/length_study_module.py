# reports/modules/length_study_module.py
# Модуль приложения "Длительность исследования" с логикой расчета статистики и построения графиков

import pandas as pd
import numpy as np
import matplotlib

matplotlib.use("Agg")  # Без GUI для веб
import matplotlib.pyplot as plt
import base64
from io import BytesIO
from datetime import date
import os
from django.db.models import Case, When, F
from investigations.models import Investigation
from reports.config.paths import BASE_REPORTS_DIR


class LengthStudyProcessor:
    """Анализ длительности исследований"""

    def __init__(self, year=None):
        self.today = date.today()
        # self.current_year = self.today.year
        self.year = year or self.today.year  # Добавили год
        self.result_df = pd.DataFrame()
        self.df = pd.DataFrame()
        self.df_asp = pd.DataFrame()
        self.df_gp = pd.DataFrame()

    def get_data_from_db(self):
        """Получение данных с логикой подстановки дат"""
        queryset = (
            Investigation.objects.filter(
                act_date__isnull=False,  # Есть дата исследования
                reclamation__year=self.year,  # Добавляем фильтр по году рекламации
            )
            .select_related("reclamation__defect_period")
            .annotate(
                # Логика подстановки даты поступления
                effective_received_date=Case(
                    # Если есть product_received_date - используем его
                    When(
                        reclamation__product_received_date__isnull=False,
                        then=F("reclamation__product_received_date"),
                    ),
                    # Иначе используем message_received_date
                    default=F("reclamation__message_received_date"),
                )
            )
            .values(
                "act_date",
                "effective_received_date",
                "reclamation__defect_period__name",
            )
        )

        if not queryset.exists():
            return None

        df = pd.DataFrame(list(queryset))

        # Переименовываем столбцы
        df.rename(
            columns={
                "act_date": "Дата исследования",
                "effective_received_date": "Дата поступления",
                "reclamation__defect_period__name": "Потребитель",
            },
            inplace=True,
        )

        # Убираем записи где effective_received_date пустое (подстраховка)
        df = df.dropna(subset=["Дата поступления"])

        return df

    def calculate_statistics(self):
        """Основная логика расчета статистики"""
        df = self.get_data_from_db()

        if df is None or df.empty:
            return False, "Нет данных для анализа"

        # Преобразуем в datetime если нужно
        df["Дата исследования"] = pd.to_datetime(df["Дата исследования"])
        df["Дата поступления"] = pd.to_datetime(df["Дата поступления"])

        # Рассчитываем разность в днях
        df["DIFF"] = (df["Дата исследования"] - df["Дата поступления"]).dt.days

        # Исключаем отрицательные значения если есть
        df = df[df["DIFF"] >= 0]

        if df.empty:
            return False, "Нет корректных данных для анализа"

        self.df = df.copy()

        # Группировка данных
        self.df_asp = df[df["Потребитель"].str.contains("АСП", na=False)]
        self.df_gp = df[df["Потребитель"].str.contains("эксплуатация", na=False)]

        # Расчет статистики
        df_mean = round(df["DIFF"].mean(), 2) if len(df) > 0 else 0
        df_median = round(df["DIFF"].median(), 2) if len(df) > 0 else 0

        asp_mean = round(self.df_asp["DIFF"].mean(), 2) if len(self.df_asp) > 0 else 0
        asp_median = (
            round(self.df_asp["DIFF"].median(), 2) if len(self.df_asp) > 0 else 0
        )

        gp_mean = round(self.df_gp["DIFF"].mean(), 2) if len(self.df_gp) > 0 else 0
        gp_median = round(self.df_gp["DIFF"].median(), 2) if len(self.df_gp) > 0 else 0

        # Результирующая таблица
        self.result_df = pd.DataFrame(
            [[df_mean, asp_mean, gp_mean], [df_median, asp_median, gp_median]],
            index=["Среднее значение (дней)", "Медианное значение (дней)"],
            columns=["В_целом", "Конвейер", "Эксплуатация"],
        )

        return True, f"Проанализировано записей: {len(df)}"

    def create_plots_base64(self):
        """Создание графиков в base64 для веб"""
        if self.df.empty:
            return None

        fig, axes = plt.subplots(1, 3, figsize=(12, 4))

        # Общая гистограмма
        if len(self.df) > 0:
            axes[0].hist(self.df["DIFF"], bins=20, color="skyblue", edgecolor="black")
            axes[0].set_title("Общая статистика")
            axes[0].set_xlim(-2, 40)
            axes[0].set_ylabel("Количество исследований")

        # Гистограмма АСП (Конвейер)
        if len(self.df_asp) > 0:
            axes[1].hist(
                self.df_asp["DIFF"], bins=20, color="salmon", edgecolor="black"
            )
            axes[1].set_title("Исследование по АСП")
            axes[1].set_xlim(-1, 40)
            axes[1].set_xlabel("Количество дней")

        # Гистограмма ГП (Эксплуатация)
        if len(self.df_gp) > 0:
            axes[2].hist(
                self.df_gp["DIFF"], bins=20, color="lightgreen", edgecolor="black"
            )
            axes[2].set_title("Исследование по ГП")
            axes[2].set_xlim(-1, 40)

        # Заголовок
        fig.suptitle(f"{self.year} год", fontsize=16)
        plt.tight_layout()

        # Конвертируем в base64
        buffer = BytesIO()
        plt.savefig(buffer, format="png", dpi=300, bbox_inches="tight")
        buffer.seek(0)
        plot_data = buffer.getvalue()
        buffer.close()
        plt.close(fig)

        plot_base64 = base64.b64encode(plot_data).decode("utf-8")
        return plot_base64

    def save_files(self):
        """Сохранение файлов на диск"""
        today_str = self.today.strftime("%d-%m-%Y")

        # TXT файл
        txt_path = os.path.join(
            BASE_REPORTS_DIR, f"Статистика длительности исследований_{today_str}.txt"
        )
        with open(txt_path, "w", encoding="utf-8") as f:
            print(
                f"\n\tСтатистика длительности исследований за {self.year} на {today_str}\n\n",
                file=f,
            )
            f.write(self.result_df.to_string())

        # PNG файл
        png_path = os.path.join(
            BASE_REPORTS_DIR, f"График длительности исследований_{today_str}.png"
        )

        # Пересоздаем график для сохранения
        fig, axes = plt.subplots(1, 3, figsize=(12, 4))

        if len(self.df) > 0:
            axes[0].hist(self.df["DIFF"], bins=20, color="skyblue", edgecolor="black")
            axes[0].set_title("Общая статистика")
            axes[0].set_xlim(-2, 40)
            axes[0].set_ylabel("Количество исследований")

        if len(self.df_asp) > 0:
            axes[1].hist(
                self.df_asp["DIFF"], bins=20, color="salmon", edgecolor="black"
            )
            axes[1].set_title("Исследование по АСП")
            axes[1].set_xlim(-1, 40)
            axes[1].set_xlabel("Количество дней")

        if len(self.df_gp) > 0:
            axes[2].hist(
                self.df_gp["DIFF"], bins=20, color="lightgreen", edgecolor="black"
            )
            axes[2].set_title("Исследование по ГП")
            axes[2].set_xlim(-1, 40)

        fig.suptitle(f"{self.year} год", fontsize=16)
        plt.tight_layout()
        plt.savefig(png_path, dpi=300, bbox_inches="tight")
        plt.close(fig)

        return txt_path, png_path

    def generate_report(self):
        """Главный метод генерации отчета"""
        try:
            success, message = self.calculate_statistics()

            if not success:
                return {"success": False, "message": message, "message_type": "info"}

            # Создаем графики для веб
            plot_base64 = self.create_plots_base64()

            # Сохраняем файлы
            txt_path, png_path = self.save_files()

            # Данные для таблицы
            table_data = self.result_df.to_dict("index")

            return {
                "success": True,
                "message": f"Анализ завершен. {message}",
                "full_message": f"Файлы с таблицей и графиками находятся в папке {BASE_REPORTS_DIR}",
                "table_data": table_data,
                "plot_base64": plot_base64,
                "txt_path": txt_path,
                "png_path": png_path,
                "message_type": "success",
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Ошибка при анализе: {str(e)}",
                "message_type": "error",
            }
