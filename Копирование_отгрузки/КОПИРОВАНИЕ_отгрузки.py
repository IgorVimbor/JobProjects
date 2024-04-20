import copyshipment
import tkinter as tk
from tkinter import messagebox
import tkinter.ttk as ttk
import time


def progress_line():
    # старт виджета загрузки
    window.update()
    progress_bar['value'] = 0
    window.update()

    while progress_bar['value'] < 170:
        progress_bar['value'] += 10
        window.update()
        time.sleep(0.5)

    # вызов класса Pre_copy копирования данных
    pr = copyshipment.Pre_copy()

    pr.copy_in_otk(3, 18, 1)     # ТКР
    pr.copy_in_otk(20, 34, 2)    # ПК
    pr.copy_in_otk(36, 48, 3)    # ВН
    pr.copy_in_otk(50, 61, 4)    # МН
    pr.copy_in_otk(63, 69, 5)    # ГП
    pr.copy_in_otk(71, 82, 6)    # ЦМФ
    pr.copy_in_otk(103, 107, 4)  # штанга и коромысло

    # продолжение работы виджета загрузки
    while progress_bar['value'] < 200:
        progress_bar['value'] += 10
        window.update()
        time.sleep(0.5)

    # вывод информационного окна о сохранении отчета
    messagebox.showinfo('СООБЩЕНИЕ', 'Процесс копирования завершен.\n\n'
                                     'Для сохранения информации нажмите ОК\n'
                                     'и далее СОХРАНИТЬ в основном окне.')


def get_save():
    # вызов класса Copy_value для копирования значений
    grp = copyshipment.Copy_value()
    grp.copy_garant()

    # вывод информационного окна о сохранении данных
    messagebox.showinfo('ИНФОРМАЦИЯ', 'Сохранение данных по отгрузке\n'
                                      'и расчет гарантийного парка завершены.\n\n'
                                      'Нажмите ОК и далее ЗАКРЫТЬ ОКНО.')


def close_window():
    window.destroy()


window = tk.Tk()

# Создается окно с заголовком
# меняем логотип Tkinter (перышко) на свой логотип
window.iconbitmap(
    '//Server/otk/Support_files_не_удалять!!!/Значки_Логотипы/IconGreen.ico')
# название заголовка в окне приложения
window.title('КОПИРОВАНИЕ ДАННЫХ ПО ОТГРУЗКЕ ИЗ ТАБЛИЦЫ ОСиМ')
window.geometry('700x320')    # размер окна приложения

# Пустая строка перед фреймом
lbl_null_1 = tk.Label(text='')
lbl_null_1.pack()

# Создается ПЕРВАЯ рамка frm_form_1 для размещения рамок frame1 и frame2
frm_form_1 = tk.Frame(relief=tk.SUNKEN, borderwidth=3)
frm_form_1.pack()

# Создается рамка frame1
frame1 = tk.Frame(master=frm_form_1, relief=tk.SUNKEN,
                  borderwidth=3, width=300, height=270, bg="white")
frame1.pack(fill=tk.BOTH, side=tk.LEFT)

# Создается рамка frame2
frame2 = tk.Frame(master=frm_form_1, relief=tk.SUNKEN,
                  borderwidth=3, width=300, bg="white")
frame2.pack(fill=tk.BOTH, side=tk.LEFT)

# Заполняем рамку frame1
lbl_1 = tk.Label(master=frame1, text='Проверьте место расположения и правильность\n'
                                     'наименования файлов ОСиМ и ОТК.\n\n'
                                     'ВНИМАНИЕ!\n'
                                     'Файлы должны иметь расширение .xlsx\n\n'
                                     'После проверки нажмите КОПИРОВАТЬ.', justify='left', font=("Arial Bold", 10), bg="white")
lbl_1.grid(row=0, column=0, padx=5, sticky="w")

# Заполняем рамку frame2
lbl_2 = tk.Label(master=frame2, text='Папка:\n'
                                     '      otk на Server\n'
                                     '      ОТЧЕТНОСТЬ БЗА\n'
                                     '      ОТГРУЗКА+ГАРАНТИЙНЫЙ ПАРК\n'
                                     'Файлы:\n'
                                     '      Отгрузка для ОТК_текущий год.xlsx\n'
                                     '      ОТГРУЗКА+ГАРАНТИЙНЫЙ ПАРК_текущий год.xlsx', justify='left', font=("Arial Bold", 10), bg="white")
lbl_2.grid(row=0, column=0, padx=5, sticky="w")

# Пустая строка перед следующей рамкой
lbl_null_2 = tk.Label(text='')
lbl_null_2.pack()

# Создает ВТОРУЮ рамку frm_buttons для размещения кнопки кнопки "КОПИРОВАТЬ" и "СОХРАНИТЬ"
frm_buttons_1 = tk.Frame(master=window, relief=tk.SUNKEN, borderwidth=3)
frm_buttons_1.pack()

bnt_1 = tk.Button(master=frm_buttons_1, text='КОПИРОВАТЬ', font=(
    "Arial Bold", 10), fg="green", command=progress_line)
bnt_2 = tk.Button(master=frm_buttons_1, text='СОХРАНИТЬ', font=(
    "Arial Bold", 10), fg="green", command=get_save)
bnt_2.pack(side=tk.RIGHT, padx=10, ipadx=10)
bnt_1.pack(side=tk.RIGHT, padx=10)

# Пустая строка перед следующей рамкой
lbl_null_3 = tk.Label(text='')
lbl_null_3.pack()

# Создается ТРЕТЬЯ рамка frm_form_3 для размещения индикатора загрузки
frm_form_3 = tk.Frame(relief=tk.SUNKEN, borderwidth=3)
frm_form_3.pack()

# Создается виджет индикатора загрузки
progress_bar = ttk.Progressbar(
    frm_form_3, orient="horizontal", mode="determinate", length=500, maximum=200, value=0)
lbl_3 = tk.Label(frm_form_3, text="Процесс копирования")

lbl_3.grid(row=0, column=0)
progress_bar.grid(row=0, column=1)

# Пустая строка перед следующей рамкой
lbl_null_3 = tk.Label(text='')
lbl_null_3.pack()

# Создается ЧЕТВЕРТАЯ рамка frm_buttons_2 для размещения кнопки "ЗАКРЫТЬ ОКНО"
frm_buttons_2 = tk.Frame(master=window, relief=tk.SUNKEN, borderwidth=3)
frm_buttons_2.pack()

bnt_2 = tk.Button(master=frm_buttons_2, text='ЗАКРЫТЬ ОКНО', font=(
    "Arial Bold", 10), fg="red", command=close_window)
bnt_2.pack(side=tk.RIGHT, padx=10)

window.mainloop()
