import pandas as pd
import numpy as np
from datetime import date
import warnings

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
# --------------------------------------------------------------------------------------------------

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

df1_diff_mean = round(df1["DIFF"].mean(), 2)
# print(df1_diff_mean)  # 4.79
