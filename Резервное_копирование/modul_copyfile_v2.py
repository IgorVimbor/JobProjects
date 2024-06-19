import os
import shutil
from datetime import date, datetime


year_now = str(date.today().year)  # текущий год
data = date.today()  # сегодняшняя дата

# файл для логирования (располагается в каталоге проекта или приложения)
file_logs = "Резервное копирование_logs.txt"


class Copy_file:
    def __init__(self, lst_file, path_to_base):
        # корневой каталог, где будет находиться каталог с копиями файлов, например: 'D:/'
        self.path = path_to_base
        # полный путь до каталога с копиями файлов с сегодняшней датой
        self.path_to = f"{path_to_base}/АРХИВ резервных копий файлов_{data}/"
        # перечень (список) файлов для копирования
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
            os.rename(f"{self.path}/{dir_now}/", self.path_to)
        else:  # если не существует - создаем
            os.mkdir(self.path_to)

    def copy_file(self):
        """функция производит копирование файлов в переименованный (созданный) каталог
        с сегодняшней датой для копий файлов и записывает информацию в лог-файл
        """
        # если перечень файлов и каталог передан в аргументы, т.е. есть что и куда копировать
        try:
            # если список файлов пустой - выбрасывем ошибку
            if not self.files or not self.path:
                raise
            # вызываем функцию для переименовывания (создания) каталога с сегодняшней датой
            self.make_dir()
            # циклом по перечню файлов для копирования
            for file in self.files:
                # отсекаем название файла с расширением
                f_name = file.split("/")[-1]
                # копируем файл в каталог резевных копий
                shutil.copy(file, f"{self.path_to}{f_name}")
            # записываем информацию в лог-файл
            with open(file_logs, "a", encoding="utf-8") as file:
                print(
                    f"{datetime.now()}\n    ОК! Скопировано {len(self.files)} файл(а/ов) в каталог {self.path_to} ",
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


if __name__ == "__main__":

    files_to_copy = [
        "E:/EDUCATION/ПЕРЕЧЕНЬ по Python.docx",
        "E:/YMZ_month_json.txt",
        "E:/YMZ_year_json.txt",
    ]

    # корневой каталог для копирования резервных копий файлов
    path_2 = "E:/"

    obj_2 = Copy_file(files_to_copy, path_2)
    result = obj_2.copy_file()
    print(result)
