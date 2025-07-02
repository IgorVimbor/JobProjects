import pandas as pd
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk

import paths_work  # импортируем файл с путями до базы данных, отчетов и др.


year_now = paths_work.year_now  # текущий год
date_new = paths_work.date_new  # сегодняшняя дата
file = paths_work.file_database  # путь к базе рекламаций ОТК
file_out = paths_work.folder_reports  # путь к каталогу для сохранения отчетов


class NotActsApp:
    """Класс для подготовки информации по не закрытым актам рекламаций (без GUI)"""

    def make_frame_not_act(self):
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

        # Удаляем строки, где отсутствует даты в столбцах "Дата прихода" и "Дата исследования" (оба столбца пустые)
        self.df = self.df.dropna(subset=["Дата прихода", "Дата исследования"], how='all')

        # Заполняем отсутствующие значения в столбце Дата прихода на значения из столбца Дата сообщения, при условии,
        # что в столбце Номер накладной стоит "фото", иначе заполняем None
        self.df["Дата прихода"] = self.df["Дата прихода"].where(
            self.df["Дата прихода"].notnull(),
            self.df["Дата сообщения"].where(self.df["Номер накладной"].str.contains("фото"), None)
            )

        # переводим тип данных в столбцах в datetime64
        self.df[["Дата РА", "Дата прихода", "Дата исследования"]] = self.df[["Дата РА", "Дата прихода", "Дата исследования"]].apply(pd.to_datetime)

        # приводим нумерацию строк в датафрейме как в базе рекламаций
        self.df.index = self.df.index + 3
        # присваиваем индексу строк датафрейма наименование "Строка базы"
        self.df.index.name = "Строка базы"

        # --------------------------- Датафрейм изделий по АСП по которым НЕТ актов --------------------------------

        self.df_asp = self.df[
            (self.df["Потребитель"].str.contains("АСП") == True) & (self.df["Дата исследования"].isnull())
        ][
            ["Потребитель", "Наименование", "Обозначение", "Номер РА", "Дата РА", "Дата прихода"]
        ]

        # --------------------------- Датафрейм изделий по ГП по которым НЕТ актов ----------------------------------

        self.df_gp = self.df[
            (self.df["Потребитель"].str.contains("эксплуатация") == True) & (self.df["Дата исследования"].isnull())
        ][
            ["Потребитель", "Наименование", "Обозначение", "Номер РА", "Дата РА", "Дата прихода"]
        ]

        return self.df_asp, self.df_gp


class NotActsWindow(tk.Toplevel):
    """Главное окно с вкладками"""
    def __init__(self, master=None):
        super().__init__(master)

        # Блокируем взаимодействие с родительским окном
        self.grab_set()
        self.transient(master)

        # Настройка окна
        self.title("Перечень не закрытых актов рекламаций")
        # self.iconbitmap("IconBZA.ico")

        width = 1000
        heigh = 500
        screenwidth = self.winfo_screenwidth()
        screenheight = self.winfo_screenheight()
        self.geometry("%dx%d+%d+%d" % (width, heigh, (screenwidth - width) / 2, (screenheight - heigh) / 3))

        # Создаем анализатор данных и получаем датафреймы по АСП и ГП
        self.analysis = NotActsApp()
        self.df_asp, self.df_gp = self.analysis.make_frame_not_act()

        # Создаем Notebook (вкладки)
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Вкладка с таблицей по АСП
        self.create_stats_asp()

        # Вкладка с таблицей по ГП
        self.create_stats_gp()

        # По умолчанию показываем первую вкладку
        self.notebook.select(0)


    def create_stats_asp(self):
        """метод для создания вкладки с таблицей по АСП и кнопкой сохранения"""
        tab_stats = ttk.Frame(self.notebook)
        self.notebook.add(tab_stats, text="АСП")

        # Текст (таблица) с результатами по АСП
        text = tk.Text(tab_stats, wrap=tk.NONE, font=('Courier New', 11))
        text.insert(tk.END, self.df_asp.to_string())
        text.config(state=tk.DISABLED)

        # Полосы прокрутки
        scroll_x = ttk.Scrollbar(tab_stats, orient=tk.HORIZONTAL, command=text.xview)
        scroll_y = ttk.Scrollbar(tab_stats, orient=tk.VERTICAL, command=text.yview)
        text.configure(xscrollcommand=scroll_x.set, yscrollcommand=scroll_y.set)

        # Фрейм для кнопки (выравниваем по правому краю)
        button_frame = tk.Frame(tab_stats, bg='white')
        button_frame.pack(fill=tk.X, pady=(0, 10))

        # Кнопка "Сохранить в файл"
        save_btn = ttk.Button(
            button_frame,
            text="Сохранить в файл",
            command=self.save_reports_asp,
            style='Accent.TButton'  # Стиль для выделенной кнопки
        )
        save_btn.pack(side=tk.RIGHT, padx=5)

        # Пояснительный текст
        info_label = tk.Label(
            button_frame,
            text=f"Перечень актов рекламаций на АСП, по которым НЕТ актов исследования на {date_new}",
            font=('Arial', 10, 'bold'),
            bg='white',
            justify='center'
        )
        info_label.pack(fill=tk.X, pady=(5, 10))

        # Размещаем элементы
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)


    def save_reports_asp(self):
        """Обработчик кнопки сохранения таблицы по АСП с уведомлениями"""
        try:
            # сохраняем отчет по АСП в файл txt
            with open(f"{file_out}НЕТ актов АСП_{date_new}.txt", "w", encoding="utf-8") as f:
                print(f"\n\n\tПеречень актов рекламаций на АСП, по которым НЕТ актов исследования на {date_new}\n\n\n", file=f)
                f.write(self.df_asp.to_string())

            messagebox.showinfo("Успешно", f"Отчет с данными по АСП сохранен в каталоге:\n\n{file_out}", parent=self)

        except Exception as e:
            messagebox.showerror("Ошибка", "Не удалось сохранить отчет", parent=self)


    def create_stats_gp(self):
        """метод для создания вкладки с таблицей по ГП и кнопкой сохранения"""
        tab_stats = ttk.Frame(self.notebook)
        self.notebook.add(tab_stats, text="Эксплуатация")

        # Текст (таблтца) с результатами по ГП
        text = tk.Text(tab_stats, wrap=tk.NONE, font=('Courier New', 11))
        text.insert(tk.END, self.df_gp.to_string())
        text.config(state=tk.DISABLED)

        # Полосы прокрутки
        scroll_x = ttk.Scrollbar(tab_stats, orient=tk.HORIZONTAL, command=text.xview)
        scroll_y = ttk.Scrollbar(tab_stats, orient=tk.VERTICAL, command=text.yview)
        text.configure(xscrollcommand=scroll_x.set, yscrollcommand=scroll_y.set)

        # Фрейм для кнопки (выравниваем по правому краю)
        button_frame = tk.Frame(tab_stats, bg='white')
        button_frame.pack(fill=tk.X, pady=(0, 10))

        # Кнопка "Сохранить в файл"
        save_btn = ttk.Button(
            button_frame,
            text="Сохранить в файл",
            command=self.save_reports_gp,
            style='Accent.TButton'  # Стиль для выделенной кнопки
        )
        save_btn.pack(side=tk.RIGHT, padx=5)

        # Пояснительный текст
        info_label = tk.Label(
            button_frame,
            text=f"Перечень актов рекламаций из Эксплуатации, по которым НЕТ актов исследования на {date_new}",
            font=('Arial', 10, 'bold'),
            bg='white',
            justify='center'
        )
        info_label.pack(fill=tk.X, pady=(5, 10))

        # Размещаем элементы
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)


    def save_reports_gp(self):
        """Обработчик кнопки сохранения таблицы по ГП с уведомлениями"""
        try:
            # сохраняем отчет по ГП в файл txt
            with open(f"{file_out}НЕТ актов ГП_{date_new}.txt", "w", encoding="utf-8") as f:
                print(f"\n\n\tПеречень актов рекламаций из Эксплуатации, по которым НЕТ актов исследования на {date_new}\n\n\n", file=f)
                f.write(self.df_gp.to_string())

            messagebox.showinfo("Успешно", f"Отчет с данными по ГП сохранен в каталоге:\n\n{file_out}", parent=self)

        except Exception as e:
            messagebox.showerror("Ошибка", "Не удалось сохранить отчет", parent=self)
