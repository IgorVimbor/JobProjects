# Основной модуль приложения <Копирование отгрузки>
import os
import tkinter as tk
from tkinter import messagebox
import tkinter.ttk as ttk
import time

import copier.copier_modul as cm


class CopierData(tk.Toplevel):
    def __init__(self, master=None):
        super().__init__(master)

        self.iconbitmap("IconBZA.ico")
        self.title("КОПИРОВАНИЕ ДАННЫХ ПО ОТГРУЗКЕ В ФАЙЛЫ ОТК")

        width = 710
        heigh = 380
        screenwidth = self.winfo_screenwidth()
        screenheight = self.winfo_screenheight()
        self.geometry(
            "%dx%d+%d+%d"
            % (width, heigh, (screenwidth - width) / 2, (screenheight - heigh) / 3)
        )

        # Пустая строка перед фреймом
        lbl_null_1 = tk.Label(self, text="")
        lbl_null_1.pack()

        # Создается ПЕРВАЯ рамка frm_form_1 для размещения рамок frame1 и frame2
        self.frm_form_1 = tk.Frame(self, relief=tk.SUNKEN, borderwidth=3)
        self.frm_form_1.pack()

        # Создается рамка frame1
        self.frame1 = tk.Frame(
            master=self.frm_form_1,
            relief=tk.SUNKEN,
            borderwidth=3,
            width=300,
            height=270,
            bg="white",
        )
        self.frame1.pack(fill=tk.BOTH, side=tk.LEFT)

        # Создается рамка frame2
        self.frame2 = tk.Frame(
            master=self.frm_form_1, relief=tk.SUNKEN, borderwidth=3, width=300, bg="white"
        )
        self.frame2.pack(fill=tk.BOTH, side=tk.LEFT)

        # Заполняем рамку frame1
        lbl_1 = tk.Label(
            master=self.frame1,
            text="\nВНИМАНИЕ!\n\n"
            "Проверьте расположение и наименование файлов.\n"
            "Файлы должны иметь расширение .xlsx\n\n"
            "\nПосле проверки нажмите кнопку КОПИРОВАТЬ.",
            justify="left",
            font=("Arial Bold", 10),
            bg="white",
        )
        lbl_1.grid(row=0, column=0, padx=5, sticky="w")

        # Заполняем рамку frame2
        lbl_2 = tk.Label(
            master=self.frame2,
            text="Каталог (папка):\n"
            "     - otk на Server\n"
            "     - ОТЧЕТНОСТЬ БЗА\n"
            "     - ОТГРУЗКА+ГАРАНТИЙНЫЙ ПАРК\n"
            "Файлы:\n"
            "     - Отгрузка для ОТК_текущий год.xlsx\n"
            "     - ОТГРУЗКА+ГАРАНТИЙНЫЙ ПАРК_текущий год.xlsx\n"
            "     - Отчет по дефектности БЗА_текущий месяц.xlsx\n",
            justify="left",
            font=("Arial Bold", 10),
            bg="white",
        )
        lbl_2.grid(row=0, column=0, padx=5, sticky="w")

        # Пустая строка перед следующей рамкой
        lbl_null_2 = tk.Label(self, text="")
        lbl_null_2.pack()

        # Создаем кнопку "КОПИРОВАТЬ"
        self.bnt_1 = tk.Button(
            self,
            text="КОПИРОВАТЬ",
            font=("Arial Bold", 12),
            fg="green",
            bg="linen",
            activebackground="peach puff",
            relief=tk.SUNKEN,
            command=self.on_button_click,
        )
        self.bnt_1.pack(padx=10)

        # Пустая строка перед следующей рамкой
        lbl_null_3 = tk.Label(self, text="")
        lbl_null_3.pack()

        # Создается ТРЕТЬЯ рамка frm_form_3 для размещения индикатора загрузки
        self.frm_form_3 = tk.Frame(self, relief=tk.SUNKEN, borderwidth=3)
        self.frm_form_3.pack()

        # Создается виджет индикатора загрузки
        self.progress_bar = ttk.Progressbar(
            self.frm_form_3,
            orient="horizontal",
            mode="determinate",
            length=500,
            maximum=100,
            value=0,
        )
        lbl_3 = tk.Label(self.frm_form_3, text="Процесс копирования")

        lbl_3.grid(row=0, column=0)
        self.progress_bar.grid(row=0, column=1)

        # Пустые строки
        for _ in range(3):
            lbl_null = tk.Label(self, text="")
            lbl_null.pack()

        # Личная подпись
        lbl_4 = tk.Label(self, text="Development by IGOR VASILENOK  ")
        lbl_4.pack(side=tk.RIGHT)

    def data_copier(self):
        """функция копирования отгрузки из файла ОСиМ в файл ОТК на Лист конкретного месяца,
        а затем на лист "Гарантийный парк" и лист "Данные2" файла отчета"""

        pr = cm.ExcelSheetCopier()

        pr.copy_in_otk(3, 21, 1)  # ТКР
        self.progress_bar["value"] += 10
        self.update()
        pr.copy_in_otk(23, 40, 2)  # ПК
        self.progress_bar["value"] += 10
        self.update()
        pr.copy_in_otk(42, 59, 3)  # ВН
        self.progress_bar["value"] += 10
        self.update()
        pr.copy_in_otk(61, 75, 4)  # МН
        self.progress_bar["value"] += 10
        self.update()
        pr.copy_in_otk(77, 83, 5)  # ГП
        self.progress_bar["value"] += 10
        self.update()
        pr.copy_in_otk(85, 96, 6)  # ЦМФ
        self.progress_bar["value"] += 10
        self.update()
        pr.copy_in_otk(110, 114, 11)  # штанга и коромысло
        self.progress_bar["value"] += 10
        self.update()

        grp = cm.DataCopierGarant()
        grp.copy_garant()
        self.progress_bar["value"] += 10
        self.update()

        self.progress_bar["value"] = 100
        self.update()

        time.sleep(1)

    def on_button_click(self):
        """функция запуска копирования и изменения поведения кнопки в процессе копирования"""

        self.bnt_1.config(state="disabled", fg="black")

        try:
            self.data_copier()

            self.bnt_1.config(state="normal", fg="green")
            time.sleep(0.5)

            result = messagebox.askyesno(
                "СООБЩЕНИЕ",
                f"Данные по отгрузке скопированы в файл {cm.file_otk}.\n\nОткрыть файл?",
                parent=self
            )

            if result:  # Если пользователь нажал "Да"
                self._open_file(cm.file_otk)

                # Закрываем окно после успешного завершения
                self.destroy()
            else:
                self.progress_bar["value"] = 0

        except Exception as e:
            messagebox.showerror(
                "ОШИБКА",
                f"Произошла ошибка при работе приложения:\n\n{e}",
                parent=self
            )
            self.destroy()

    def _open_file(self, file_path):
        """Открывает файл с помощью стандартного приложения Windows"""
        try:
            os.startfile(file_path)
        except Exception as e:
            messagebox.showwarning(
                "Ошибка открытия",
                f"Не удалось открыть файл:\n{str(e)}",
                parent=self
            )
