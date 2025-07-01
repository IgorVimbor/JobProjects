import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk

import paths  # импортируем файл с путями до базы данных, отчетов и др.


year_now = paths.year_now  # текущий год
date_new = paths.date_new  # сегодняшняя дата
file = paths.file_database  # путь к базе рекламаций ОТК
file_out = paths.folder_reports  # путь к каталогу для сохранения отчетов


class LengthStudyAnalysis:
    """Класс для анализа данных (без GUI)"""

    def calculate_statistics(self):
        """метод для подсчета статистики"""
        self.df = pd.read_excel(
            file,
            sheet_name=str(year_now),
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
            "Дата сообщения", "Потребитель", "Наименование", "Обозначение",
            "Номер РА", "Дата РА", "Дата прихода", "Номер накладной", "Дата исследования"
        ]
        # --------------------------------- Обработка значений столбцов датафрейма ---------------------------------------

        # Удаляем строки, где отсутствует дата в столбце "Дата исследования"
        self.df = self.df.dropna(subset=["Дата исследования"])

        # удаляем строки с сегодняшним приходом
        self.df = self.df[self.df["Дата прихода"] != date_new]

        # Заполняем отсутствующие значения в столбце Дата прихода на значения из столбца Дата сообщения, при условии,
        # что в столбце Номер накладной стоит "фото", иначе заполняем датой исследования
        self.df["Дата прихода"] = self.df["Дата прихода"].where(
            self.df["Дата прихода"].notnull(),
            self.df["Дата сообщения"].where(self.df["Номер накладной"].str.contains("фото"), self.df["Дата исследования"])
            )

        # переводим тип данных в столбцах в datetime64
        self.df[["Дата РА", "Дата прихода", "Дата исследования"]] = self.df[["Дата РА", "Дата прихода", "Дата исследования"]].apply(pd.to_datetime)

        # создаем новый столбец в разницей между датой акта исследования и датой поступления
        self.df["DIFF"] = (self.df["Дата исследования"] - self.df["Дата прихода"]) / np.timedelta64(1, "D")

        # ----------------------------- Общая средняя продолжительность исследования -----------------------------

        # находим среднее и медианное значение
        self.df_mean = round(self.df["DIFF"].mean(), 2)
        self.df_median = round(self.df["DIFF"].median(), 2)

        # ----------------------------- Продолжительность исследования по АСП ------------------------------------

        self.df_asp = self.df[self.df["Потребитель"].str.contains("АСП") == True]
        # находим среднее и медианное значение
        self.asp_mean = round(self.df_asp["DIFF"].mean(), 2)
        self.asp_median = round(self.df_asp["DIFF"].median(), 2)

        # ------------------------------ Продолжительность исследования по ГП ------------------------------------

        self.df_gp = self.df[self.df["Потребитель"].str.contains("эксплуатация") == True]
        # находим среднее и медианное значение
        self.gp_mean = round(self.df_gp["DIFF"].mean(), 2)  # 5.86
        self.gp_median = round(self.df_gp["DIFF"].median(), 2)  #  3.0

        # ---------------------------------------- Результат ------------------------------------------------------

        self.result_df = pd.DataFrame(
            [
                [self.df_mean, self.asp_mean, self.gp_mean],
                [self.df_median, self.asp_median, self.gp_median]
            ],
            index=["Среднее значение", "Медианное значение"],
            columns=["В целом", "Конвейер", "Эксплуатация"],
        )

        return self.result_df


    def create_plots(self):
        fig, axes = plt.subplots(1, 3, figsize=(12, 4))

        # Общая гистограмма
        axes[0].hist(self.df["DIFF"], self.df["DIFF"].count(), color='skyblue', edgecolor='black')
        axes[0].set_title("Общая статистика")
        axes[0].set_xlim(-2, 40)
        axes[0].set_ylabel("Количество исследований")

        # Гистограмма АСП
        axes[1].hist(self.df_asp["DIFF"], self.df_asp["DIFF"].count(), color='salmon', edgecolor='black')
        axes[1].set_title("Исследование по АСП")
        axes[1].set_xlim(-1, 40)
        axes[1].set_xlabel("Количество дней")

        # Гистограмма ГП
        axes[2].hist(self.df_gp["DIFF"], self.df_gp["DIFF"].count(), color='lightgreen', edgecolor='black')
        axes[2].set_title("Исследование по ГП")
        axes[2].set_xlim(-1, 40)

        # добавляем заголовок
        fig.suptitle(f"{year_now} год", fontsize=16)

        plt.tight_layout()

        return fig


class LengthStudyWindow(tk.Toplevel):
    """Главное окно анализа с вкладками"""
    def __init__(self, master=None):
        super().__init__(master)

        # Блокируем взаимодействие с родительским окном
        self.grab_set()
        self.transient(master)

        self.title("Анализ длительности исследований")
        # self.iconbitmap("IconBZA.ico")

        width = 1000
        heigh = 500
        screenwidth = self.winfo_screenwidth()
        screenheight = self.winfo_screenheight()
        self.geometry("%dx%d+%d+%d" % (width, heigh, (screenwidth - width) / 2, (screenheight - heigh) / 3))

        # Создаем анализатор данных и получаем результат статистики
        self.analysis = LengthStudyAnalysis()
        self.table_statistic = self.analysis.calculate_statistics()

        # Создаем Notebook (вкладки)
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Вкладка с таблицей
        self.create_stats_tab()

        # Вкладка с графиками
        self.create_plots_tab()

        # По умолчанию показываем первую вкладку
        self.notebook.select(0)


    def create_stats_tab(self):
        """метод для создания вкладки с таблицей статистики, пояснением и кнопкой сохранения"""
        tab_stats = ttk.Frame(self.notebook)
        self.notebook.add(tab_stats, text="Статистика")

        # Основной фрейм с белым фоном
        main_frame = tk.Frame(tab_stats, bg='white')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10, anchor='nw')

        # Фрейм для кнопки (выравниваем по правому краю)
        button_frame = tk.Frame(main_frame, bg='white')
        button_frame.pack(fill=tk.X, pady=(0, 10))

        # Кнопка "Сохранить в файл"
        save_btn = ttk.Button(
            button_frame,
            text="Сохранить в файл",
            command=self.save_reports_handler,
            style='Accent.TButton'  # Стиль для выделенной кнопки
        )
        save_btn.pack(side=tk.RIGHT, padx=5)

        # Пояснительный текст
        info_label = tk.Label(
            main_frame,
            text=f"Представленные в таблице данные рассчитаны за {year_now} год по состоянию на {date_new}.\n\n"\
                "Длительность исследований рассчитывалась, как разница между датами акта исследования и прихода изделия на завод,\n"\
                "за исключением приходов сегодняшнего дня.",
            font=('Arial', 10, 'italic'),
            bg='white',
            anchor='w',
            justify='left'
        )
        info_label.pack(fill=tk.X, pady=(0, 10), anchor='w')

        # Пустая строка
        tk.Label(main_frame, text="", bg='white').pack(anchor='w')

        # Текст с результатами (таблица статистики)
        text = tk.Text(
            main_frame,
            wrap=tk.NONE,
            font=('Courier New', 12),
            bg='white',
            padx=5,
            pady=5,
            height=10,
            width=60
        )
        text.insert(tk.END, self.table_statistic.to_string())
        text.config(state=tk.DISABLED)
        text.pack(fill=tk.BOTH, expand=True, anchor='nw')


    def save_reports_handler(self):
        """Обработчик кнопки сохранения таблицы с уведомлениями"""
        try:
            # сохраняем в файл txt таблицу со статистикой
            with open(f"{file_out}Статистика длительности исследований_{date_new}.txt", "w", encoding="utf-8") as f:
                print(f"\n\tСтатистика длительности исследований за {year_now} на {date_new}\n\n", file=f)
                f.write(self.table_statistic.to_string())

            messagebox.showinfo("Успешно", f"Отчет со статистикой сохранен в каталоге:\n\n{file_out}", parent=self)

        except Exception as e:
            messagebox.showerror("Ошибка", "Не удалось сохранить отчет", parent=self)


    def create_plots_tab(self):
        """метод для создания вкладки с графиками"""
        tab_plots = ttk.Frame(self.notebook)
        self.notebook.add(tab_plots, text="Гистограммы")

        # Фрейм для кнопки (выравниваем по правому краю)
        button_frame = tk.Frame(tab_plots)
        button_frame.pack(fill=tk.X, pady=(0, 10))

        # Кнопка "Сохранить в файл"
        save_btn = ttk.Button(
            button_frame,
            text="Сохранить в файл",
            command=self.save_plots_handler,
            style='Accent.TButton'  # Стиль для выделенной кнопки
        )
        save_btn.pack(side=tk.RIGHT, padx=5)

        # Создаем графики
        self.figure = self.analysis.create_plots()

        # Встраиваем график в Tkinter
        canvas = FigureCanvasTkAgg(self.figure, master=tab_plots)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)


    def save_plots_handler(self):
        """Обработчик кнопки сохранения графика с уведомлениями"""

        try:
            self.figure.savefig(f"{file_out}График длительности исследований_{date_new}.pdf")
            messagebox.showinfo("Успешно", f"График сохранен в каталоге:\n\n{file_out}", parent=self)
        except Exception as e:
            messagebox.showerror("Ошибка", "Не удалось сохранить график", parent=self)
