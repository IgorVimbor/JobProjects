import json
from datetime import datetime
import pandas as pd
import os
import win32com.client
from openpyxl import load_workbook
from openpyxl.styles import Alignment, Font, Border, Side

import warnings

warnings.simplefilter(action="ignore", category=Warning)


year_now = datetime.today().year  # текущий год

# имя файла базы рекламаций ОТК с учетом текущего года
# file = "//Server/otk/1 ГАРАНТИЯ на сервере/" + str(year_now) + "-2019_ЖУРНАЛ УЧЁТА.xlsm"
file = f"D:/РАБОТА/{str(year_now)}-2019_ЖУРНАЛ УЧЁТА.xlsm"

# ------------------------------- Создаем датафрейм из файла Excel базы ОТК -----------------------------------
df = pd.read_excel(
    file,
    sheet_name=str(year_now),
    usecols=[
        "Период выявления дефекта (отказа)",
        "Наименование изделия",
        "Количество предъявленных изделий",
        "Виновник дефекта - БЗА",
        "Виновник дефекта - потребитель",
        "Изделие соответствует  ТУ",
        "Виновник не установлен",
    ],
    header=1,
)
# header=1 - строку 2 таблицы ОТК делаем заголовками столбцов датафрейма (индексы строк начинаются с 0)

# изменяем наименование столбцов датафрейма
df.rename(
    columns={
        "Период выявления дефекта (отказа)": "Потребитель",
        "Наименование изделия": "Изделие",
        "Количество предъявленных изделий": "Количество",
        "Виновник дефекта - БЗА": "вин-БЗА",
        "Виновник дефекта - потребитель": "вин-Потребитель",
        "Изделие соответствует  ТУ": "вин-ТУ",
        "Виновник не установлен": "вин-НЕТ",
    },
    inplace=True,
)

# ------------------------------ вариант 1 - компактный с распаковкой словаря (**) -------------------------------

vin_columns = ['вин-БЗА', 'вин-Потребитель', 'вин-ТУ', 'вин-НЕТ']

# Создаем временную копию только на время операций
df_temp = df.copy()

# Выполняем все преобразования в одном блоке:
# - рассчитываем значение для суммирования (количество * флаг), используя метод eq()
for col in vin_columns:
    df_temp[f"{col}_value"] = df_temp['Количество'] * df_temp[col].eq('+').astype(int)

# Группируем и суммируем
res_df = df_temp.groupby(['Потребитель', 'Изделие']).agg(
    Количество=('Количество', 'sum'),
    **{col: (f"{col}_value", 'sum') for col in vin_columns}
).reset_index()

# Преобразуем типы
res_df[vin_columns] = res_df[vin_columns].astype(int)
res_df['Количество'] = res_df['Количество'].astype(int)

# Удаляем временный датафрейм сразу после использования
del df_temp

# Создаем новые столбцы "Признано", "Отклонено", "Не поступало" и расчитываем значения в них
res_df["Признано"] = res_df["вин-БЗА"] + res_df["вин-НЕТ"]
res_df["Отклонено"] = res_df["вин-ТУ"] + res_df["вин-Потребитель"]
res_df["Не поступало"] = res_df["Количество"] - (res_df["Признано"] + res_df["Отклонено"])

# Выбираем только нужные столбцы
res_df = res_df[['Потребитель', 'Изделие', 'Количество', 'Признано', 'Отклонено', 'Не поступало']]

# записываем в файл TXT
date_new = datetime.today().strftime("%d-%m-%Y")  # сегодняшняя дата

file_txt = f"D:/РАБОТА/Количество признанных рекламаций_{date_new}.txt"
# file_txt = "//Server/otk/Support_files_не_удалять!!!/Количество признанных рекламаций.txt"

with open(file_txt, "w", encoding="utf-8") as f:
    print(
        f"\n\n\tСправка по количеству признанных рекламаций на {date_new}\n\n",
        file=f,
    )
    f.write(res_df.to_string())

print("Справка в файл TXT записана")

# print(res_df)


# ------------------------------------ вариант 2 - подробный ---------------------------------------

# # Список колонок с префиксом "вин-"
# vin_columns = ['вин-БЗА', 'вин-Потребитель', 'вин-ТУ', 'вин-НЕТ']

# # Создаем копию DataFrame для обработки
# df_temp = df.copy()

# # 1. Создаем временные столбцы для каждой вин-колонки
# for col in vin_columns:
#     # Создаем флаговый столбец: 1 если "+", иначе 0
#     flag_col = f"{col}_flag"
#     df_temp[flag_col] = df_temp[col].apply(lambda x: 1 if x == '+' else 0)

#     # Рассчитываем значение для суммирования (флаг * количество)
#     value_col = f"{col}_value"
#     df_temp[value_col] = df_temp[flag_col] * df_temp['Количество']

# # 2. Список всех столбцов для суммирования
# sum_columns = ['Количество'] + [f"{col}_value" for col in vin_columns]

# # 3. Группируем и суммируем
# result_df = df_temp.groupby(['Потребитель', 'Изделие'])[sum_columns].sum().reset_index()

# # 4. Переименовываем временные столбцы в исходные названия
# rename_dict = {}
# for col in vin_columns:
#     rename_dict[f"{col}_value"] = col

# result_df = result_df.rename(columns=rename_dict)

# # 5. Преобразуем типы данных в int
# int_columns = ['Количество'] + vin_columns
# result_df[int_columns] = result_df[int_columns].astype(int)

# # 6. Выбираем только нужные столбцы
# final_columns = ['Потребитель', 'Изделие', 'Количество'] + vin_columns
# result_df = result_df[final_columns]

# # Удаляем временный датафрейм (опционально)
# del df_temp

# # ... далее как в варианте 1 ...