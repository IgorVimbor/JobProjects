# Статистика по продолжительности исследования рекламационных изделий
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk

import paths # импортируем файл с путями до базы данных, отчетов и др.

class LengthStudyAnalysis:
    """Класс для анализа данных (без GUI)"""
    def __init__(self):
        self.year_now = paths.year_now
        self.date_new = paths.date_new

        self.load_data()
        self.process_data()


    def load_data(self):
        file = paths.file_database
        self.df = pd.read_excel(
            file,
            sheet_name=str(self.year_now),
            usecols=[
                "Дата поступления сообщения в ОТК",
                "Период выявления дефекта (отказа)",
                "Наименование изделия",
                "Обозначение изделия",
                "Номер рекламационного акта ПРИОБРЕТАТЕЛЯ изделия",
                "Дата рекламационного акта ПРИОБРЕТАТЕЛЯ изделия",
                "Дата поступления изделия",
                "Номер накладной прихода изделия",
                "Дата акта исследования",
            ],
            header=1,
        )

        # Переименовываем столбцы для удобства
        self.df.columns = [
            "Дата сообщения", "Потребитель", "Наименование", "Обозначение", "Номер РА",
            "Дата РА", "Дата прихода", "Номер накладной", "Дата исследования"
        ]


    def process_data(self):
        """метод для подготовки и обработки данных"""
        # Удаляем строки, где отсутствует даты в столбцах "Дата прихода" и "Дата исследования" (оба столбца пустые)
        self.df = self.df.dropna(subset=["Дата прихода", "Дата исследования"], how='all')

        # Заполняем отсутствующие значения в столбце Дата прихода на значения из столбца Дата сообщения, при условии,
        # что в столбце Номер накладной стоит "фото", иначе заполняем на None
        self.df["Дата прихода"] = self.df["Дата прихода"].where(
            self.df["Дата прихода"].notnull(),
            self.df["Дата сообщения"].where(self.df["Номер накладной"].str.contains("фото"), None)
        )

        # В столбце "Дата исследования" заменяем отсутствующие данные сегодняшней датой
        self.df["Дата исследования"] = self.df["Дата исследования"].fillna(self.date_new).apply(pd.to_datetime)

        # Переводим тип данных в столбцах в datetime64
        self.df[["Дата РА", "Дата прихода", "Дата исследования"]] = self.df[["Дата РА", "Дата прихода", "Дата исследования"]].apply(pd.to_datetime)

        # Создаем новый столбец в разницей между датой акта исследования и датой поступления
        self.df["DIFF"] = (self.df["Дата исследования"] - self.df["Дата прихода"]) / np.timedelta64(1, "D")

        # сохраняем в файлы датафреймы с отсутствующими актами по АСП и ГП
        self.save_missing_acts_reports()
        self.calculate_statistics()


    def save_missing_acts_reports(self):
        """метод для создания датафреймов с отсутствующими актами по АСП и ГП и сохранения в файлы"""
        # датафрейм изделий АСП по которым нет актов исследования
        df_asp_not_act = self.df[
            (self.df["Потребитель"].str.contains("АСП") == True)
            & (self.df["Дата исследования"].isnull())
        ][
            [
                "Потребитель",
                "Наименование",
                "Обозначение",
                "Номер РА",
                "Дата РА",
                "Дата прихода",
            ]
        ]

        # сохраняем в файл .txt
        with open(f"{paths.folder_reports}НЕТ актов АСП - {self.date_new}.txt", "w", encoding="utf-8") as f:
            print(f"\n\tПеречень актов рекламаций по которым НЕТ актов исследования на {self.date_new}\n\n", file=f)
            f.write(df_asp_not_act.to_string())

        # датафрейм изделий ГП по которым нет актов исследования
        df_gp_not_act = self.df[
            (self.df["Потребитель"].str.contains("эксплуатация") == True)
            & (self.df["Дата исследования"].isnull())
        ][
            [
                "Потребитель",
                "Наименование",
                "Обозначение",
                "Номер РА",
                "Дата РА",
                "Дата прихода",
            ]
        ]

        # сохраняем в файл .txt
        with open(f"{paths.folder_reports}НЕТ актов ГП - {self.date_new}.txt", "w", encoding="utf-8") as f:
            print(f"\n\tПеречень актов рекламаций по которым НЕТ актов исследования ГП на {self.date_new}\n\n", file=f)
            f.write(df_gp_not_act.to_string())


    def calculate_statistics(self):
        """метод для подсчета статистики"""
        # Общая статистика
        self.df_diff_mean = round(self.df["DIFF"].mean(), 2)
        self.df_diff_median = round(self.df["DIFF"].median(), 2)

        # Статистика по АСП
        self.df_asp = self.df[self.df["Потребитель"].str.contains("АСП") == True]
        self.df_asp = self.df_asp[self.df_asp["Дата прихода"].dt.day != self.date_new]
        self.df_asp_mean = round(self.df_asp["DIFF"].mean(), 2)
        self.df_asp_median = round(self.df_asp["DIFF"].median(), 2)

        # Статистика по ГП
        self.df_gp = self.df[self.df["Потребитель"].str.contains("эксплуатация") == True]
        self.df_gp_mean = round(self.df_gp["DIFF"].mean(), 2)
        self.df_gp_median = round(self.df_gp["DIFF"].median(), 2)

        self.result_df = pd.DataFrame(
            [
                [self.df_diff_mean, self.df_asp_mean, self.df_gp_mean],
                [self.df_diff_median, self.df_asp_median, self.df_gp_median]
            ],
            index=["Среднее", "Медиана"],
            columns=["Общее", "АСП", "ГП"]
        )

    def create_plots(self):
        """метод для создания графиков"""
        fig, axes = plt.subplots(1, 3, figsize=(12, 4))

        # Гистограмма общая
        axes[0].hist(self.df["DIFF"], bins=20, color='skyblue', edgecolor='black')
        axes[0].set_title("Общая статистика")
        axes[0].set_xlabel("Дни")
        axes[0].set_ylabel("Количество")

        # Гистограмма АСП
        axes[1].hist(self.df_asp["DIFF"], bins=20, color='salmon', edgecolor='black')
        axes[1].set_title("АСП")
        axes[1].set_xlabel("Дни")

        # Гистограмма ГП
        axes[2].hist(self.df_gp["DIFF"], bins=20, color='lightgreen', edgecolor='black')
        axes[2].set_title("ГП")
        axes[2].set_xlabel("Дни")

        plt.tight_layout()
        return fig


class LengthStudyWindow(tk.Toplevel):
    """Окно с выбором типа отчёта"""
    def __init__(self, master=None):
        super().__init__(master)
        self.title("Анализ длительности исследований")
        self.geometry("400x300")

        self.analysis = LengthStudyAnalysis()  # Создаём экземпляр анализатора

        ttk.Label(self, text="Выберите тип отчёта:", font=('Arial', 12)).pack(pady=10)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=20)

        ttk.Button(btn_frame, text="Таблица статистики",
                 command=self.show_stats).pack(pady=5, fill=tk.X)
        ttk.Button(btn_frame, text="Гистограммы",
                 command=self.show_plots).pack(pady=5, fill=tk.X)
        ttk.Button(btn_frame, text="Оба отчёта",
                 command=self.show_both).pack(pady=5, fill=tk.X)

    def show_stats(self):
        StatsWindow(self, self.analysis.result_df)

    def show_plots(self):
        PlotsWindow(self, self.analysis.create_plots())

    def show_both(self):
        self.show_stats()
        self.show_plots()


class StatsWindow(tk.Toplevel):
    """Окно с таблицей статистики"""
    def __init__(self, master, data_df):
        super().__init__(master)
        self.title("Статистика длительности")
        self.geometry("600x300")

        text = tk.Text(self, wrap=tk.NONE)
        text.insert(tk.END, data_df.to_string())
        text.config(state=tk.DISABLED)

        scroll_x = ttk.Scrollbar(self, orient=tk.HORIZONTAL, command=text.xview)
        scroll_y = ttk.Scrollbar(self, orient=tk.VERTICAL, command=text.yview)
        text.configure(xscrollcommand=scroll_x.set, yscrollcommand=scroll_y.set)

        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)


class PlotsWindow(tk.Toplevel):
    """Окно с гистограммами"""
    def __init__(self, master, figure):
        super().__init__(master)
        self.title("Гистограммы длительности")
        self.geometry("900x500")

        canvas = FigureCanvasTkAgg(figure, master=self)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
