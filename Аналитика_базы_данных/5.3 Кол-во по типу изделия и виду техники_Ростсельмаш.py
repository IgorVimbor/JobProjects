import pandas as pd
from functions.out_dataframe import MyFrame
import matplotlib.pyplot as plt
import warnings


# Команда для удаления предупреждений Pandas в консоли
warnings.simplefilter(action="ignore", category=Warning)

# потребитель
client = 'ЯМЗ - эксплуатация'
# изделие по которому будет формироваться отчет
product = 'водяной насос'
# ---------------------------------------------------------------------------------------------------

# создаем датафреймы по годам и сводный датафрейм
df_2024 = MyFrame(2024, client, product).get_frame()
df_2023 = MyFrame(2023, client, product).get_frame()
df_2022 = MyFrame(2022, client, product).get_frame()
df = pd.concat([df_2024, df_2023, df_2022])

# список столбцов датафрейма
lst = df_2023.columns.values.tolist()
'''
['Месяц регистрации', 'Обозначение изделия', 'Дата изготовления изделия', 
'Транспортное средство (установка)', 'Пробег, наработка', 
'Причины возникновения дефектов', 'Пояснения к причинам возникновения дефектов', 
'Поставщик дефектного комплектующего']
'''
# циклом по датафреймам
for d in (df_2024, df_2023, df_2022):
    # сохраняем в переменную год по которому делаем анализ
    year = d['Месяц регистрации'].dt.year.unique()[0]

    # в датафрейме оставляем только строки, где транспортное средство содержит слова 'ACROS', 'NOVA', 'KSU'
    d = d[
        (d['Транспортное средство (установка)'].str.contains('ACROS')) |
        (d['Транспортное средство (установка)'].str.contains('NOVA')) |
        (d['Транспортное средство (установка)'].str.contains('KSU'))
    ]

    # результирующие датафреймы по годам (обозначение изделия и количество в базе)
    tmp_df = d.groupby('Месяц регистрации').agg(
        Total=('Обозначение изделия', 'count')).reset_index()

    # в столбце 'Месяц регистрации' оставляем только номер месяца, т.е. было '2024-02-01' стало '2'
    tmp_df['Месяц регистрации'] = tmp_df['Месяц регистрации'].dt.month

    # добавляем снизу строку с итоговым количеством (суммой)
    tmp_df.loc[len(tmp_df.index)] = ['ИТОГО', tmp_df['Total'].sum()]

    # избавляемся от дефолтных индексов - делаем индексом столбец 'Месяц регистрации'
    tmp_df.set_index('Месяц регистрации', inplace=True)

    # выводим в консоль
    print(f"\tДанные за {year} год")
    print(tmp_df)
    print()

    # сохраняем в файл .txt по номеру года
    with open('//Server/otk\ОТЧЕТНОСТЬ БЗА/АНАЛИЗ дефектности БЗА/Количество дефектов вн 536 на Ростсельмаш.txt', 'a') as file:
        print(f'\tДанные за {year} год', file=file)
        print(tmp_df, file=file)
        print(file=file)

print('Файл записан')

# строим график для визуализации
# res_1.plot(kind='line')
# plt.show()
