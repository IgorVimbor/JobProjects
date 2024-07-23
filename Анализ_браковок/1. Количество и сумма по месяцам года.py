import pandas as pd
from datetime import date
import matplotlib.pyplot as plt
import warnings


# Команда для удаления предупреждений Pandas в консоли
warnings.simplefilter(action="ignore", category=Warning)

# -------------------------------------- Считываем файл и создаем фрейм ----------------------------------------
# "example_files/ЖУРНАЛ УЧЕТА актов о браке_2020-2024.xls"
# считываем данные из файла Excel и создаем фрейм
df = pd.read_excel(
    "//Server/otk/2 ИННА/Списание БРАКА по ЦЕХАМ/ЖУРНАЛ УЧЕТА актов о браке_2020-2024.xlsx",
    sheet_name="2024",
    usecols=[
        "Дата_регистрации_акта_НП",
        "Наименование_детали",
        "Обозначение_детали",
        "Количество",
        "Сумма_по_акту",
        "ПРИЧИНА",
        "ВИНОВНИК",
        "Цех_участок",
        "Операция",
        "Описание_дефектов_и_причин",
        "Основание_для_списания (КТУ, акт, протокол и др.)",
    ],
    header=1,
)

# изменяем тип данных в столбце "Дата_регистрации_акта_НП" на datetime
df["Дата_регистрации_акта_НП"] = pd.to_datetime(
    df["Дата_регистрации_акта_НП"], errors="coerce"
)

# удаляем пустые строки в столбце "Сумма_по_акту"
df.dropna(subset=["Сумма_по_акту"], inplace=True)
# описание фрейма после удаления пустых строк
"""
#   Column                                             Non-Null Count  Dtype
---  ------                                             --------------  -----
 0   Дата_регистрации_акта_НП                           158 non-null    datetime64[ns]
 1   Наименование_детали                                158 non-null    object
 2   Обозначение_детали                                 158 non-null    object
 3   Количество                                         158 non-null    float64
 4   Сумма_по_акту                                      158 non-null    float64
 5   ПРИЧИНА                                            158 non-null    float64
 6   ВИНОВНИК                                           158 non-null    float64
 7   Цех_участок                                        158 non-null    object
 8   Операция                                           156 non-null    object
 9   Описание_дефектов_и_причин                         153 non-null    object
 10  Основание_для_списания (КТУ, акт, протокол и др.)  2 non-null      object
dtypes: datetime64[ns](1), float64(4), object(6)
memory usage: 11.1+ KB
"""

# -------------------------------------------- СУММА по МЕСЯЦАМ ГОДА -----------------------------------------------------
# группируем по месяцу года и считаем сумму по столбцам "Количество" и "Сумма_по_акту" за месяц,
# переводим итог по столбцу "Количество" в int и выводим только столбцы "Количество" и "Сумма_по_акту"
df_sum = (
    df.groupby(df["Дата_регистрации_акта_НП"].dt.month)
    .agg({"Количество": sum, "Сумма_по_акту": sum})
    .astype({"Количество": "int"})[["Количество", "Сумма_по_акту"]]
)

# вводим новый столбец "Количество наименований" - группируем по месяцу года и считаем уникальные значения в "Обозначение_детали"
df_sum["Количество наименований"] = df.groupby(df["Дата_регистрации_акта_НП"].dt.month)[
    "Обозначение_детали"
].nunique()

# переименовываем столбец "Количество"
df_sum.rename(columns={"Количество": "Общее количество деталей"}, inplace=True)

# изменяем порядок расположения столбцов
df_sum = df_sum[
    [
        "Общее количество деталей",
        "Количество наименований",
        "Сумма_по_акту",
    ]
]
print(df_sum)
"""
                          Общее количество деталей  Количество наименований  Сумма_по_акту
Дата_регистрации_акта_НП
1                                             1284                       62        8962.80
2                                             1507                       64       15776.26
"""
