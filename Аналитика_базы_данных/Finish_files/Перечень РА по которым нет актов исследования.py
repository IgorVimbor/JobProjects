# Перечень рекламационных актов по которым НЕТ актов исследования

import pandas as pd
import numpy as np
from datetime import date
import warnings
import matplotlib.pyplot as plt
import seaborn as sns

# убираем вывод информационных сообщений pandas
warnings.simplefilter(action="ignore", category=Warning)

# --------------------------------------------------- Настройка вывода датафрейма в консоль ----------------------------------

# устанавливаем максимальное количество столбцов при выводе в консоль
pd.set_option("display.max_columns", 20)
# устанавливаем максимальное количество символов - ширину столбца
pd.set_option("display.max_colwidth", 70)
# устанавливаем ширину консоли
pd.set_option("display.width", 300)

""" Alt + z """  # включить/выключить горизонтальную прокрутку
# -----------------------------------------------------------------------------------------------------------------------------

analys_year = 2025  # год, по которому проводим анализ

year_now = date.today().year  # текущий год
file = f"//Server/otk/1 ГАРАНТИЯ на сервере/{str(year_now)}-2019_ЖУРНАЛ УЧЁТА.xlsm"

df = pd.read_excel(
    file,
    sheet_name=str(analys_year),
    usecols=[
        "Дата поступления сообщения в ОТК",
        "Период выявления дефекта (отказа)",
        "Наименование изделия",
        "Обозначение изделия",
        "Номер рекламационного акта ПРИОБРЕТАТЕЛЯ изделия",
        "Дата рекламационного акта ПРИОБРЕТАТЕЛЯ изделия",
        "Дата поступления изделия",
        "Дата акта исследования",
    ],
    header=1,
)

# --------------------------------- Обработка значений столбцов датафрейма ---------------------------------------

# В базе ОТК до 2025 года в ячейке "Дата поступления изделия" имеет строковый фомат и имеются значения "фото".
# Начиная с 2025 года ячейки "Дата поступления сообщения в ОТК", "Дата рекламационного акта ПРИОБРЕТАТЕЛЯ изделия",
# "Дата поступления изделия" и "Дата акта исследования" имеют только формат даты

if analys_year < 2025:
    # строки для 2020-2024 годов
    # если в ячейке "Дата поступления изделия" указана не дата, а значение, содержащее слово "фото" - заменяем
    # на значение в ячейке "Дата поступления сообщения в ОТК", если в ней есть значение, а если нет - на None
    df.loc[
        df["Дата поступления изделия"].str.contains("фото") == True,
        "Дата поступления изделия",
    ] = df["Дата поступления сообщения в ОТК"].where(df["Дата поступления сообщения в ОТК"].notnull(), None)
else:
    # # строка для 2025 года
    df["Дата поступления изделия"] = df["Дата поступления сообщения в ОТК"].where(df["Дата поступления сообщения в ОТК"].notnull(), None)


# удаляем строки, где отсутствует дата поступления на завод
df = df.dropna(subset=["Дата поступления изделия"])


if analys_year < 2025:
    # строки для 2020-2024 годов
    # если в ячейке "Дата акта исследования" записаны несколько дат, то оставляем последнюю дату
    df.loc[
        df["Дата акта исследования"].str.contains("\n") == True,
        "Дата акта исследования",
    ] = df["Дата акта исследования"].map(lambda x: str(x).split("\n")[-1])

    # переводим тип данных в столбцах в datetime64
    df[
        [
            "Дата рекламационного акта ПРИОБРЕТАТЕЛЯ изделия",
            "Дата поступления изделия",
            "Дата акта исследования",
        ]
    ] = df[
        [
            "Дата рекламационного акта ПРИОБРЕТАТЕЛЯ изделия",
            "Дата поступления изделия",
            "Дата акта исследования",
        ]
    ].apply(pd.to_datetime)


# ---------------------------- Изделия по АСП по которым НЕТ актов --------------------------------

# датафрейм изделий АСП по которым нет актов исследования
df_asp_not_act = df[
    (df["Период выявления дефекта (отказа)"].str.contains("АСП") == True)
    & (df["Дата акта исследования"].isnull())
][
    [
        "Период выявления дефекта (отказа)",
        "Наименование изделия",
        "Обозначение изделия",
        "Номер рекламационного акта ПРИОБРЕТАТЕЛЯ изделия",
        "Дата рекламационного акта ПРИОБРЕТАТЕЛЯ изделия",
        "Дата поступления изделия",
    ]
]
# переименовываем столбцы датафрейма
df_asp_not_act.columns = [
    "Потребитель",
    "Наименование",
    "Обозначение",
    "Номер РА",
    "Дата РА",
    "Дата прихода",
]

# приводим нумерацию строк в датафрейме как в базе рекламаций
df_asp_not_act.index = df_asp_not_act.index + 3
# присваиваем наименование столбцу с номерами строк датафрейма (индексу строк)
df_asp_not_act.index.name = "Строка базы"

print(df_asp_not_act)

# сохраняем в файл .txt
with open(
    f"//Server/otk/Support_files_не_удалять!!!/НЕТ актов АСП - {date.today()}.txt",
    "w",
    encoding="utf-8",
) as f:
    print(
        f"\tПеречень актов рекламаций по которым НЕТ актов исследования на {date.today()}",
        file=f,
    )
    f.write(df_asp_not_act.to_string())

print("\nОтчет по АСП записан.")


# ---------------------------- Изделия по ГП по которым НЕТ актов --------------------------------

# датафрейм изделий ГП по которым нет актов исследования
df_gp_not_act = df[
    (df["Период выявления дефекта (отказа)"].str.contains("эксплуатация") == True)
    & (df["Дата акта исследования"].isnull())
][
    [
        "Период выявления дефекта (отказа)",
        "Наименование изделия",
        "Обозначение изделия",
        "Номер рекламационного акта ПРИОБРЕТАТЕЛЯ изделия",
        "Дата рекламационного акта ПРИОБРЕТАТЕЛЯ изделия",
        "Дата поступления изделия",
    ]
]
# Переименовываем столбцы датафрейма
df_gp_not_act.columns = [
    "Потребитель",
    "Наименование",
    "Обозначение",
    "Номер РА",
    "Дата РА",
    "Дата прихода",
]

# Приводим нумерацию строк в датафрейме как в базе рекламаций
df_gp_not_act.index = df_gp_not_act.index + 3
# Присваиваем наименование столбцу с номерами строк датафрейма (индексу строк)
df_gp_not_act.index.name = "Строка базы"

print(df_gp_not_act)

# сохраняем в файл .txt
with open(
    f"//Server/otk/Support_files_не_удалять!!!/НЕТ актов ГП - {date.today()}.txt",
    "w",
    encoding="utf-8",
) as f:
    print(
        f"\n\n\tПеречень актов рекламаций по которым НЕТ актов исследования ГП на {date.today()}",
        file=f,
    )
    f.write(df_gp_not_act.to_string())

print("\nОтчет по ГП записан.")
