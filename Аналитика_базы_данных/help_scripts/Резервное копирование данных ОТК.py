import os
import shutil
from datetime import date


year_now = str(date.today().year)
data = date.today()

path_from = '//Server/otk/'  # корневой каталог

# список катологов в корневом каталоге
lst_dirs_otk = [it.name for it in os.scandir(path_from) if it.is_dir()]
# список с наименованием существующего каталога, в котором сохранены копии
dir_to = [it for it in lst_dirs_otk if 'АРХИВ баз данных ОТК' in it]

# если такой каталог существует
if dir_to:
    # переименовываем его по сегодняшней дате
    os.rename(f'{path_from}{dir_to[0]}/',
              f'{path_from}АРХИВ баз данных ОТК_{data}/')
else:
    # если не существует - создаем
    os.mkdir(f'{path_from}АРХИВ баз данных ОТК_{data}/')

# путь с наименованием нового каталога для сохоанения
path_to = f'{path_from}АРХИВ баз данных ОТК_{data}/'


directs = ('1 ГАРАНТИЯ на сервере/',
           '2 ИННА/Списание БРАКА по ЦЕХАМ/',
           '5 ВХОДНОЙ КОНТРОЛЬ/СПРАВКА-ОТЧЕТ_по месяцам+итог/',
           'ОТЧЕТНОСТЬ БЗА/ОТГРУЗКА+ГАРАНТИЙНЫЙ ПАРК/',
           'ПРЕТЕНЗИИ/')

files = (f'{year_now}-2019_ЖУРНАЛ УЧЁТА.xls',
         'ЖУРНАЛ УЧЕТА актов о браке_2020-2024.xls',
         'ОТЧЕТ_ВХОДНОЙ КОНТРОЛЬ_по месяцам + за год.xls',
         'ОТГРУЗКА+ГАРАНТИЙНЫЙ ПАРК_текущий год.xlsx',
         'Отгрузка для ОТК_текущий год.xlsx',
         'ОТЧЕТ по гарантийке_УК_текущий год.xlsx',
         'ЖУРНАЛ претензий_МАЗ-ПТЗ-ЧСДМ-УРАЛ-Салео.xls',
         'ЖУРНАЛ претензий_ММЗ.xls',
         'ЖУРНАЛ претензий_ЯМЗ.xls')

for i in range(3):
    shutil.copy(f'{path_from}{directs[i]}{files[i]}', f'{path_to}{files[i]}')
    print('Файл скопирован')

for i in range(3, 6):
    shutil.copy(f'{path_from}{directs[3]}{files[i]}', f'{path_to}{files[i]}')
    print('Файл скопирован')

for i in range(6, 9):
    shutil.copy(f'{path_from}{directs[4]}{files[i]}', f'{path_to}{files[i]}')
    print('Файл скопирован')
