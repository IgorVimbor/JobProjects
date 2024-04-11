# Программа сохраняет в файл информацию из ВСЕЙ базы:
# - сколько всего сообщений зафиксировано в базе,
# - наименование потребителя и количество сообщений по нему.
# Файл сохраняется в папке: ОТЧЕТНОСТЬ БЗА/АНАЛИТИКА дефектности БЗА/Отчет по общему количеству дефектов.txt

import pandas as pd
from datetime import date
import warnings


# Команда для удаления предупреждений Pandas в консоли
warnings.simplefilter(action="ignore", category=Warning)
# То есть предупреждения типа:
''' A value is trying to be set on a copy of a slice from a DataFrame.
    Try using .loc[row_indexer,col_indexer] = value instead  '''
# не будут показываться


year_now = date.today().year  # текущий год

# расположение базы ОТК и имя файла с учетом текущего года
# вместо 'E:/' указать '//Server/otk/1 ГАРАНТИЯ на сервере/'
file_in = '//Server/otk/1 ГАРАНТИЯ на сервере//' + \
    str(year_now) + '-2019_ЖУРНАЛ УЧЁТА.xls'

# расположение файла в который будет сохраняться отчет
file_out = '//Server/otk/ОТЧЕТНОСТЬ БЗА/АНАЛИЗ дефектности БЗА/Количество сообщений_по потребителям.txt'

sheet = str(year_now)    # делаем активным лист базы ОТК по году поиска
# читаем файл Excel и создаем датафрейм
df = pd.read_excel(file_in, sheet_name=sheet, header=1)
k = 3  # поправочный коэффициент нумерации строк

# создаем датафрейм по двум столбцам - месяцу и потребителю.
# Сразу удаляем пустые значения методом dropna()
""" 'Месяц регистрации' или 'Дата изготовления изделия' """  # наименования столбцов для анализа
all_count_defects = df[['Месяц регистрации',
                        'Период выявления дефекта (отказа)']].dropna()
# print(count_defects_month.head())

# кортеж названий потребителей из датафрейма (по этому кортежу считаем количество повторений)
tp_defect = tuple(all_count_defects['Период выявления дефекта (отказа)'])

# словарь дефектов: ключ - где выявлен дефект, значение - количество дефектов
dct_defect = {}
for t in tp_defect:
    dct_defect.setdefault(t, tp_defect.count(t))

# сортируем словарь по убыванию количества дефектов и сохраняем в список дефектов
# в котором хранятся кортежи (потребитель, количество дефектов)
lst_defect = sorted(dct_defect.items(), key=lambda x: x[1], reverse=True)

# функция для вывода в консоль


def show_terminal():
    print('-'*50)
    print(f'Всего поступило {len(all_count_defects)} сообщений.')
    print()
    for key, value in lst_defect:
        # выводим в консоль данные из списка дефектов
        print(f'{key}: {value}')
    print('-'*50)

# функция для сохранения в файл


def save_file():
    with open(file_out, 'w', encoding="utf-8") as res_file:   # записываем в файл
        print('-'*50, file=res_file)
        print(
            f'Всего поступило {len(all_count_defects)} сообщений.', file=res_file)
        print(file=res_file)
        for key, value in lst_defect:
            print(f'{key}: {value}', file=res_file)
        print('-'*50, file=res_file)


ans = int(input(
    'Если вывод в терминал - введите 1.\nЕсли сохранить в файл - введите 2.\nВведите число: '))
if ans == 1:
    show_terminal()
else:
    try:
        save_file()
        print('-'*20, '\nОтчет сохранен\n', '-'*20)
    except:
        print('-'*20, '\nВозникла ошибка\n', '-'*20)
