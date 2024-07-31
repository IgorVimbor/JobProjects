# Диаграмма - потребитель и вид изделия по месяцу регистрации или дате изготовления

import pandas as pd
import warnings
import sys

sys.path.insert(0, "E:/MyRepositories/JobProjects/Аналитика_базы_данных/functions/")
from out_dataframe import MyFrame
from stolb_diagram import show_stolb_graph

# Команда для удаления предупреждений Pandas в консоли
warnings.simplefilter(action="ignore", category=Warning)


# вводим данные
client = "ММЗ - эксплуатация"  # потребитель
product = "водяной насос"  # изделие по которому будет формироваться диаграмма
# наименование столбца по которому строим диаграмму
value_column = "Месяц регистрации"
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
df1 = MyFrame(2023, "ММЗ - эксплуатация", product).get_frame()
df2 = MyFrame(2023, "ММЗ - АСП", product).get_frame()
df3 = MyFrame(2024, "ММЗ - эксплуатация", product).get_frame()
df4 = MyFrame(2024, "ММЗ - АСП", product).get_frame()
# data_2024 = MyFrame(2024, client, product).get_frame()
# data_2023 = MyFrame(2023, client, product).get_frame()
# data_2022 = MyFrame(2022, client, product).get_frame()
# data_2021 = MyFrame(2021, client, product).get_frame()

# создаем сводный датафрейм из датафреймов по годам
# df = pd.concat([data_2024, data_2023, data_2022, data_2021])
df = pd.concat([df1, df2, df3, df4])

# если выбран столбец 'Дата изготовления изделия', то в датафрейме удаляем строки, где нет даты
if value_column == "Дата изготовления изделия":
    df.dropna(subset=[value_column], inplace=True)

# сортированный список значений столбца датафрейма по которому строим диаграмму
lst = sorted(df[value_column].to_list())

# словарь: ключ - дата (месяц.год) или другой параметр для диаграммы, значение - количество повторов
dct_defect = {}
for t in lst:
    if isinstance(t, pd.Timestamp):
        dct_defect.setdefault(t.strftime("%m.%y"), lst.count(t))
    else:
        dct_defect.setdefault(t, lst.count(t))

# вспомогательный словарь для печати заголовка диаграммы и наименования файла
dct_name = {
    "водяной насос": "Водяные насосы",
    "компрессор": "Компрессоры",
    "турбокомпрессор": "Турбокомпрессоры",
    "масляный насос": "Масляные насосы",
    "Дата изготовления изделия": "дате изготовления изделия",
    "Месяц регистрации": "дате сообщения",
    "Пробег, наработка": "пробегу в километрах",
    "Обозначение изделия": "обозначению изделия",
}

# заголовок диаграммы
title = (
    f"{dct_name[product]} {client.split()[0]}\nКоличество по {dct_name[value_column]}"
)

# путь для сохранения файла
path = (
    f"//Server/otk/ОТЧЕТНОСТЬ БЗА/АНАЛИЗ дефектности БЗА/Диаграмма_{client.split()[0]}_по {dct_name[value_column]}"
    + ".pdf"
)
print("График готов")

show_stolb_graph(dct_defect, width=18, title_graph=title, path_out_file=None)
# show_stolb_graph(dct_defect, width=18, size=8, title_graph=title, path_out_file=path)
# print("Файл записан")
