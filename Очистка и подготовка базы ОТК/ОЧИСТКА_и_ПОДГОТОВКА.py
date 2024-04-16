import tkinter as tk
import allclassotk as otk
from tkinter import messagebox
import tkinter.ttk as ttk
import time


def get_clear():
    # старт виджета загрузки
    window.update()
    progress_bar['value'] = 0
    window.update()

    while progress_bar['value'] < 70:
        progress_bar['value'] += 10
        window.update()
        time.sleep(0.5)

    # вызов классов Clear_list и Copy_and_clear_gp модуля allclassotk
    cl = otk.Clear_list()
    cl.start_clear()
    clgp = otk.Copy_and_clear_gp()
    clgp.start_all_gp()

    # вывод информационного окна о сохранении отчета
    messagebox.showinfo('СООБЩЕНИЕ', 'Процесс очистки завершен.\n\n'
                                     'Для сохранения информации нажмите ОК\n'
                                     'и далее СОХРАНИТЬ в основном окне.')


def get_save():
    # продолжение работы виджета загрузки
    while progress_bar['value'] < 100:
        progress_bar['value'] += 10
        window.update()
        time.sleep(0.5)

    # вывод информационного окна о сохранении данных
    messagebox.showinfo('ИНФОРМАЦИЯ', 'Изменная таблица сохранена.\n'
                                      'Нажмите ОК и ЗАКРОЙТЕ программу.')


window = tk.Tk()

# Создается окно с заголовком
# меняем логотип Tkinter (перышко) на свой логотип
window.iconbitmap(
    '//Server/otk/Support_files_не_удалять!!!/Значки_Логотипы/IconYellow.ico')
# название заголовка в окне приложения
window.title('ОЧИСТКА ДАННЫХ ПО ОТГРУЗКЕ В ТАБЛИЦЕ ОТК')
# размер окна приложения
window.geometry('520x320')

# Пустая строка перед фреймом
lbl_null_1 = tk.Label(text='')
lbl_null_1.pack()

# Создается рамка frm_form_1 для размещения поля с текстом
frm_form_1 = tk.Frame(relief=tk.SUNKEN, borderwidth=3)
frm_form_1.pack()

# Заполняем рамку frm_form_1
lbl_1 = tk.Label(master=frm_form_1, text='Программа произведет очистку данных на всех листах,\n'
                 'переименует листы и таблицы на СЛЕДУЮЩИЙ ГОД, подготовит\n'
                 'таблицы на листе "Гарантийный парк" к работе в следующем году.\n\n'
                 'ВНИМАНИЕ!\n'
                 'Допускается только однократный запуск программы!\n'
                 'В случае повторного запуска год на всех листах будет увеличен!\n\n'
                 'Файл, который будет очищен:\n'
                 'ОТГРУЗКА+ГАРАНТИЙНЫЙ ПАРК_текущий год.xlsx', justify='left', font=("Arial Bold", 10), bg="white")
lbl_1.grid(row=0, column=0, padx=5, sticky="w")

# Пустая строка перед фреймом
lbl_null_2 = tk.Label(text='')
lbl_null_2.pack()

# Создается рамка frm_form_3 для размещения индикатора загрузки
frm_form_3 = tk.Frame(relief=tk.SUNKEN, borderwidth=3)
frm_form_3.pack()

# Создается виджет индикатора загрузки
progress_bar = ttk.Progressbar(
    frm_form_3, orient="horizontal", mode="determinate", length=350, maximum=100, value=0)
lbl_3 = tk.Label(frm_form_3, text="Процесс очистки")

lbl_3.grid(row=0, column=0)
progress_bar.grid(row=0, column=1)

# Пустая строка перед фреймом
lbl_null_3 = tk.Label(text='')
lbl_null_3.pack()

# Создает рамку frm_buttons для размещения кнопки кнопки "ОЧИСТИТЬ" и "СОХРАНИТЬ"
frm_buttons_1 = tk.Frame(master=window, relief=tk.SUNKEN, borderwidth=3)
frm_buttons_1.pack()

bnt_1 = tk.Button(master=frm_buttons_1, text='ОЧИСТИТЬ ТАБЛИЦУ', font=(
    "Arial Bold", 10), fg="green", command=get_clear)
bnt_2 = tk.Button(master=frm_buttons_1, text='СОХРАНИТЬ',
                  font=("Arial Bold", 10), fg="red", command=get_save)
bnt_2.pack(side=tk.RIGHT, padx=10, ipadx=10)
bnt_1.pack(side=tk.RIGHT, padx=10)

window.mainloop()
