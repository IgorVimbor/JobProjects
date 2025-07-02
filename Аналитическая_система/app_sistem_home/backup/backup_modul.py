# Вспомогательный модуль приложения <Резервное копирование>

import os
import shutil
from datetime import date, datetime

import paths_home  # импортируем файл с путями до базы данных, отчетов и др.


year_now = str(date.today().year)  # текущий год
data_now = date.today()  # сегодняшняя дата

# импортируем путь до файла для логирования резервного копирования
file_logs = paths_home.buckup_logs


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
                elif os.path.isdir(item):  # если объект - это каталог
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


if __name__ == "__main__":

    files_to_copy = [
        "D:/EDUCATION/ПЕРЕЧЕНЬ по Python.docx",
        "D:/PDF files/Банковские платежи/Оплата ДС-19_январь21.pdf",
        "D:/ЗАГРУЗКИ/calendar.csv",
        "D:/Изображения/1-6-1.png",
        "E:/Плейлисты/Поль Мариа",
    ]

    # корневой каталог для копирования резервных копий файлов
    path_2 = "E:/"

    obj_2 = Copy_file(files_to_copy, path_2)
    result = obj_2.copy_file()
    print(result)
