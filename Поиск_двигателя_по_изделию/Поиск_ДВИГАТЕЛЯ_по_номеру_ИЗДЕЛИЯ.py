import tkinter as tk
import dvig_to_product as dvg
from tkinter import messagebox


def out_value(): # возвращает номер года и строку номеров изделий из строк ввода информации
    god = ent_god.get()     # получение текста из строки ввода года
    if not god:
        messagebox.showinfo('ОШИБКА', 'Не введен год поиска')
    prods = ent_dvig.get()  # получение текста из строки ввода номеров изделий
    return god, prods       # возвращаем номер года и строку номеров изделий

def get_itog():   # функция выборки из базы и вывода на экран (на базе модуля dvig_to_product)
    god, prods = out_value()   # номер года и строка номеров изделий
    pr = dvg.Search(god)       # создаем экземпляр класса из импортированного модуля
    text_1.insert(1.0, f"{'-'*50}\n")   # декоративная строка
    for prod in prods.split():
        prod = str(int(prod))  # переводим в int и обратно в str для удаления незначащих нулей в вводимых номерах изделий
        if pr.get_answer(prod):
            res, vid, dvig, act = pr.get_answer(prod)
            text_1.insert(1.0, f'Двигатель № {dvig}, акт рекламации № {act}\n')
            text_1.insert(1.0, f'Изделие № {prod} - {vid} - cтрока {res+3}\n')
            text_1.insert(1.0, f"{'-'*50}\n")  # декоративная строка
        else:
            text_1.insert(1.0, f'Изделия № {prod} нет в базе {god} года\n')
            text_1.insert(1.0, f"{'-'*50}\n")  # декоративная строка

def clear_strok():  # функция очистки строк ввода года и номеров изделий
    god, prods = out_value()
    if god:
        ent_god.delete(0, tk.END)
    if prods:
        ent_dvig.delete(0, tk.END)

def clear_res():  # функция очистки поля вывода результата
    text_1.delete('1.0', tk.END)


window = tk.Tk()

# Создается окно с заголовком
window.iconbitmap('//Server/otk/1 ГАРАНТИЯ на сервере/ЗНАЧКИ_Логотипы/IconGray_oval.ico')  # меняем логотип Tkinter
window.title('ПОИСК ДВИГАТЕЛЯ В БАЗЕ РЕКЛАМАЦИЙ ПО НОМЕРУ ИЗДЕЛИЯ')  # название заголовка в окне приложения
window.geometry('500x400')  # размер окна приложения (ширина-высота)

# Делаем окно растягивающимся с центрированием по центру
window.columnconfigure(0, weight=1, minsize=250)
window.rowconfigure([0, 10], weight=1, minsize=100)

# Пустая строка перед фреймом
lbl_null_0 = tk.Label(text='')
lbl_null_0.pack()

# Создается рамка `frm_form` для ярлыка с текстом и полей для ввода информации.
frm_form = tk.Frame(relief=tk.SUNKEN, borderwidth=3)
frm_form.pack()

# ЗАПОЛНЯЕМ ПЕРВЫЙ ФРЕЙМ
lbl = tk.Label(master=frm_form, text='1. Введите ГОД в котором будем искать номер двигателя:   ', font=("Arial Bold", 10))
ent_god = tk.Entry(master=frm_form, width=15)

# Используем менеджер геометрии grid для размещения ярлыков и поля ввода номеров изделий
lbl.grid(row=0, column=0, sticky='w')
ent_god.grid(row=0, column=1, sticky='w')

# Пустая строка между фреймами
lbl_null = tk.Label(text='')
lbl_null.pack()

# Создается новая рамка `frm_form_1` для ярлыков с текстом и полей для ввода информации.
frm_form_1 = tk.Frame(relief=tk.SUNKEN, borderwidth=3)
frm_form_1.pack()

# ЗАПОЛНЯЕМ ВТОРОЙ ФРЕЙМ
lbl_dvig_3 = tk.Label(master=frm_form_1, text='2. Введите через пробел номера ИЗДЕЛИЙ и нажмите НАЧАТЬ ПОИСК.',
                      font=("Arial Bold", 10))
ent_dvig = tk.Entry(master=frm_form_1, width=80)

# Используем менеджер геометрии grid для размещения ярлыков и поля ввода номеров изделий
lbl_dvig_3.grid(row=4, column=0, sticky='w')
ent_dvig.grid(row=5, column=0)

# Создает новую рамку frm_buttons для размещения кнопок НАЧАТЬ ПОИСК и ОЧИСТИТЬ СТРОКУ
frm_buttons = tk.Frame()
frm_buttons.pack(fill=tk.X, ipadx=5, ipady=5)
bnt_1 = tk.Button(master=frm_buttons, text='НАЧАТЬ ПОИСК', font=("Arial Bold", 10), command=get_itog)
bnt_2 = tk.Button(master=frm_buttons, text='ОЧИСТИТЬ СТРОКИ', font=("Arial Bold", 10), command=clear_strok)
bnt_2.pack(side=tk.RIGHT, ipadx=10)
bnt_1.pack(side=tk.RIGHT, padx=10, ipadx=10)

# Пустая строка между фреймами
lbl_null_4 = tk.Label(text='')
lbl_null_4.pack()

# Создается новая рамка frm_form_2 для ярлыков с текстом и поля для вывода результата
frm_form_2 = tk.Frame(relief=tk.SUNKEN, borderwidth=3)
frm_form_2.pack()


# ЗАПОЛНЯЕМ ТРЕТИЙ ФРЕЙМ
lbl_2 = tk.Label(master=frm_form_2, text='3. РЕЗУЛЬТАТ ПОИСКА:', font=("Arial Bold", 10))
text_1 = tk.Text(master=frm_form_2, width=69, height=8, background='white', font=("Arial Bold", 10))
lbl_4 = tk.Label(master=frm_form_2, text='')   # пустая строка

# Используем менеджер геометрии grid для размещения ярлыков и поля вывода результата
lbl_2.grid(row=0, column=0, sticky='w')
text_1.grid(row=1, column=0)
lbl_4.grid(row=3, column=0)

# Создает новую рамку frm_buttons_2 для размещения кнопок СДЕЛАТЬ ОТЧЕТ и СБРОСИТЬ РЕЗУЛЬТАТ
frm_buttons_2 = tk.Frame()
frm_buttons_2.pack(fill=tk.X, ipadx=5, ipady=5)
bnt_4 = tk.Button(master=frm_buttons_2, text='СБРОСИТЬ РЕЗУЛЬТАТ', font=("Arial Bold", 10), command=clear_res)
bnt_4.pack(side=tk.RIGHT, ipadx=10)

window.mainloop()
