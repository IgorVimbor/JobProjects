# ВЕРСИЯ для автоматического резервного копирования файлов по расписанию,
# которое настраивается в Планировщике задач Windows

# ------------------- Вспомогательный класс, осуществляющий непосредственное копирование файлов ---------------
# класс Copy_file взят из модуля modul_copyfile_v2.py
from tkinter import Tk, Label
import json
import os
import shutil
from datetime import date, datetime

year_now = str(date.today().year)  # текущий год
data = date.today()  # сегодняшняя дата

# файл для логирования (располагается в каталоге проекта или приложения)
file_logs = "D:/My Programs/Резервное копирование/Резервное копирование_logs.txt"


class Copy_file:
    def __init__(self, lst_file, dir_to_copy):
        # корневой каталог, где будет находиться каталог с копиями файлов, например: 'D:/'
        self.path = dir_to_copy
        # полный путь до каталога с копиями файлов с сегодняшней датой
        self.path_full_name = f"{dir_to_copy}/АРХИВ резервных копий файлов_{data}/"
        # список файлов для копирования
        self.files = [file.strip() for file in lst_file]

    def make_dir(self):
        """функция находит существующий каталог с копиями файлов и переименовывает его по сегодняшней дате
        или создает такой каталог, если он отсутстует
        """
        dir_now = ""  # существующий каталог с копиями файлов
        # циклом по объектам корневого каталога где будет находиться каталог с копиями файлов
        for it in os.scandir(self.path):
            # если объект является каталогом и содержит в названии слова 'АРХИВ резервных копий'
            if it.is_dir() and "АРХИВ резервных копий файлов" in it.name:
                dir_now = it.name  # сохраняем название каталога в переменную
        if dir_now:  # если каталог существует
            # переименовываем его по сегодняшней дате
            os.rename(f"{self.path}/{dir_now}/", self.path_full_name)
        else:  # если не существует - создаем
            os.mkdir(self.path_full_name)

    def copy_file(self):
        """функция производит копирование файлов в переименованный (созданный) каталог
        с сегодняшней датой для копий файлов и записывает информацию в лог-файл
        """
        # если перечень файлов и каталог передан в аргументы, т.е. есть что и куда копировать
        try:
            # если список файлов пустой или - выбрасывем ошибку
            if not self.files or not self.path:
                raise
            # вызываем функцию для переименовывания (создания) каталога с сегодняшней датой
            self.make_dir()
            # циклом по списку файлов для копирования
            for file in self.files:
                # отсекаем название файла с расширением
                f_name = file.split("/")[-1]
                # копируем файл в каталог резевных копий
                shutil.copy(file, f"{self.path_full_name}{f_name}")
            # записываем информацию в лог-файл
            with open(file_logs, "a", encoding="utf-8") as file:
                print(
                    f"{datetime.now()}\n    ОК! Скопировано {len(self.files)} файл(а/ов) в каталог {self.path_full_name} ",
                    file=file,
                )
            return True
        except:
            # записываем информацию об ошибке в лог-файл
            with open(file_logs, "a", encoding="utf-8") as file:
                print(
                    f"{datetime.now()}\n    ОШИБКА! Файлы или каталоги для копирования не выбраны!",
                    file=file,
                )
            return False


# --------------------- Основной модуль - считывание из базы данных и старт резервного копирования ---------------
# Создана общая база данных - файл "Резервное копирование_база данных.txt", в который записывается словарь .json
# В базе данных по ключу "files" хранится перечень файлов для копирования, по ключу "dirs" - перечень каталогов.


# база данных - перечень резервных копий файлов и каталогов
database = "D:/My Programs/Резервное копирование/Резервное копирование_база данных.txt"

# открываем базу данных, считываем файл json и сохраняем словарь в переменную
with open(database, encoding="utf-8-sig") as file:
    dct_files: dict = json.load(file)

# формируем окно Tkinter
window = Tk()
# заголовок окна Tkinter
window.title("Автоматическое Резервное Копирование")
width = 450  # ширина окна
heigh = 220  # высота окна
# определяем координаты центра экрана и размещаем окно по центру
screenwidth = window.winfo_screenwidth()
screenheight = window.winfo_screenheight()
window.geometry(
    "%dx%d+%d+%d" % (width, heigh,
                     (screenwidth - width) / 2,
                     (screenheight - heigh) / 2)
)

lst_flag = []  # список флагов при копировании в каждый каталог
# по каждому каталогу из списка выбранных каталогов
for dr in dct_files["dirs"]:
    # создаем экземпляр класса Copy_file
    obj = Copy_file(dct_files["files"], dr)
    flag = obj.copy_file()  # копируем файлы в указанный каталог
    lst_flag.append(flag)  # добавляем флаг в список флагов
# print(lst_flag)

# вывод информационного окна о сохранении файлов или ошибке
if all(lst_flag):  # если все флаги в списке True
    # создаем виджет Label с текстом
    lbl = Label(
        window,
        text="Резервные копии\nфайлов записаны\nпо расписанию.",
        font=("Arial Bold", 40),
        fg='green')
else:  # иначе
    lbl = Label(
        window,
        text="При резервном копировании\nфайлов по расписанию\nпроизошла ошибка!\nПроверьте списки файлов!",
        font=("Arial Bold", 35),
        fg='red')

# размещаем виджет в окне
lbl.grid(column=0, row=0)


if __name__ == "__main__":
    window.mainloop()
