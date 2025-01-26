# Основной исполняемый модуль

import tkinter as tk
from tkinter import messagebox
import tkinter.ttk as ttk
import time


def on_button_click():
    """функция запуска создания отчета и записи его в файл с изменением поведения кнопки в процессе"""

    # делаем НЕ активной кнопку "СОЗДАТЬ ОТЧЕТ" и изменяем цвет текста кнопки
    btn_1.config(state="disabled", fg="black")


# -------------------------- Создание окна приложения с заголовком ----------------------------
window = tk.Tk()

# меняем логотип Tkinter (перышко) на свой логотип
window.iconbitmap("IconBZA.ico")
# название заголовка в окне приложения
window.title("ПОДГОТОВКА СПРАВКИ О КОЛИЧЕСТВЕ РЕКЛАМАЦИЙ ЗА ПЕРИОД")
# размер окна приложения
width = 578  # ширина окна
heigh = 380  # высота окна
# определяем координаты центра экрана и размещаем окно
screenwidth = window.winfo_screenwidth()
screenheight = window.winfo_screenheight()
window.geometry(
    "%dx%d+%d+%d"
    % (width, heigh, (screenwidth - width) / 2, (screenheight - heigh) / 3)
)


# ---------------------- Первый фрейм для строк и полей для текста ------------------------
# пустая строка
lbl_null_1 = tk.Label(window, text="")
lbl_null_1.grid(row=0, column=0)

# формируем и размещаем первый фрейм для строк и полей для текста
frm_1 = tk.LabelFrame(
    window,
    text="Номера строк базы рекламаций ОТК",
    font=("Arial Bold", 14),
    labelanchor="n",
)
frm_1.grid(row=1, column=0, columnspan=4, sticky="w", padx=10)

# пустая строка
lbl_null_2 = tk.Label(frm_1, text="")
lbl_null_2.grid(row=0, column=0)

# формируем и размещаем во фрейме строку с текстом "Начала периода:"
lbl_1 = tk.Label(frm_1, text="Начала периода:", font=("Arial Bold", 12))
lbl_1.grid(row=1, column=0, sticky="e")

# формируем и размещаем поле для вывода номера строки
entry_1 = tk.Entry(frm_1, font=("Arial Bold", 20), width=8)
entry_1.grid(row=1, column=1)

# формируем и размещаем во фрейме строку с текстом "Окончания периода:"
lbl_2 = tk.Label(frm_1, text="      Окончания периода:", font=("Arial Bold", 12))
lbl_2.grid(row=1, column=2, sticky="e")

# формируем и размещаем поле для вывода номера строки
entry_2 = tk.Entry(frm_1, font=("Arial Bold", 20), width=8)
entry_2.grid(row=1, column=3)


# ---------------------- Второй фрейм для строк и полей для текста ------------------------
# пустая строка
lbl_null_3 = tk.Label(window, text="")
lbl_null_3.grid(row=2, column=0)

# формируем и размещаем второй фрейм для строк и полей для текста
frm_2 = tk.LabelFrame(
    window,
    text="Даты формирования отчетов по количеству рекламаций",
    font=("Arial Bold", 14),
    labelanchor="n",
)
frm_2.grid(row=3, column=0, columnspan=4, sticky="w", padx=10)

# пустая строка
lbl_null_4 = tk.Label(frm_2, text="")
lbl_null_4.grid(row=0, column=0)

# формируем и размещаем во фрейме строку с текстом "Предыдущая:"
lbl_3 = tk.Label(frm_2, text="      Предыдущая:", font=("Arial Bold", 12))
lbl_3.grid(row=1, column=0, sticky="e")

# формируем и размещаем поле для вывода номера строки
entry_3 = tk.Entry(frm_2, font=("Arial Bold", 20), width=9)
entry_3.grid(row=1, column=1)

# формируем и размещаем во фрейме строку с текстом "Сегодняшняя:"
lbl_4 = tk.Label(frm_2, text="          Сегодняшняя:", font=("Arial Bold", 12))
lbl_4.grid(row=1, column=2, sticky="e")

# формируем и размещаем поле для вывода номера строки
entry_4 = tk.Entry(frm_2, font=("Arial Bold", 20), width=9)
entry_4.grid(row=1, column=3)


# ----------------- Кнопка запуска создания отчета и записи его в файл ----------------
# пустая строка
lbl_null_5 = tk.Label(window, text="")
lbl_null_5.grid(row=4, column=0)

# Создаем кнопку "СОЗДАТЬ ОТЧЕТ"
btn_1 = tk.Button(
    window,
    text="СОЗДАТЬ СПРАВКУ-ОТЧЕТ",
    font=("Arial Bold", 12),
    fg="green",
    bg="linen",  # цвет фона кнопки
    activebackground="peach puff",  # цвет кнопки при нажатии на нее
    relief=tk.SUNKEN,
    command=on_button_click,
)
btn_1.grid(row=5, column=0, columnspan=4)


# ----------------------- Поле для вывода текста о завершении ---------------------------
# пустая строка
lbl_null_6 = tk.Label(window, text="")
lbl_null_6.grid(row=6, column=0)

# создаем поле для вывода текста "Справка о количестве дефектов за период готова!"
entry_5 = tk.Entry(font=("Arial Bold", 20), width=35)
entry_5.grid(row=7, column=0, columnspan=4)

# ------------------------------ Личная подпись -----------------------------------------
# пустые строки
for i in range(8, 10):
    lbl_null = tk.Label(window, text="")
    lbl_null.grid(row=i, column=0)

# lbl_4 = tk.Label(text="Интелектуальная собственность IGOR VASILENOK")
lbl_5 = tk.Label(window, text="  Development by IGOR VASILENOK")
lbl_5.grid(row=10, column=0, sticky="w")

lbl_6 = tk.Label(window, text="v1_25-01-2025  ")
lbl_6.grid(row=10, column=3, sticky="e")

window.mainloop()
