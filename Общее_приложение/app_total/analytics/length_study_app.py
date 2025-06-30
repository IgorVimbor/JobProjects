# Статистика по продолжительности исследования рекламационных изделий
import os
import pandas as pd
import numpy as np
import warnings
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk

import paths  # импортируем файл с путями до базы данных, отчетов и др.

class LengthStudyApp:
    def __init__(self, master=None):
        self.master = master if master else tk.Tk()
        self.master.title("Длительность исследования рекламаций")
        self.master.geometry("900x700")

        self.year_now = paths.year_now  # текущий год
        self.date_new = paths.date_new  # сегодняшняя дата

        self.create_widgets()
        self.load_data()
        self.process_data()
        self.display_results()
        self.create_plots()

    def create_widgets(self):
        self.main_frame = ttk.Frame(self.master)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Results frame
        self.results_frame = ttk.LabelFrame(self.main_frame, text="Результаты")
        self.results_frame.pack(fill=tk.X, padx=10, pady=5)

        # Plots frame
        self.plots_frame = ttk.LabelFrame(self.main_frame, text="Графики")
        self.plots_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    def load_data(self):
        file = paths.file_database  # путь к базе рекламаций ОТК

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

        # переименовываем столбцы для удобства
        self.df.columns = [
            "Дата сообщения",
            "Потребитель",
            "Наименование",
            "Обозначение",
            "Номер РА",
            "Дата РА",
            "Дата прихода",
            "Номер накладной",
            "Дата исследования"
        ]

    def process_data(self):
        # удаляем строки, где отсутствует даты в столбцах "Дата прихода" и "Дата исследования" (оба столбца пустые)
        self.df = self.df.dropna(subset=["Дата прихода", "Дата исследования"], how='all')

        # Заполняем отсутствующие значения
        self.df["Дата прихода"] = self.df["Дата прихода"].where(
            self.df["Дата прихода"].notnull(),
            self.df["Дата сообщения"].where(self.df["Номер накладной"].str.contains("фото"), None)
        )

        # переводим тип данных в столбцах в datetime64
        self.df[["Дата РА", "Дата прихода", "Дата исследования"]] = self.df[
            ["Дата РА", "Дата прихода", "Дата исследования"]
        ].apply(pd.to_datetime)

        # сохраняем файлы с изделиями без актов
        self.save_missing_acts_reports()

        # в столбце "Дата акта исследования" заменяем отсутствующие данные сегодняшней датой
        self.df["Дата исследования"] = self.df["Дата исследования"].fillna(self.date_new).apply(pd.to_datetime)

        # создаем новый столбец в разницей между датой акта исследования и датой поступления
        self.df["DIFF"] = (self.df["Дата исследования"] - self.df["Дата прихода"]) / np.timedelta64(1, "D")

        # Рассчитываем статистики
        self.calculate_statistics()

    def save_missing_acts_reports(self):
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
        # Общая статистика
        self.df_diff_mean = round(self.df["DIFF"].mean(), 2)
        self.df_diff_median = round(self.df["DIFF"].median(), 2)

        # Статистика по АСП
        self.df2 = self.df[self.df["Потребитель"].str.contains("АСП") == True]
        self.df2 = self.df2[self.df2["Дата прихода"].dt.day != self.date_new]
        self.df2_diff_mean = round(self.df2["DIFF"].mean(), 2)
        self.df2_diff_median = round(self.df2["DIFF"].median(), 2)

        # Статистика по ГП
        self.df3 = self.df[self.df["Потребитель"].str.contains("эксплуатация") == True]
        self.df3_diff_mean = round(self.df3["DIFF"].mean(), 2)
        self.df3_diff_median = round(self.df3["DIFF"].median(), 2)

    def display_results(self):
        data = [
            [self.df_diff_mean, self.df2_diff_mean, self.df3_diff_mean],
            [self.df_diff_median, self.df2_diff_median, self.df3_diff_median],
        ]

        self.result = pd.DataFrame(
            data,
            index=["Среднее значение", "Медианное значение"],
            columns=["В целом", "Конвейер", "Эксплуатация"],
        )

        # Create a text widget to display the results
        text = tk.Text(self.results_frame, height=5, width=80)
        text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        text.insert(tk.END, self.result.to_string())
        text.config(state=tk.DISABLED)

    def create_plots(self):
        # укзываем количество строк и столбцов на рисунке и размеры рисунка
        fig, axes = plt.subplots(nrows=1, ncols=3, figsize=(10, 4))

        # гистограмма по исследованию в целом
        axes[0].hist(self.df["DIFF"], self.df["DIFF"].count())
        axes[0].set_title("Исследование в целом")
        axes[0].set_xlim(-2, 40)
        axes[0].set_ylim(0, 60)
        axes[0].set_xlabel("Количество дней")
        axes[0].set_ylabel("Количество исследований\n(значения ограничены для лучшей визуализации)")

        # гистограмма по АСП
        axes[1].hist(self.df2["DIFF"], self.df2["DIFF"].count())
        axes[1].set_title("Исследование по АСП")
        axes[1].set_xlim(-1, 40)
        axes[1].set_xlabel("Количество дней")
        axes[1].set_ylabel("Количество исследований")

        # истограмма по ГП
        axes[2].hist(self.df3["DIFF"], self.df3["DIFF"].count())
        axes[2].set_title("Исследование по ГП")
        axes[2].set_xlim(-1, 40)
        axes[2].set_xlabel("Количество дней")
        axes[2].set_ylabel("Количество исследований")

        # раздвигаем графики друг от друга по ширине
        fig.subplots_adjust(wspace=0.3)

        # добавляем заголовок
        fig.suptitle(f"{self.year_now} год", fontsize=16)

        # Embed the plot in the Tkinter window
        canvas = FigureCanvasTkAgg(fig, master=self.plots_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)