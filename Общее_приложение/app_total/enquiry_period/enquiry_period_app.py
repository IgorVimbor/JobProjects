import tkinter as tk
from tkinter import messagebox
import time

import enquiry_period.enquiry_period_modul as epm


class EnquiryPeriod(tk.Toplevel):
    def __init__(self, master=None):
        super().__init__(master)

        self.iconbitmap("app_total/IconBZA.ico")
        self.title("СПРАВКА О КОЛИЧЕСТВЕ РЕКЛАМАЦИЙ ЗА ПЕРИОД")

        width = 566  # ширина окна
        heigh = 380  # высота окна
        screenwidth = self.winfo_screenwidth()
        screenheight = self.winfo_screenheight()
        self.geometry(
            "%dx%d+%d+%d"
            % (width, heigh, (screenwidth - width) / 2, (screenheight - heigh) / 3)
        )

        # Первый фрейм для строк и полей для текста
        lbl_null_1 = tk.Label(self, text="")
        lbl_null_1.grid(row=0, column=0)

        self.frm_1 = tk.LabelFrame(
            self,
            text="Номера строк базы рекламаций ОТК",
            font=("Arial Bold", 14),
            labelanchor="n",
        )
        self.frm_1.grid(row=1, column=0, columnspan=4, sticky="w", padx=10)

        lbl_null_2 = tk.Label(self.frm_1, text="")
        lbl_null_2.grid(row=0, column=0)

        lbl_1 = tk.Label(self.frm_1, text="Начала периода:", font=("Arial Bold", 12))
        lbl_1.grid(row=1, column=0, sticky="e")

        self.entry_1 = tk.Entry(self.frm_1, font=("Arial Bold", 18), width=9)
        self.entry_1.grid(row=1, column=1)

        lbl_2 = tk.Label(self.frm_1, text="     Окончания периода:", font=("Arial Bold", 12))
        lbl_2.grid(row=1, column=2, sticky="e")

        self.entry_2 = tk.Entry(self.frm_1, font=("Arial Bold", 18), width=9)
        self.entry_2.grid(row=1, column=3)

        # Второй фрейм для строк и полей для текста
        lbl_null_3 = tk.Label(self, text="")
        lbl_null_3.grid(row=2, column=0)

        self.frm_2 = tk.LabelFrame(
            self,
            text="Даты формирования отчетов по количеству рекламаций",
            font=("Arial Bold", 14),
            labelanchor="n",
        )
        self.frm_2.grid(row=3, column=0, columnspan=4, sticky="w", padx=10)

        lbl_null_4 = tk.Label(self.frm_2, text="")
        lbl_null_4.grid(row=0, column=0)

        lbl_3 = tk.Label(self.frm_2, text="   Предыдущая:", font=("Arial Bold", 12))
        lbl_3.grid(row=1, column=0, sticky="e")

        self.entry_3 = tk.Entry(self.frm_2, font=("Arial Bold", 18), width=10)
        self.entry_3.grid(row=1, column=1)

        lbl_4 = tk.Label(self.frm_2, text="            Сегодняшняя:", font=("Arial Bold", 12))
        lbl_4.grid(row=1, column=2, sticky="e")

        self.entry_4 = tk.Entry(self.frm_2, font=("Arial Bold", 18), width=10)
        self.entry_4.grid(row=1, column=3)

        # Кнопка запуска создания отчета и записи его в файл
        lbl_null_5 = tk.Label(self, text="")
        lbl_null_5.grid(row=4, column=0)

        self.btn_1 = tk.Button(
            self,
            text="СОЗДАТЬ СПРАВКУ-ОТЧЕТ",
            font=("Arial bold", 12),
            fg="green",
            bg="linen",
            activebackground="peach puff",
            relief=tk.SUNKEN,
            command=self.on_button_click,
        )
        self.btn_1.grid(row=5, column=0, columnspan=4)

        # Поле для вывода текста о завершении
        lbl_null_6 = tk.Label(self, text="")
        lbl_null_6.grid(row=6, column=0)

        self.entry_5 = tk.Entry(self, font=("Arial Bold", 20), width=35, justify="center")
        self.entry_5.grid(row=7, column=0, columnspan=4)

        # Личная подпись
        for i in range(8, 10):
            lbl_null = tk.Label(self, text="")
            lbl_null.grid(row=i, column=0)

        lbl_5 = tk.Label(self, text="  Development by IGOR VASILENOK")
        lbl_5.grid(row=10, column=0, sticky="w")

        lbl_6 = tk.Label(self, text="v1_25-01-2025  ")
        lbl_6.grid(row=10, column=3, sticky="e")

    def make_result(self):
        """функция создания справки-отчета и записи его в файл"""

        obj = epm.WriteResult()

        indexend = obj.index_end
        dateend = obj.date_end

        self.entry_1.insert(0, indexend)
        self.entry_3.insert(0, dateend)

        obj.get_result()

        indexend_new = obj.index_end_new
        self.entry_2.insert(0, indexend_new)
        self.entry_4.insert(0, epm.date_end_new)

        obj.write_to_database()

        time.sleep(1)
        obj.write_to_txt()

        time.sleep(1)
        obj.write_to_excel()

    def on_button_click(self):
        """функция запуска создания отчета с изменением поведения кнопки в процессе"""

        self.btn_1.config(state="disabled", fg="black")

        try:
            self.make_result()

            entry_5 = tk.Entry(
                self,
                font=("Arial Bold", 20),
                width=35,
                justify="center",
                background="aquamarine",
            )
            entry_5.grid(row=7, column=0, columnspan=4)
            entry_5.insert(0, "Файл Excel со справкой записан!")

        except:
            messagebox.showinfo(
                "СООБЩЕНИЕ",
                "Возникла ОШИБКА в работе приложения!!!\n\n"
                "Возможно, отсутствуют данные для составления справки.\n"
                "Обратитесь к разработчику приложения!",
                parent=self
            )
            time.sleep(0.5)
            self.destroy()
