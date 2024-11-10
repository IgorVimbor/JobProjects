# ВЕРСИЯ для автоматического резервного копирования файлов по расписанию,
# которое настраивается в Планировщике задач Windows

# ------------------- Вспомогательный класс, осуществляющий непосредственное копирование файлов ---------------
# класс Copy_file взят из модуля modul_copyfile_v4.py
import json
import os
import shutil
from datetime import date, datetime
import time


year_now = str(date.today().year)  # текущий год
data_now = date.today()  # сегодняшняя дата

# файл для логирования (располагается в каталоге проекта или приложения)
file_logs = "D:/My Programs/Резервное копирование/Резервное копирование_logs.txt"


class Copy_file:
    def __init__(self, lst_file, dir_to_copy):
        # путь до каталога, где будет находиться каталог с архивом копий файлов, например: 'D:/'
        self.path = dir_to_copy
        # создаем каталог с сегодняшней датой в наименовании, где будет архив копий файлов
        self.path_full_name = f"{dir_to_copy}/АРХИВ резервных копий файлов_{data_now}/"
        # список файлов для копирования
        self.files = [file.strip() for file in lst_file]

    def make_dir(self):
        """функция находит существующий каталог с копиями файлов и переименовывает его по сегодняшней дате
        или создает такой каталог, если он отсутстует
        """
        dir_now = ""  # существующий каталог с копиями файлов
        # циклом по объектам корневого каталога, где будет находиться каталог с архивом копий файлов
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
        """функция создает архив копий файлов в переименованный (созданный) каталог
        с сегодняшней датой для копий файлов и записывает информацию в лог-файл
        """
        # если перечень файлов и каталог передан в аргументы, т.е. есть что и куда копировать
        try:
            # если список файлов пустой или не выбран каталог для архивирования - выбрасывем ошибку
            if not self.files or not self.path:
                raise

            # вызываем функцию для переименовывания (создания) каталога с сегодняшней датой
            self.make_dir()

            # Создаем временный каталог для копирования файлов
            temp_dir = f"{self.path_full_name}/temp_archive_dir/"
            os.makedirs(temp_dir, exist_ok=True)

            # циклом по списку копируем файлы и каталоги во временный каталог
            for item in self.files:
                if os.path.isfile(item):  # если объект - это файл
                    # отсекаем название файла с расширением
                    file_name = os.path.basename(item)  # file.split("/")[-1]
                    # копируем файл во временный каталог копий файлов
                    shutil.copy(item, os.path.join(temp_dir, file_name))
                    # копируем файл в каталог резевных копий (если требуется, то РАСКОМЕНТИРОВАТЬ)
                    # shutil.copy(item, os.path.join(self.path_full_name, file_name))
                elif os.path.isdir(item):  # если объект - это каталог и каталогов
                    base_name = os.path.basename(item)  # отсекаем название каталога
                    # копируем каталог во временный каталог копий файлов и каталогов
                    shutil.copytree(item, os.path.join(temp_dir, base_name))

            # Создаем архив
            archive_name = f"{self.path_full_name}Архив файлов"
            shutil.make_archive(archive_name, "zip", temp_dir)
            # Удаляем временный каталог копий файлов
            shutil.rmtree(temp_dir)

            # записываем информацию в лог-файл
            with open(file_logs, "a", encoding="utf-8") as file:
                print(
                    f"{datetime.now()}\n    ОК! Скопировано {len(self.files)} файл(а/ов) в каталог {self.path_full_name} ",
                    file=file,
                )
                print(f"    ОК! Архив файлов_{data_now}.zip успешно создан.", file=file)
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

lst_flag = []  # список флагов при копировании в каждый каталог
# по каждому каталогу из списка выбранных каталогов
for dr in dct_files["dirs"]:
    # создаем экземпляр класса Copy_file
    obj = Copy_file(dct_files["files"], dr)
    flag = obj.copy_file()  # копируем файлы в указанный каталог
    lst_flag.append(flag)  # добавляем флаг в список флагов
    print(flag)

# вывод информационного окна о сохранении файлов или ошибке
if all(lst_flag):  # если все флаги в списке True
    print(
        "\n\tРЕЗЕРВНЫЕ КОПИИ ФАЙЛОВ ЗАПИСАНЫ ПО РАСПИСАНИЮ.\n\n\tЗАКРОЙТЕ ОКНО ПРИЛОЖЕНИЯ."
    )
    time.sleep(300)
else:
    print(
        "\nПРИ РЕЗЕРВНОМ КОПИРОВАНИИ ФАЙЛОВ ПО РАСПИСАНИЮ ПРОИЗОШЛА ОШИБКА!\nПРОВЕРЬТЕ СПИСОК ФАЙЛОВ!"
    )


# -------------------- вариант с окном Tkinter ----------------------------
# from tkinter import Tk, Label

# # формируем окно Tkinter
# window = Tk()
# # заголовок окна Tkinter
# window.title("Автоматическое Резервное Копирование")
# width = 450  # ширина окна
# heigh = 220  # высота окна
# # определяем координаты центра экрана и размещаем окно по центру
# screenwidth = window.winfo_screenwidth()
# screenheight = window.winfo_screenheight()
# window.geometry(
#     "%dx%d+%d+%d"
#     % (width, heigh, (screenwidth - width) / 2, (screenheight - heigh) / 2)
# )

# lst_flag = []  # список флагов при копировании в каждый каталог
# # по каждому каталогу из списка выбранных каталогов
# for dr in dct_files["dirs"]:
#     # создаем экземпляр класса Copy_file
#     obj = Copy_file(dct_files["files"], dr)
#     flag = obj.copy_file()  # копируем файлы в указанный каталог
#     lst_flag.append(flag)  # добавляем флаг в список флагов
# # print(lst_flag)

# # вывод информационного окна о сохранении файлов или ошибке
# if all(lst_flag):  # если все флаги в списке True
#     # создаем виджет Label с текстом
#     lbl = Label(
#         window,
#         text="Резервные копии\nфайлов записаны\nпо расписанию.",
#         font=("Arial Bold", 40),
#         fg="green",
#     )
# else:  # иначе
#     lbl = Label(
#         window,
#         text="При резервном копировании\nфайлов по расписанию\nпроизошла ошибка!\nПроверьте списки файлов!",
#         font=("Arial Bold", 35),
#         fg="red",
#     )

# # размещаем виджет в окне
# lbl.grid(column=0, row=0)

# window.mainloop()
# --------------------------------------------------------------------------------------------------------
