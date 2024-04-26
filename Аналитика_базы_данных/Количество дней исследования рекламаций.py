import pandas as pd
import numpy as np
from datetime import date
import warnings
import matplotlib.pyplot as plt
import seaborn as sns

warnings.simplefilter(action="ignore", category=Warning)


year_now = date.today().year  # текущий год

# file = f"//Server/otk/1 ГАРАНТИЯ на сервере/{str(year_now)}-2019_ЖУРНАЛ УЧЁТА.xlsx"
file_home = f"{str(year_now)}-2019_ЖУРНАЛ УЧЁТА.xlsx"

df = pd.read_excel(
    file_home,
    sheet_name="2024",
    usecols=[
        "Период выявления дефекта (отказа)",
        "Наименование изделия",
        "Обозначение изделия",
        "Дата поступления изделия",
        "Дата акта исследования",
    ],
    header=1,
)

# если в строках указана не дата - заменяем на пустую строку
df["Дата поступления изделия"] = df["Дата поступления изделия"].map(
    lambda x: "" if str(x).isalpha() else x
)
# переводим тип данных в столбцах в datetime64
df[["Дата поступления изделия", "Дата акта исследования"]] = df[
    ["Дата поступления изделия", "Дата акта исследования"]
].apply(pd.to_datetime)
# print(df.info())
"""
Data columns (total 5 columns):
 #   Column                             Non-Null Count  Dtype
---  ------                             --------------  -----
 0   Период выявления дефекта (отказа)  486 non-null    object
 1   Обозначение изделия                486 non-null    object
 2   Наименование изделия               486 non-null    object
 3   Дата поступления изделия           432 non-null    datetime64[ns]
 4   Дата акта исследования             388 non-null    datetime64[ns]
dtypes: datetime64[ns](2), object(3)
"""

# -------------------------------------- Общая средняя продолжительность исследования -------------------------------------

# удаляем строки, где отсутствует дата поступления на завод
df1 = df.dropna(subset=["Дата поступления изделия"])
# print(df1.info())
"""
Index: 432 entries, 0 to 480
Data columns (total 5 columns):
 #   Column                             Non-Null Count  Dtype
---  ------                             --------------  -----
 0   Период выявления дефекта (отказа)  432 non-null    object
 1   Обозначение изделия                432 non-null    object
 2   Наименование изделия               432 non-null    object
 3   Дата поступления изделия           432 non-null    datetime64[ns]
 4   Дата акта исследования             388 non-null    datetime64[ns]
dtypes: datetime64[ns](2), object(3)
"""
# создаем новый столбец в разницей между датой акта и датой поступления
df1["DIFF"] = (
    df1["Дата акта исследования"] - df1["Дата поступления изделия"]
) / np.timedelta64(1, "D")

# находим среднее и медианное значение
df1_diff_mean = round(df1["DIFF"].mean(), 2)  # 4.79
df1_diff_median = round(df1["DIFF"].median(), 2)  # 2.0

# строим гистограмму
sns.displot(data=df1, x="DIFF", kde=True)
plt.xlim(-10, 20)
plt.ylim(0, 100)
# plt.show()

# ----------------------------------------- Продолжительность исследования по АСП ------------------------------------------

df2 = df[df["Период выявления дефекта (отказа)"].str.contains("АСП") == True]
# print(df2.info())
"""
Index: 70 entries, 31 to 484
Data columns (total 5 columns):
 #   Column                             Non-Null Count  Dtype
---  ------                             --------------  -----
 0   Период выявления дефекта (отказа)  70 non-null     object
 1   Обозначение изделия                70 non-null     object
 2   Наименование изделия               70 non-null     object
 3   Дата поступления изделия           48 non-null     datetime64[ns]
 4   Дата акта исследования             34 non-null     datetime64[ns]
dtypes: datetime64[ns](2), object(3)
"""

# удаляем строки, где отсутствует дата поступления на завод
df2 = df2.dropna(subset=["Дата поступления изделия"])
# print(df2_not_act.info())
"""
Index: 48 entries, 31 to 385
Data columns (total 5 columns):
 #   Column                             Non-Null Count  Dtype
---  ------                             --------------  -----
 0   Период выявления дефекта (отказа)  48 non-null     object
 1   Обозначение изделия                48 non-null     object
 2   Наименование изделия               48 non-null     object
 3   Дата поступления изделия           48 non-null     datetime64[ns]
 4   Дата акта исследования             34 non-null     datetime64[ns]
dtypes: datetime64[ns](2), object(3)
"""

# удаляем строки с 855 водяным ЯМЗ и сегодняшним приходом
df2 = df2[
    (~df2["Обозначение изделия"].isin(["855.1307010-10", "8.8402"]))
    & (df2["Дата поступления изделия"].dt.day != date.today().day)
]

# датафрейм изделий по которым нет актов
df2_not_act = df2[df2["Дата акта исследования"].isnull()]
"""
   Период выявления дефекта (отказа) Обозначение изделия Наименование изделия Дата поступления изделия Дата акта исследования
32                          ММЗ -АСП      240-1307010-А1        водяной насос               2024-01-15                    NaT
33                          ММЗ -АСП   240-1307010-А1-11        водяной насос               2024-01-15                    NaT
34                          ММЗ -АСП         3LD-1307010        водяной насос               2024-01-15                    NaT
35                          ММЗ -АСП      260-1307116-02        водяной насос               2024-01-15                    NaT
36                         ПАЗ - АСП         ПК 225-К-01           компрессор               2024-01-16                    NaT
37                         ПАЗ - АСП         ПК 225-К-01           компрессор               2024-01-16                    NaT
"""

# в столбце "Дата акта исследования" заменяем отсутствующие данные снгодняшней датой
df2["Дата акта исследования"] = (
    df2["Дата акта исследования"].fillna(date.today()).apply(pd.to_datetime)
)

# создаем новый столбец в разницей между датой акта и датой поступления
df2["DIFF"] = (
    df2["Дата акта исследования"] - df2["Дата поступления изделия"]
) / np.timedelta64(1, "D")
# print(df2)

# находим среднее и медианное значение
df2_diff_mean = round(df2["DIFF"].mean(), 2)  # 20.11
df2_diff_median = round(df2["DIFF"].median(), 2)  #  5.0

# строим гистограмму
sns.displot(data=df2, x="DIFF", kde=True)
plt.xlim(-1, 30)
plt.ylim(0, 30)
# plt.show()

# ----------------------------------------- Продолжительность исследования по ГП -------------------------------------------
