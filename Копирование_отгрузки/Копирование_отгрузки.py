import tkinter as tk
from tkinter import messagebox
import tkinter.ttk as ttk
import time

import modul_copier


def data_copier():
    """функция копирования отгрузки из файла ОСиМ в файл ОТК на Лист конкретного месяца,
    а затем на лист "Гарантийный парк" и лист "Данные2" файла отчета"""

    # копируем отгрузку из файла ОСиМ в файл ОТК на Лист конкретного месяца
    pr = modul_copier.ExcelSheetCopier()

    pr.copy_in_otk(3, 21, 1)  # ТКР
    progress_bar["value"] += 10  # изменяем виджет загрузки
    window.update()
    pr.copy_in_otk(23, 40, 2)  # ПК
    progress_bar["value"] += 10  # изменяем виджет загрузки
    window.update()
    pr.copy_in_otk(42, 59, 3)  # ВН
    progress_bar["value"] += 10  # изменяем виджет загрузки
    window.update()
    pr.copy_in_otk(61, 75, 4)  # МН
    progress_bar["value"] += 10  # изменяем виджет загрузки
    window.update()
    pr.copy_in_otk(77, 83, 5)  # ГП
    progress_bar["value"] += 10  # изменяем виджет загрузки
    window.update()
    pr.copy_in_otk(85, 96, 6)  # ЦМФ
    progress_bar["value"] += 10  # изменяем виджет загрузки
    window.update()
    pr.copy_in_otk(110, 114, 11)  # штанга и коромысло
    progress_bar["value"] += 10  # изменяем виджет загрузки
    window.update()

    # копируем отгрузку по потребителям и изделиям на лист "Гарантийный парк" и лист "Данные2" файла отчета
    grp = modul_copier.DataCopierGarant()
    grp.copy_garant()
    progress_bar["value"] += 10  # изменяем виджет загрузки
    window.update()

    progress_bar["value"] = 100  # изменяем виджет загрузки
    window.update()

    time.sleep(1)


def on_button_click():
    """функция запуска копирования и изменения поведения кнопки в процессе копирования"""

    # делаем НЕ активной кнопку "КОПИРОВАТЬ" на время копирования и изменяем цвет текста кнопки
    bnt_1.config(state="disabled", fg="black")

    # попытка копирования данных по отгрузке
    try:
        data_copier()  # запускаем функцию копирования данных

        # возвращаем кнопку "КОПИРОВАТЬ" в активное состояние
        bnt_1.config(state="normal", fg="green")
        time.sleep(0.5)

        # информируем пользователя об успешном завершении копирования и предлагаем закрыть приложение
        result = messagebox.askyesno(
            "СООБЩЕНИЕ",
            "Данные по отгрузке скопированы в файлы ОТК.\n\nЗакрыть программу?",
        )
        if result:  # если ЕСТЬ согласие на закрытие программы
            time.sleep(0.5)
            window.destroy()  # закрываем приложение
        else:  # если НЕТ согласия
            progress_bar["value"] = 0  # обнуляем виджет загрузки

    # если возникла ошибка при копировании данных - выводим информационное окно и закрываем приложение
    except:
        messagebox.showinfo(
            "СООБЩЕНИЕ",
            "Возникла ОШИБКА при копировании!!!\n\n"
            "Закройте программу и проверьте исходные файлы.\n"
            "Файлы должны иметь расширение .xlsx.",
        )
        time.sleep(0.5)
        window.destroy()  # закрываем приложение


window = tk.Tk()

# Создается окно с заголовком
# меняем логотип Tkinter (перышко) на свой логотип
window.iconbitmap("IconGreen.ico")
# название заголовка в окне приложения
window.title("КОПИРОВАНИЕ ДАННЫХ ПО ОТГРУЗКЕ В ФАЙЛЫ ОТК")
# размер окна приложения
width = 710  # ширина окна
heigh = 380  # высота окна
# определяем координаты центра экрана и размещаем окно
screenwidth = window.winfo_screenwidth()
screenheight = window.winfo_screenheight()
window.geometry(
    "%dx%d+%d+%d"
    % (width, heigh, (screenwidth - width) / 2, (screenheight - heigh) / 3)
)

# Пустая строка перед фреймом
lbl_null_1 = tk.Label(text="")
lbl_null_1.pack()

# Создается ПЕРВАЯ рамка frm_form_1 для размещения рамок frame1 и frame2
frm_form_1 = tk.Frame(relief=tk.SUNKEN, borderwidth=3)
frm_form_1.pack()

# Создается рамка frame1
frame1 = tk.Frame(
    master=frm_form_1,
    relief=tk.SUNKEN,
    borderwidth=3,
    width=300,
    height=270,
    bg="white",
)
frame1.pack(fill=tk.BOTH, side=tk.LEFT)

# Создается рамка frame2
frame2 = tk.Frame(
    master=frm_form_1, relief=tk.SUNKEN, borderwidth=3, width=300, bg="white"
)
frame2.pack(fill=tk.BOTH, side=tk.LEFT)

# Заполняем рамку frame1
lbl_1 = tk.Label(
    master=frame1,
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
    master=frame2,
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
lbl_null_2 = tk.Label(text="")
lbl_null_2.pack()

# Создаем кнопку "КОПИРОВАТЬ"
bnt_1 = tk.Button(
    text="КОПИРОВАТЬ",
    font=("Arial Bold", 12),
    fg="green", 
    bg="linen",  # цвет фона кнопки
    activebackground="peach puff",  # цвет кнопки при нажатии на нее
    relief=tk.SUNKEN,
    command=on_button_click,
)
bnt_1.pack(padx=10)

# Пустая строка перед следующей рамкой
lbl_null_3 = tk.Label(text="")
lbl_null_3.pack()

# Создается ТРЕТЬЯ рамка frm_form_3 для размещения индикатора загрузки
frm_form_3 = tk.Frame(relief=tk.SUNKEN, borderwidth=3)
frm_form_3.pack()

# Создается виджет индикатора загрузки
progress_bar = ttk.Progressbar(
    frm_form_3,
    orient="horizontal",
    mode="determinate",
    length=500,
    maximum=100,
    value=0,
)
lbl_3 = tk.Label(frm_form_3, text="Процесс копирования")

lbl_3.grid(row=0, column=0)
progress_bar.grid(row=0, column=1)

# Пустые строки
for _ in range(3):
    lbl_null = tk.Label(text="")
    lbl_null.pack()


# ------------------------------ Личная подпись -----------------------------------------
lbl_4 = tk.Label(text="Development by IGOR VASILENOK  ")
lbl_4.pack(side=tk.RIGHT)


window.mainloop()

# pyinstaller --onefile --windowed --icon=IconGreen.ico Копирование_отгрузки.py
