import pandas as pd
import numpy as np
from datetime import date
import warnings
import matplotlib.pyplot as plt
import seaborn as sns

warnings.simplefilter(action="ignore", category=Warning)


analys_year = 2024  # год, по которому проводим анализ

year_now = date.today().year  # текущий год

# file = f"//Server/otk/1 ГАРАНТИЯ на сервере/{str(year_now)}-2019_ЖУРНАЛ УЧЁТА.xlsx"
file_home = f"{str(year_now)}-2019_ЖУРНАЛ УЧЁТА.xlsx"

df = pd.read_excel(
    file_home,
    sheet_name=str(analys_year),
    usecols=[
        "Дата поступления сообщения в ОТК",
        "Период выявления дефекта (отказа)",
        "Наименование изделия",
        "Обозначение изделия",
        "Дата поступления изделия",
        "Дата акта исследования",
    ],
    header=1,
)

# если в ячейке "Дата поступления изделия" указана не дата, а значение, содержащее слово "фото" - заменяем
# на значение в ячейке "Дата поступления сообщения в ОТК", если в ней есть значение, а если нет - на None
df.loc[
    df["Дата поступления изделия"].str.contains("фото") == True,
    "Дата поступления изделия",
] = df["Дата поступления сообщения в ОТК"].where(
    df["Дата поступления сообщения в ОТК"].notnull(), None
)

# удаляем строки, где отсутствует дата поступления на завод
df = df.dropna(subset=["Дата поступления изделия"])

# если в ячейке "Дата акта исследования" записаны несколько дат, то оставляем последнюю дату
df.loc[
    df["Дата акта исследования"].str.contains("\n") == True,
    "Дата акта исследования",
] = df["Дата акта исследования"].map(lambda x: str(x).split("\n")[-1])

# переводим тип данных в столбцах в datetime64
df[["Дата поступления изделия", "Дата акта исследования"]] = df[
    ["Дата поступления изделия", "Дата акта исследования"]
].apply(pd.to_datetime)

# -----------------------------------------------------------------------------------
# датафрейм изделий АСП по которым нет актов
df_asp_not_act = df[
    (df["Период выявления дефекта (отказа)"].str.contains("АСП") == True)
    & (df["Дата акта исследования"].isnull())
]
# print(df_asp_not_act)

# датафрейм изделий ГП по которым нет актов
df_gp_not_act = df[
    (df["Период выявления дефекта (отказа)"].str.contains("эксплуатация") == True)
    & (df["Дата акта исследования"].isnull())
]
# print(df_gp_not_act)
# ------------------------------------------------------------------------------------

# в столбце "Дата акта исследования" заменяем отсутствующие данные сегодняшней датой
df["Дата акта исследования"] = (
    df["Дата акта исследования"].fillna(date.today()).apply(pd.to_datetime)
)

# создаем новый столбец в разницей между датой акта и датой поступления
df["DIFF"] = (
    df["Дата акта исследования"] - df["Дата поступления изделия"]
) / np.timedelta64(1, "D")

# print(df.info())
"""
Data columns (total 7 columns):
 #   Column                             Non-Null Count  Dtype
---  ------                             --------------  -----
 0   Дата поступления сообщения в ОТК   298 non-null    datetime64[ns]
 1   Период выявления дефекта (отказа)  432 non-null    object
 2   Обозначение изделия                432 non-null    object
 3   Наименование изделия               432 non-null    object
 4   Дата поступления изделия           432 non-null    datetime64[ns]
 5   Дата акта исследования             432 non-null    datetime64[ns]
 6   DIFF                               432 non-null    float64
dtypes: datetime64[ns](3), float64(1), object(3)
"""

# -------------------------------------- Общая средняя продолжительность исследования -------------------------------------

# находим среднее и медианное значение
df_diff_mean = round(df["DIFF"].mean(), 2)  # 4.79
df_diff_median = round(df["DIFF"].median(), 2)  # 2.0

print("-" * 60)
print(f"Общая средняя продолжительность исследования - {df_diff_mean} дней")
print(f"Общая медианная продолжительность исследования - {df_diff_median} дней")

# ----------------------------------------- Продолжительность исследования по АСП ------------------------------------------

df2 = df[df["Период выявления дефекта (отказа)"].str.contains("АСП") == True]
# print(df2.info())
"""
Data columns (total 7 columns):
 #   Column                             Non-Null Count  Dtype
---  ------                             --------------  -----
 0   Дата поступления сообщения в ОТК   4 non-null      datetime64[ns]
 1   Период выявления дефекта (отказа)  48 non-null     object
 2   Обозначение изделия                48 non-null     object
 3   Наименование изделия               48 non-null     object
 4   Дата поступления изделия           48 non-null     datetime64[ns]
 5   Дата акта исследования             48 non-null     datetime64[ns]
 6   DIFF                               48 non-null     float64
dtypes: datetime64[ns](3), float64(1), object(3)
"""

# удаляем строки с 855 водяным ЯМЗ и сегодняшним приходом
df2 = df2[
    (~df2["Обозначение изделия"].isin(["855.1307010-10", "8.8402"]))
    & (df2["Дата поступления изделия"].dt.day != date.today().day)
]

# сортируем фрейм по убыванию значений стобца "DIFF" и оставляем только строки, где "DIFF" > 5
df2_sort = df2.sort_values(by="DIFF", ascending=False)[df2["DIFF"] >= 14]
# print(df2_sort)

# находим среднее и медианное значение
df2_diff_mean = round(df2["DIFF"].mean(), 2)  # 20.11
df2_diff_median = round(df2["DIFF"].median(), 2)  #  5.0

print("-" * 60)
print(f"Средняя продолжительность исследования по АСП - {df2_diff_mean} дней")
print(f"Медианная продолжительность исследования по АСП - {df2_diff_median} дней")

# ----------------------------------------- Продолжительность исследования по ГП -------------------------------------------

df3 = df[df["Период выявления дефекта (отказа)"].str.contains("эксплуатация") == True]
# print(df3.info())
"""
Data columns (total 7 columns):
 #   Column                             Non-Null Count  Dtype
---  ------                             --------------  -----
 0   Дата поступления сообщения в ОТК   293 non-null    datetime64[ns]
 1   Период выявления дефекта (отказа)  352 non-null    object
 2   Обозначение изделия                352 non-null    object
 3   Наименование изделия               352 non-null    object
 4   Дата поступления изделия           352 non-null    datetime64[ns]
 5   Дата акта исследования             352 non-null    datetime64[ns]
 6   DIFF                               352 non-null    float64
dtypes: datetime64[ns](3), float64(1), object(3)
"""

# сортируем фрейм по убыванию значений стобца "DIFF" и оставляем только строки, где "DIFF" > 5
df3_sort = df3.sort_values(by="DIFF", ascending=False)[df3["DIFF"] >= 14]
# print(df3_sort)

# находим среднее и медианное значение
df3_diff_mean = round(df3["DIFF"].mean(), 2)  # 5.86
df3_diff_median = round(df3["DIFF"].median(), 2)  #  3.0

print("-" * 60)
print(f"Средняя продолжительность рассмотрения по ГП - {df3_diff_mean} дней")
print(f"Медианная продолжительность рассмотрения по ГП - {df3_diff_median} дней")
print("-" * 60)

# ----------------------------------------------------- Результат ----------------------------------------------------------

data = [
    [df_diff_mean, df2_diff_mean, df3_diff_mean],
    [df_diff_median, df2_diff_median, df3_diff_median],
]

result = pd.DataFrame(
    data,
    index=["Среднее значение", "Медианное значение"],
    columns=["В целом", "Конвейер", "Эксплуатация"],
)
print(result)

# ---------------------------------------------- Строим графики по отдельности ----------------------------------------------

# # строим общую гистограмму
# sns.histplot(data=df, x="DIFF", kde=True)
# plt.xlim(-2, 110)
# plt.ylim(0, 60)
# plt.title("Исследование в целом\n(значения по оси Y ограничены для лучшей визуализации)")
# # plt.show()

# # строим гистограмму по АСП
# sns.histplot(data=df2, x="DIFF", kde=True)
# plt.xlim(-1, 110)
# # plt.ylim(0, 30)
# plt.title("Исследование по АСП")
# # plt.show()

# # строим гистограмму по ГП
# sns.histplot(data=df3, x="DIFF", kde=True)
# plt.xlim(-1, 40)
# # plt.ylim(0, 100)
# plt.title("Исследование по ГП")
# # plt.show()

# --------------------------------------- Объединенный рисунок из трех гистограмм -------------------------------------------------

# укзываем количество строк и столбцов на рисунке, размеры рисунка
fig, axes = plt.subplots(nrows=1, ncols=3, figsize=(15, 5))

#    вариант 1 - простые гистограммы Matplotlib
# axes[0].hist(df["DIFF"], df["DIFF"].count())
# axes[1].hist(df2["DIFF"], df2["DIFF"].count())
# axes[2].hist(df3["DIFF"], df3["DIFF"].count())
# plt.show()

#    вариант 2 - гистограммы Seaborn
# строим общую гистограмму
sns.histplot(data=df, x="DIFF", kde=True, ax=axes[0])
axes[0].set_title("Исследование в целом")
axes[0].set_xlim(-2, 110)
axes[0].set_ylim(0, 60)
axes[0].set_xlabel("Количество дней")
axes[0].set_ylabel(
    "Количество исследований\n(значения ограничены для лучшей визуализации)"
)

# строим гистограмму по АСП
sns.histplot(data=df2, x="DIFF", kde=True, ax=axes[1])
axes[1].set_title("Исследование по АСП")
axes[1].set_xlim(-1, 110)
# axes[1].set_ylim(0, 30)
axes[1].set_xlabel("Количество дней")
axes[1].set_ylabel("Количество исследований")

# строим гистограмму по ГП
sns.histplot(data=df3, x="DIFF", kde=True, ax=axes[2])
axes[2].set_title("Исследование по ГП")
axes[2].set_xlim(-1, 40)
# axes[2].set_ylim(0, 100)
axes[2].set_xlabel("Количество дней")
axes[2].set_ylabel("Количество исследований")

# раздвигаем графики друг от друга по ширине
fig.subplots_adjust(wspace=0.3)

# добавляем заголовок
fig.suptitle(f"{analys_year} год", fontsize=16)

plt.show()
