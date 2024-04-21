# ВЕРСИЯ 3
# Создана общая база данных - файл "Резервное копирование_база данных.txt", в который записывается словарь .json
# В базе данных по ключу "files" хранится перечень файлов для копирования, по ключу "dirs" - перечень каталогов.

import json
import time
import tkinter as tk
import tkinter.ttk as ttk
import tkinter.filedialog as fd
from tkinter import messagebox
from modul_copyfile_v2 import Copy_file

# база данных - перечень резервных копий файлов и каталогов
# располагается в каталоге проекта или приложения
database = "Резервное копирование_база данных.txt"

try:  # если база данных уже существует
    # открываем базу данных, считываем файл json и сохраняем словарь в переменную
    with open(database, encoding="utf-8-sig") as file:
        data: dict = json.load(file)
except:  # если базы данных нет - создаем
    data = {"files": [], "dirs": []}
    with open(database, "w", encoding="utf-8-sig") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


class ListFrame(tk.Frame):
    def __init__(self, master, width, height, key):
        super().__init__(master)  # наследуемся от tk.Frame
        self._width = width  # ширина виджета
        self._height = height  # высота виджета
        self.key = key  # ключи из файла json ("files" или "dirs")

        # создаем объект Listbox и в нем объект Scrollbar с прокруткой (скроллингом)
        self.listbox = tk.Listbox(self)
        self.scroll = tk.Scrollbar(self, orient=tk.VERTICAL, command=self.listbox.yview)
        # указываем размеры объекта Listbox
        self.listbox.config(width=self._width, height=self._height)
        # сохраняем размещение объектов Listbox и Scrollbar во фрейме
        self.listbox.pack(side=tk.LEFT)
        self.scroll.pack(side=tk.LEFT, fill=tk.Y)

        # добавляем в объект Listbox перечень файлов для копирования или каталогов
        if key == "files":
            self.listbox.insert(0, *[i.split("/")[-1] for i in data[self.key]])
        else:
            self.listbox.insert(0, *[i for i in data[self.key]])

    def insert_to_listbox(self, item):
        """функция для добавления файла в перечень файлов объекта Listbox и базу данных"""
        if self.key == "files":  # если выбран файл
            # добавляем новый файл в конец перечня файлов объекта Listbox
            self.listbox.insert(tk.END, item.split("/")[-1])
            # добавляем новый файл в базу данных по ключу словаря
            data[self.key].append(item + "\n")
        else:  # если выбран каталог
            # добавляем новый каталог в список каталогов
            self.listbox.insert(tk.END, item)
            # сохряняем новый каталог в переменную
            new_dir = self.listbox.get(first="end")
            # добавляем новый каталог в базу данных по ключу словаря
            data[self.key].append(new_dir)
        self.write_to_base(data)  # сохраняем изменения в базе данных
        # print(data)

    def del_from_listbox(self):
        """функция для удаления файла из перечня файлов объекта Listbox и из базы данных"""
        index = self.listbox.curselection()  # находим индекс выделенной строки в списке
        if index:  # если строка выбрана
            # определяем значение строки - наименование файла
            value = self.listbox.get(index)
            if self.key == "files":  # если выбран файл
                # удаляем файл из перечня файлов для копирования
                self.listbox.delete(index)
                # удаляем файл из базы данных
                for item in data[self.key]:
                    if value in item:
                        data[self.key].remove(item)
                self.write_to_base(data)  # сохраняем изменения в базе данных
            else:  # если выбран каталог
                # удаляем каталог из перечня каталогов для копирования
                self.listbox.delete(index)
                data[self.key].remove(value)
        # print(data)

    def write_to_base(self, dct):
        """функция для записи актуального перечня файлов и каталогов в базу данных"""
        with open(database, "w", encoding="utf-8-sig") as file:
            json.dump(dct, file, ensure_ascii=False, indent=4)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        # название заголовка в окне приложения
        self.title("РЕЗЕРВНОЕ КОПИРОВАНИЕ_v3")
        # меняем логотип Tkinter на свой
        self.iconbitmap("IconGray_square.ico")
        # self.iconbitmap("//Server/otk/Support_files_не_удалять!!!/Значки_Логотипы/IconGray_square.ico")

        width = 540  # ширина окна
        heigh = 530  # высота окна
        # определяем координаты центра экрана и размещаем окно
        screenwidth = self.winfo_screenwidth()
        screenheight = self.winfo_screenheight()
        self.geometry(
            "%dx%d+%d+%d"
            % (width, heigh, (screenwidth - width) / 2, (screenheight - heigh) / 2)
        )

        # наименование фрейма с перечнем файлов и скроллингом
        self.group_1 = tk.LabelFrame(
            self, padx=15, pady=10, text="Перечень файлов для резевного копирования"
        )
        # экземпляр класса ListFrame
        # виджет с перечнем файлов для копирования и скроллингом (объект Listbox и в нем объект Scrollbar)
        self.frame_a = ListFrame(self.group_1, width=74, height=12, key="files")

        # наименование фрейма с каталогом в который будут сохраняться файлы
        self.group_2 = tk.LabelFrame(
            self,
            padx=15,
            pady=10,
            text="Перечень каталогов для резевного копирования",
        )
        # экземпляр класса ListFrame
        # виджет (объект Listbox) для выбора каталога в который будут сохраняться файлы
        self.frame_b = ListFrame(self.group_2, width=74, height=3, key="dirs")

        # кнопка выбора файла и добавления в список
        self.btn_add_file = tk.Button(
            self,
            text="Добавить файл",
            command=lambda x="Добавить файл": self.choose_file(x),
        )

        # кнопка удаления файла из списка
        self.btn_del_file = tk.Button(
            self, text="Убрать файл", command=self.frame_a.del_from_listbox
        )

        # кнопка выбора каталога в который будут сохраняться файлы и добавления в список
        self.btn_add_pap = tk.Button(
            self,
            text="Добавить каталог",
            command=lambda x="Добавить каталог": self.choose_file(x),
        )

        # кнопка удаления каталога в который будут сохраняться файлы
        self.btn_del_pap = tk.Button(
            self, text="Убрать каталог", command=self.frame_b.del_from_listbox
        )

        # кнопка копирования файлов из списка
        self.btn_copy_file = tk.Button(
            self, text="Копировать файлы", command=self.start_copy
        )

        # виджет индикатора копирования файлов из списка
        self.progress_bar = ttk.Progressbar(
            self,
            orient="horizontal",
            mode="determinate",
            length=400,
            maximum=100,
            value=0,
        )

        self.text = tk.Label(self, text="Intellectual property of Igor Vasilenok")

        # размещаем фреймы, виджеты и кнопки
        opts = {"padx": 15, "pady": 7}
        self.group_1.grid(row=0, columnspan=2, **opts)
        self.frame_a.pack()
        self.btn_add_file.grid(row=1, column=0, **opts, sticky=tk.E)
        self.btn_del_file.grid(row=1, column=1, **opts, sticky=tk.W)
        self.group_2.grid(row=2, columnspan=2, **opts)
        self.frame_b.pack()
        self.btn_add_pap.grid(row=3, column=0, **opts, sticky=tk.E)
        self.btn_del_pap.grid(row=3, column=1, **opts, sticky=tk.W)
        self.progress_bar.grid(row=4, columnspan=2, **opts)
        self.btn_copy_file.grid(row=5, columnspan=2, **opts)
        self.text.grid(row=6, columnspan=2, sticky=tk.W)

    def choose_file(self, x):
        """функция для выбора файла из окна Проводника"""
        if x == "Добавить файл":
            # выбираем файл из открывшегося окна Проводника
            filename = fd.askopenfilename(title="Открыть файл", initialdir="/")
            if filename:  # если файл выбран
                # добавляем файл в список файлов для копирования
                self.frame_a.insert_to_listbox(filename)
        elif x == "Добавить каталог":
            # выбираем каталог из открывшегося окна Проводника
            fl_pap = fd.askdirectory(title="Открыть каталог")
            if fl_pap:  # если каталог выбран
                # добавляем каталог в список каталогов для копирования
                self.frame_b.insert_to_listbox(fl_pap)

    def change_progress(self):
        """функция отображения виджета загрузки с задержкой на 1 секунду"""
        while self.progress_bar["value"] < 100:
            self.progress_bar["value"] += 10
            self.update()
            time.sleep(0.2)
            if self.progress_bar["value"] == 70:  # остановка (псевдозагрузка)
                time.sleep(0.5)

    def start_copy(self):
        """функция для копирования во все каталоги и вывода информационного окна"""
        flag_error = False
        # если список файлов или каталогов пустой - выводим информационное окно об ошибке
        if not all([v for v in data.values()]):
            messagebox.showerror(
                "ВНИМАНИЕ!",
                "Произошла ошибка!\nФайлы или каталоги для копирования не выбраны!",
            )
            flag_error = True

        # по каждому каталогу из списка выбранных каталогов
        for dr in data["dirs"]:
            self.progress_bar["value"] = 0  # обнуляем виджет загрузки

            # создаем экземпляр класса Copy_file из кастомного модуля modul_copyfile
            obj = Copy_file(data["files"], dr)
            flag = obj.copy_file()  # копируем файлы в указанный каталог
            print(flag)
            if flag:  # если копирование завершено без ошибок и copy_file вернула True
                self.change_progress()  # старт виджета загрузки

        # вывод информационного окна о сохранении файлов и закрытии программы
        if not flag_error:
            result = messagebox.askyesno(
                "СООБЩЕНИЕ",
                "Все файлы скопированы в указанные каталоги.\nЗакрыть программу?",
            )
            if result:  # если согласие на закрытие программы
                self.destroy()  # закрываем приложение
            else:  # если НЕТ согласия
                self.progress_bar["value"] = 0  # обнуляем виджет загрузки


if __name__ == "__main__":
    app = App()
    app.mainloop()
