import os
import shutil
from datetime import date, datetime


year_now = str(date.today().year)  # текущий год
# файл для логирования
file_logs = '//Server/otk/Support_files_не_удалять!!!/Резервное копирование_logs.txt'


class Copy_file:

    data = date.today()  # сегодняшняя дата

    def __init__(self, lst_file, path_to_base: str = '//Server/otk/', ) -> None:
        # корневой каталог где будет находиться каталог с копиями файлов, например: 'D:/'
        self.path = path_to_base  # по умолчанию '//Server/otk/'
        # полный путь до каталога для копий файлов с сегодняшней датой
        self.path_to = f'{path_to_base}АРХИВ резервных копий файлов ОТК_{__class__.data}/'
        # кортеж (перечень) файлов для копирования
        self.files = [file.strip() for file in lst_file]

    def make_dir(self):
        ''' функция находит существующий каталог с копиями файлов и переименовывает его по сегодняшней дате 
            или создает такой каталог, если он отсутстует
        '''
        dir_now = ''  # существующий каталог с копиями файлов
        # циклом по объектам корневого каталога где будет находиться каталог с копиями файлов
        for it in os.scandir(self.path):
            # если объект является каталогом и содержит в названии слова 'АРХИВ баз данных ОТК'
            if it.is_dir() and 'АРХИВ резервных копий файлов' in it.name:
                dir_now = it.name  # сохраняем название каталога в переменную
        # если каталог существует
        if dir_now:
            # переименовываем его по сегодняшней дате
            os.rename(f'{self.path}{dir_now}/', self.path_to)
        else:
            os.mkdir(self.path_to)  # если не существует - создаем

    def copy_file(self):
        ''' функция производит копирование файлов из каталогов, которые находятся на /Server/otk/ в переименованный 
            (созданный) каталог с сегодняшней датой для копий файлов и записывает информацию в лог-файл
        '''
        # если перечень файлов передан в аргументы, т.е. есть что копировать
        if self.files:
            # вызываем функцию для переименовывания (создания) каталога с сегодняшней датой
            self.make_dir()
            # циклом по перечню файлов для копирования
            for file in self.files:
                # отсекаем название файла с расширением
                f_name = file.split('/')[-1]
                # копируем файл в каталог резевных копий
                shutil.copy(file, f'{self.path_to}{f_name}')
            # записываем информацию в лог-файл
            with open(file_logs, 'a', encoding='utf-8') as file:
                print(
                    f'{datetime.now()}\n    ОК! Скопировано файлов - {len(self.files)}', file=file)
            return True
        else:
            # записываем информацию в лог-файл
            with open(file_logs, 'a', encoding='utf-8') as file:
                print(
                    f'{datetime.now()}\n    ОШИБКА! Файлы для копирования не выбраны!', file=file)
            return False


if __name__ == '__main__':

    files_to_copy = [
        '//Server/otk/1 ГАРАНТИЯ на сервере/2024-2019_ЖУРНАЛ УЧЁТА.xls\n',
        '//Server/otk/2 ИННА/Списание БРАКА по ЦЕХАМ/ЖУРНАЛ УЧЕТА актов о браке_2020-2024.xls\n'
    ]

    # корневые каталоги для каталога с резервными копиями
    # по умолчанию '//Server/otk/'
    path_2 = 'D:/'

    obj_1 = Copy_file(files_to_copy)
    obj_1.copy_file()

    obj_2 = Copy_file(files_to_copy, path_2)
    obj_2.copy_file()
