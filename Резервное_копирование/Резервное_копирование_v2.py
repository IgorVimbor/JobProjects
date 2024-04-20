import os
import time
import tkinter as tk
import tkinter.ttk as ttk
import tkinter.filedialog as fd
from tkinter import messagebox
from modul_copyfile_v2 import Copy_file

# база данных - перечень резервных копий файлов (располагается в каталоге проекта или приложения)
file_base = "Резервное копирование_перечень файлов.txt"


class ListFrame(tk.Frame):
    def __init__(self, master, width, height, is_download=False):
        super().__init__(master)  # наследуемся от tk.Frame
        self._width = width  # ширина виджета
        self._height = height  # высота виджета
        # флаг, что требуется загрузить перечень файлов из базы данных
        self._download = is_download
        # вспомогательный список корневых каталогов для создания каталога резервного копирования
        self.list_dir = []

        # создаем объект Listbox и в нем объект Scrollbar с прокруткой (скроллингом)
        self.list = tk.Listbox(self)
        self.scroll = tk.Scrollbar(self, orient=tk.VERTICAL, command=self.list.yview)
        # указываем размеры объекта Listbox
        self.list.config(width=self._width, height=self._height)

        # сохраняем размещение объектов Listbox и Scrollbar во фрейме
        self.list.pack(side=tk.LEFT)
        self.scroll.pack(side=tk.LEFT, fill=tk.Y)

        # если указан флаг загрузки перечня файлов из базы данных
        if self._download:
            # открываем базу данных с перечнем файлов для копирования, считываем и сохраняем в переменную
            with open(file_base, encoding="utf-8") as items:
                self.items = items.readlines()
            # добавляем в объект Listbox перечень файлов для копирования
            self.list.insert(0, *[i.split("/")[-1] for i in self.items])

    def insert_to_listbox(self, item):
        """функция для добавления файла в перечень файлов объекта Listbox и базу данных"""
        if not os.path.isdir(item):  # если выбранный файл НЕ является каталогом
            # добавляем новый файл в конец перечня файлов для копирования объекта Listbox
            self.list.insert(tk.END, item.split("/")[-1])
            self.items.append(item + "\n")  # добавляем новый файл в базу данных
            print(self.items)
            self.write_to_base(self.items)  # сохраняем изменения в базе данных
        else:  # если выбран каталог
            self.list.insert(tk.END, item)  # добавляем новый каталог в список каталогов
            new_dir = self.list.get(first="end")  # сохряняем новый каталог в переменную
            print(new_dir)
            self.list_dir.append(new_dir)  # добавляем новый каталог в список каталогов

    def del_from_listbox(self):
        """функция для удаления файла из перечня файлов объекта Listbox и из базы данных"""
        index = self.list.curselection()  # находим индекс выделенной строки в списке
        if index:  # если строка выбрана
            # определяем значение строки - наименование файла
            value = self.list.get(index)
            # если файл (выбранная строка) НЕ является каталогом
            if not os.path.isdir(value):
                # удаляем строку из перечня файлов для копирования
                self.list.delete(index)
                # удаляем файл из базы данных
                for item in self.items:
                    if value in item:
                        self.items.remove(item)
                print(self.items)
                self.write_to_base(self.items)  # сохраняем изменения в базе данных
            else:
                # удаляем каталог из перечня каталогов для копирования
                self.list.delete(index)
                self.list_dir.remove(value)

    def write_to_base(self, lst):
        """функция для записи актуального перечня файлов для копирования в базу данных (файл txt)"""
        with open(file_base, "w", encoding="utf-8") as file:
            file.writelines(lst)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        # название заголовка в окне приложения
        self.title("РЕЗЕРВНОЕ КОПИРОВАНИЕ")
        # меняем логотип Tkinter на свой
        # self.iconbitmap("//Server/otk/Support_files_не_удалять!!!/Значки_Логотипы/IconGray_square.ico")

        width = 530  # ширина окна
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
        self.frame_a = ListFrame(self.group_1, width=74, height=12, is_download=True)

        # наименование фрейма с каталогом в который будут сохраняться файлы
        self.group_2 = tk.LabelFrame(
            self,
            padx=15,
            pady=10,
            text="Перечень каталогов для резевного копирования",
        )
        # экземпляр класса ListFrame
        # виджет (объект Listbox) для выбора каталога в который будут сохраняться файлы
        self.frame_b = ListFrame(self.group_2, width=74, height=3, is_download=False)

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
        """функция отображения виджета загрузки с задержкой на 1"""
        while self.progress_bar["value"] < 100:
            self.progress_bar["value"] += 10
            self.update()
            time.sleep(0.3)
            if self.progress_bar["value"] == 70:  # остановка (псевдозагрузка)
                time.sleep(1)

    def preparation_copy(self, dr):
        """функция для копирования файлов в конкретный каталог"""
        self.progress_bar["value"] = 0  # обнуляем виджет загрузки
        # создаем экземпляр класса Copy_file из кастомного модуля modul_copyfile
        obj = Copy_file(self.frame_a.items, dr)
        flag = obj.copy_file()  # копируем файлы в указанный каталог
        print(flag)
        if flag:  # если копирование завершено без ошибок и copy_file вернула True
            self.change_progress()  # старт виджета загрузки
        else:  # иначе вывод информационного окна об ошибке
            messagebox.showerror(
                "ВНИМАНИЕ!",
                "Произошла ошибка!\nФайлы или каталоги для копирования не выбраны!",
            )

    def start_copy(self):
        """функция для копирования во все каталоги и вывода информационного окна"""
        print(self.frame_b.list_dir)
        # по каждому каталогу из вспомогательного списка выбранных каталогов
        for dr in self.frame_b.list_dir:
            self.preparation_copy(dr)

        # вывод информационного окна о сохранении файлов и закрытии программы
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
