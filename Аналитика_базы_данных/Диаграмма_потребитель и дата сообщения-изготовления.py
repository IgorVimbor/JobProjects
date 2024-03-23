import pandas as pd
from functions.out_dataframe import MyFrame
from functions.stolb_diagram import show_stolb_graph
import warnings


# Команда для удаления предупреждений Pandas в консоли
warnings.simplefilter(action="ignore", category=Warning)
# То есть предупреждения типа:
''' A value is trying to be set on a copy of a slice from a DataFrame.
    Try using .loc[row_indexer,col_indexer] = value instead  '''
# не будут показываться


# ----------------------------- Вводим данные ------------------------------------

client = 'ЯМЗ - эксплуатация'   # потребитель
product = 'водяной насос'       # изделие по которому будет формироваться диаграмма
# наименование столбца по которому строим диаграмму
value_column = 'Месяц регистрации'
# список столбцов датафрейма
# ['Месяц регистрации',
# 'Обозначение изделия',
# 'Дата изготовления изделия',
# 'Транспортное средство (установка)',
# 'Пробег, наработка',
# 'Причины возникновения дефектов',
# 'Пояснения к причинам возникновения дефектов',
# 'Поставщик дефектного комплектующего']
# --------------------------------------------------------------------------------

# создаем датафреймы по годам
df = MyFrame(2023, client, product).get_frame()
# data_2023 = MyFrame(2023, client, product).get_frame()
# data_2022 = MyFrame(2022, client, product).get_frame()
# data_2021 = MyFrame(2021, client, product).get_frame()

# создаем сводный датафрейм из датафреймов по годам
# df = pd.concat([data_2023, data_2022, data_2021])

# если выбран столбец 'Дата изготовления изделия', то в датафрейме удаляем строки, где нет даты
if value_column == 'Дата изготовления изделия':
    df.dropna(subset=[value_column], inplace=True)

# сортированный список значений столбца датафрейма по которому строим диаграмму
lst = sorted(df[value_column].to_list())

# словарь: ключ - дата (месяц.год) или другой параметр для диаграммы, значение - количество повторов
dct_defect = {}
for t in lst:
    if isinstance(t, pd.Timestamp):
        dct_defect.setdefault(t.strftime('%m.%y'), lst.count(t))
    else:
        dct_defect.setdefault(t, lst.count(t))

# вспомогательный словарь для печати заголовка диаграммы и наименования файла
dct_name = {
    'водяной насос': 'Водяные насосы',
    'компрессор': 'Компрессоры',
    'турбокомпрессор': 'Турбокомпрессоры',
    'масляный насос': 'Масляные насосы',
    'Дата изготовления изделия': 'дате изготовления изделия',
    'Месяц регистрации': 'дате сообщения',
    'Пробег, наработка': 'пробегу в километрах',
    'Обозначение изделия': 'обозначению изделия'
}

# заголовок диаграммы
title = f'{dct_name[product]} {client.split()[0]}\nКоличество по {dct_name[value_column]}'

# путь для сохранения файла
path = f'//Server/otk/ОТЧЕТНОСТЬ БЗА/АНАЛИЗ дефектности БЗА/Диаграмма_{client.split()[0]}_по {dct_name[value_column]}' + '.pdf'
print('Файл записан')

show_stolb_graph(dct_defect, width=18, title_graph=title, path_out_file=None)
