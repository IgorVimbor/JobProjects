import tkinter as tk
from tkinter import messagebox

import engine_search.engine_search_modul as dvg


class SearchEngine(tk.Toplevel):
    def __init__(self, master=None):
        super().__init__(master)

        self.iconbitmap('app_total/IconBZA.ico')  # меняем логотип Tkinter
        self.title('ПОИСК ДВИГАТЕЛЯ ПО НОМЕРУ ИЗДЕЛИЯ')
        self.geometry('500x400')  # размер окна приложения (ширина-высота)

        # Делаем окно растягивающимся с центрированием по центру
        self.columnconfigure(0, weight=1, minsize=250)
        self.rowconfigure([0, 10], weight=1, minsize=100)

        # Пустая строка перед фреймом
        lbl_null_0 = tk.Label(self, text='')
        lbl_null_0.pack()

        # Создается рамка `frm_form` для ярлыка с текстом и полей для ввода информации.
        self.frm_form = tk.Frame(self, relief=tk.SUNKEN, borderwidth=3)
        self.frm_form.pack()

        # ЗАПОЛНЯЕМ ПЕРВЫЙ ФРЕЙМ
        lbl = tk.Label(master=self.frm_form,
                       text='1. Введите ГОД в котором будем искать номер двигателя:   ', font=("Arial Bold", 10))
        self.ent_god = tk.Entry(master=self.frm_form, width=15)

        # Используем менеджер геометрии grid для размещения ярлыков и поля ввода номеров изделий
        lbl.grid(row=0, column=0, sticky='w')
        self.ent_god.grid(row=0, column=1, sticky='w')

        # Пустая строка между фреймами
        lbl_null = tk.Label(self, text='')
        lbl_null.pack()

        # Создается новая рамка `frm_form_1` для ярлыков с текстом и полей для ввода информации.
        self.frm_form_1 = tk.Frame(self, relief=tk.SUNKEN, borderwidth=3)
        self.frm_form_1.pack()

        # ЗАПОЛНЯЕМ ВТОРОЙ ФРЕЙМ
        lbl_dvig_3 = tk.Label(master=self.frm_form_1, text='2. Введите через пробел номера ИЗДЕЛИЙ и нажмите НАЧАТЬ ПОИСК.',
                              font=("Arial Bold", 10))
        self.ent_dvig = tk.Entry(master=self.frm_form_1, width=80)

        # Используем менеджер геометрии grid для размещения ярлыков и поля ввода номеров изделий
        lbl_dvig_3.grid(row=4, column=0, sticky='w')
        self.ent_dvig.grid(row=5, column=0)

        # Создает новую рамку frm_buttons для размещения кнопок НАЧАТЬ ПОИСК и ОЧИСТИТЬ СТРОКУ
        self.frm_buttons = tk.Frame(self)
        self.frm_buttons.pack(fill=tk.X, ipadx=5, ipady=5)
        self.bnt_1 = tk.Button(master=self.frm_buttons, text='НАЧАТЬ ПОИСК',
                               font=("Arial Bold", 10), command=self.get_itog)
        self.bnt_2 = tk.Button(master=self.frm_buttons, text='ОЧИСТИТЬ СТРОКИ',
                               font=("Arial Bold", 10), command=self.clear_strok)
        self.bnt_2.pack(side=tk.RIGHT, ipadx=10)
        self.bnt_1.pack(side=tk.RIGHT, padx=10, ipadx=10)

        # Пустая строка между фреймами
        lbl_null_4 = tk.Label(self, text='')
        lbl_null_4.pack()

        # Создается новая рамка frm_form_2 для ярлыков с текстом и поля для вывода результата
        self.frm_form_2 = tk.Frame(self, relief=tk.SUNKEN, borderwidth=3)
        self.frm_form_2.pack()

        # ЗАПОЛНЯЕМ ТРЕТИЙ ФРЕЙМ
        lbl_2 = tk.Label(master=self.frm_form_2, text='3. РЕЗУЛЬТАТ ПОИСКА:',
                         font=("Arial Bold", 10))
        self.text_1 = tk.Text(master=self.frm_form_2, width=69, height=8,
                              background='white', font=("Arial Bold", 10))
        lbl_4 = tk.Label(master=self.frm_form_2, text='')   # пустая строка

        # Используем менеджер геометрии grid для размещения ярлыков и поля вывода результата
        lbl_2.grid(row=0, column=0, sticky='w')
        self.text_1.grid(row=1, column=0)
        lbl_4.grid(row=3, column=0)

        # Создает новую рамку frm_buttons_2 для размещения кнопок СДЕЛАТЬ ОТЧЕТ и СБРОСИТЬ РЕЗУЛЬТАТ
        self.frm_buttons_2 = tk.Frame(self)
        self.frm_buttons_2.pack(fill=tk.X, ipadx=5, ipady=5)
        self.bnt_4 = tk.Button(master=self.frm_buttons_2, text='СБРОСИТЬ РЕЗУЛЬТАТ',
                               font=("Arial Bold", 10), command=self.clear_res)
        self.bnt_4.pack(side=tk.RIGHT, ipadx=10)

    def out_value(self):
        """возвращает номер года и строку номеров изделий из строк ввода информации"""
        god = self.ent_god.get()     # получение текста из строки ввода года

        if not god:
            messagebox.showinfo('ОШИБКА', 'Не введен год поиска', parent=self)

        prods = self.ent_dvig.get()  # получение текста из строки ввода номеров изделий
        return god, prods       # возвращаем год и строку номеров изделий

    def get_itog(self):
        """функция выборки из базы и вывода на экран (на базе модуля dvig_to_product)"""
        self.text_1.insert(1.0, f"{'-'*50}\n")   # декоративная строка

        god, prods = self.out_value()   # год и номера изделий
        # создаем экземпляр класса из импортированного модуля
        pr = dvg.Search(god)

        for prod in prods.split():
            try:
                # переводим в int и обратно в str для удаления незначащих нулей в вводимых номерах изделий
                prod = str(int(prod))
            except ValueError:
                self.text_1.insert(1.0, f'Некорректный номер изделия: {prod}\n')
                continue
            if pr.get_answer(prod):
                res, vid, dvig, act = pr.get_answer(prod)
                self.text_1.insert(1.0, f'Двигатель № {dvig}, акт рекламации № {act}\n')
                self.text_1.insert(1.0, f'Изделие № {prod} - {vid} - cтрока {res+3}\n')
                self.text_1.insert(1.0, f"{'-'*50}\n")  # декоративная строка
            else:
                self.text_1.insert(1.0, f'Изделия № {prod} нет в базе {god} года\n')
                self.text_1.insert(1.0, f"{'-'*50}\n")  # декоративная строка

    def clear_strok(self):
        """функция очистки строк ввода года и номеров изделий"""
        god, prods = self.out_value()

        if god:
            self.ent_god.delete(0, tk.END)
        if prods:
            self.ent_dvig.delete(0, tk.END)

    def clear_res(self):
        """функция очистки поля вывода результата"""
        self.text_1.delete('1.0', tk.END)
