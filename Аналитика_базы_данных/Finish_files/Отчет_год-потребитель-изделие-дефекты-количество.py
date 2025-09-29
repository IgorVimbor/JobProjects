import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

import json
from datetime import datetime
import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Alignment, Font, Border, Side

import sys
# sys.path.insert(0, 'E:/MyRepositories/JobProjects/Аналитика_базы_данных/functions/')
sys.path.insert(0, '../functions/')
from functions.out_dataframe import MyFrame

import warnings
warnings.simplefilter(action="ignore", category=Warning)

product = "турбокомпрессор"  # изделие по которому будут строится графики
client = 'ММЗ'  # потребитель

# создаем датафреймы по годам
client_asp = f"{client} - АСП"   # потребитель АСП
client_gp = f"{client} - эксплуатация"  # потребитель ГП

df1 = MyFrame(2022, client_asp, product).get_frame()
# df2 = MyFrame(2022, client_gp, product).get_frame()
# df3 = MyFrame(2023, client_asp, product).get_frame()
# df4 = MyFrame(2023, client_gp, product).get_frame()
# df5 = MyFrame(2024, client_asp, product).get_frame()
# df6 = MyFrame(2024, client_gp, product).get_frame()
# df7 = MyFrame(2025, client_asp, product).get_frame()
# df8 = MyFrame(2025, client_gp, product).get_frame()

# создаем сводный датафрейм из датафреймов по годам
df = pd.concat([df1])

# print(df.columns)

df.rename(
            columns={
                "Количество предъявленных изделий": "Количество",
                "Заявленный дефект изделия": "Заявленный дефект",
            },
            inplace=True,
        )

# # print(df.info())

# Формируем результирующий датафрейм - отчет за период ... df_res = df_c.loc[3:].groupby(...)
df_res = (
    df.groupby(
        [
            # "Период выявления",
            # "Наименование изделия",
            "Обозначение изделия",
            "Заявленный дефект",
        ]
    )["Количество"]
    .sum()
    .to_frame()
).sort_values("Количество", ascending=False)

# Изменяем тип данных в столбце "Количество"
df_res["Количество"] = df_res["Количество"].astype("int16")

print(df_res)

# записываем в файл Excel
res_file_excel = "//Server/otk/ПРОТОКОЛЫ совещаний по качеству/2025/Группа по ТКР/ММЗ-АСП_данные по ТКР.xlsx"
df_res.to_excel(res_file_excel)

print("Файл Excel со справкой записан")
