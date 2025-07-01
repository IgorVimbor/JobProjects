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
    def __init__(self):
        self.load_data()
        self.process_data()


    def load_data(self):
        """метод для загрузки данных из базы рекламаций ОТК"""
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


    def process_data(self):
        """метод для подготовки и обработки данных"""
        # Удаляем строки, где отсутствует даты в столбцах "Дата прихода" и "Дата исследования" (оба столбца пустые)
        self.df = self.df.dropna(subset=["Дата прихода", "Дата исследования"], how='all')

        # Заполняем отсутствующие значения в столбце Дата прихода на значения из столбца Дата сообщения, при условии,
        # что в столбце Номер накладной стоит "фото", иначе заполняем на None
        self.df["Дата прихода"] = self.df["Дата прихода"].where(
            self.df["Дата прихода"].notnull(),
            self.df["Дата сообщения"].where(self.df["Номер накладной"].str.contains("фото"), None))

        # Переводим тип данных в столбцах в datetime64
        self.df[["Дата РА", "Дата прихода", "Дата исследования"]] = self.df[["Дата РА", "Дата прихода", "Дата исследования"]].apply(pd.to_datetime)

        # Расчитываем статистику
        self.calculate_statistics()


    def save_missing_acts_reports(self):
        """метод для создания датафреймов с отсутствующими актами по АСП и ГП и сохранения в файлы"""
        # датафрейм изделий АСП по которым нет актов исследования
        df_asp_not_act = self.df[
            (self.df["Потребитель"].str.contains("АСП") == True)
            & (self.df["Дата исследования"].isnull())
        ][
            ["Потребитель", "Наименование", "Обозначение", "Номер РА", "Дата РА", "Дата прихода"]
        ]

        # датафрейм изделий ГП по которым нет актов исследования
        df_gp_not_act = self.df[
            (self.df["Потребитель"].str.contains("эксплуатация") == True)
            & (self.df["Дата исследования"].isnull())
        ][
            ["Потребитель", "Наименование", "Обозначение", "Номер РА", "Дата РА", "Дата прихода"]
        ]

        # Сохранение в файлы
        try:
            # сохраняем в файл txt таблицу с отсутствующими актами по АСП
            with open(f"{file_out}НЕТ актов АСП_{date_new}.txt", "w", encoding="utf-8") as f:
                print(f"\n\tПеречень актов рекламаций по которым НЕТ актов исследования на {date_new}\n\n", file=f)
                f.write(df_asp_not_act.to_string())

            # сохраняем в файл txt таблицу с отсутствующими актами по ГП
            with open(f"{file_out}НЕТ актов ГП_{date_new}.txt", "w", encoding="utf-8") as f:
                print(f"\n\tПеречень актов рекламаций по которым НЕТ актов исследования ГП на {date_new}\n\n", file=f)
                f.write(df_gp_not_act.to_string())

            return True, f"Отчеты сохранены в каталоге:\n\n{file_out}"

        except Exception as e:
            return False, f"Не удалось сохранить файлы: {str(e)}"


class LengthStudyWindow(tk.Toplevel):
    """Главное окно анализа с вкладками"""
    def __init__(self, master=None):
        super().__init__(master)

        # Блокируем взаимодействие с родительским окном
        self.grab_set()
        self.transient(master)

        self.title("Анализ длительности исследований")
        width = 1000
        heigh = 500
        screenwidth = self.winfo_screenwidth()
        screenheight = self.winfo_screenheight()
        self.geometry("%dx%d+%d+%d" % (width, heigh, (screenwidth - width) / 2, (screenheight - heigh) / 3))

        # Создаем анализатор данных
        self.analysis = LengthStudyAnalysis()

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
        text.insert(tk.END, self.analysis.result_df.to_string())
        text.config(state=tk.DISABLED)
        text.pack(fill=tk.BOTH, expand=True, anchor='nw')


    def save_reports_handler(self):
        """Обработчик кнопки сохранения таблицы с уведомлениями"""
        # вызываем метод сохранения в файлы
        success, message = self.analysis.save_missing_acts_reports()

        if success:
            messagebox.showinfo("Успешно", message, parent=self)
        else:
            messagebox.showerror("Ошибка", message, parent=self)
