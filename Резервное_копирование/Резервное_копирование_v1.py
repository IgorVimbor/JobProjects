# ВЕРСИЯ 1
# Первоначальная (стартовая) версия приложения.
# Путь к базе данных - перечню файлов для копирования через глобальную переменную file_base захардкоден.
# В модуле modul_copyfile_v1 путь к файлу с логами также захардкоден на Server/otk/

import time
import tkinter as tk
import tkinter.ttk as ttk
import tkinter.filedialog as fd
from tkinter import messagebox
from modul_copyfile_v1 import Copy_file


file_base = (
    "//Server/otk/Support_files_не_удалять!!!/Резервное копирование_перечень файлов.txt"
)


class ListFrame(tk.Frame):
    def __init__(self, master):
        super().__init__(master)  # наследуемся от tk.Frame
        # открываем базу данных с перечнем файлов для копирования, считываем и сохраняем в переменную
        with open(file_base, encoding="utf-8") as items:
            self.items = items.readlines()
        # создаем объект Listbox и в нем объект Scrollbar с прокруткой (скроллингом)
        self.list = tk.Listbox(self)
        self.scroll = tk.Scrollbar(self, orient=tk.VERTICAL, command=self.list.yview)
        # указываем размеры объекта Listbox
        self.list.config(width=70, height=12)
        # добавляем в объект Listbox перечень файлов для копирования
        self.list.insert(0, *[i.split("/")[-1] for i in self.items])
        # сохраняем размещение объектов Listbox и Scrollbar во фрейме
        self.list.pack(side=tk.LEFT)
        self.scroll.pack(side=tk.LEFT, fill=tk.Y)

    def del_item(self):
        """функция для удаления файла из базы данных и перечня файлов объекта Listbox"""
        index = self.list.curselection()  # находим индекс выделенного файла
        if index:  # если файл выбран
            value = self.list.get(index)  # определяем его значение (имя файла)
            # print(value)
            # удаляем файл из перечня файлов для копирования
            self.list.delete(index)
            # удаляем файл из базы данных
            for item in self.items:
                if value in item:
                    self.items.remove(item)
            print(self.items)
            self.write_list(self.items)  # сохраняем изменения в базе данных

    def insert_item(self, item):
        """функция для добавления файла в базу данных и перечень файлов объекта Listbox"""
        # добавляем новый файл в конец перечня файлов для копирования объекта Listbox
        self.list.insert(tk.END, item.split("/")[-1])
        self.items.append(item + "\n")  # добавляем новый файл в базу данных
        print(self.items)
        self.write_list(self.items)  # сохраняем изменения в базе данных

    def write_list(self, lst):
        """функция для записи актуального перечня файлов для копирования в базу данных (файл txt)"""
        with open(file_base, "w", encoding="utf-8") as file:
            file.writelines(lst)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        # название заголовка в окне приложения
        self.title("РЕЗЕРВНОЕ КОПИРОВАНИЕ")
        # меняем логотип Tkinter на свой
        self.iconbitmap(
            "//Server/otk/Support_files_не_удалять!!!/Значки_Логотипы/IconGray_square.ico"
        )

        width = 530  # ширина окна
        heigh = 400  # высота окна
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

        # виджет с перечнем файлов для копирования и скроллингом (объект Listbox и в нем объект Scrollbar)
        self.frame_a = ListFrame(self.group_1)  # экземпляр класса ListFrame

        # кнопка выбора файла и добавления в список
        self.btn_add_file = tk.Button(
            self, text="Добавить файл", command=self.choose_file
        )

        # кнопка удаления файла из списка
        self.btn_del_file = tk.Button(
            self, text="Убрать файл", command=self.frame_a.del_item
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
        opts = {"padx": 15, "pady": 8}
        self.group_1.grid(row=0, columnspan=2, **opts)
        self.frame_a.pack()
        self.btn_add_file.grid(row=1, column=0, **opts, sticky=tk.E)
        self.btn_del_file.grid(row=1, column=1, **opts, sticky=tk.W)
        self.btn_copy_file.grid(row=2, columnspan=2, **opts)
        self.progress_bar.grid(row=3, columnspan=2, **opts)

    def choose_file(self):
        """функция для выбора файла из окна Проводника"""
        # выбираем файл из открывшегося окна Проводника
        filename = fd.askopenfilename(title="Открыть файл", initialdir="/")
        if filename:  # если файл выбран
            # добавляем файл в список файлов для копирования
            self.frame_a.insert_item(filename)

    def start_copy(self):
        """функция для копирования файлов и вывода информационного окна"""
        # создаем экземпляр класса Copy_file из кастомного модуля modul_copyfile
        obj = Copy_file(self.frame_a.items)
        flag = obj.copy_file()  # копируем файлы из списка файлов
        if flag:  # если копирование завершено без ошибок и copy_file() вернула True
            # старт виджета загрузки
            while self.progress_bar["value"] < 100:
                self.progress_bar["value"] += 10
                self.update()
                time.sleep(0.5)
            # вывод информационного окна о сохранении файлов и закрытии программы
            if messagebox.askokcancel(
                "СООБЩЕНИЕ", "Все файлы скопированы.\nЗакрыть программу?"
            ):
                self.destroy()
        else:  # иначе, выводим сообщение об ошибке
            messagebox.showerror("ВНИМАНИЕ!", "Произошла ошибка!")


if __name__ == "__main__":
    app = App()
    app.mainloop()
