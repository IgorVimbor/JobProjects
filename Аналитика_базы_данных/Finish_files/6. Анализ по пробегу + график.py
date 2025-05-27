import pandas as pd
import numpy as np
from datetime import date
import warnings
import matplotlib.pyplot as plt
import seaborn as sns

warnings.simplefilter(action="ignore", category=Warning)


def value_probeg(str_in):
    str_in = str(str_in).replace(",", ".").replace(" ", "").rstrip(".")

    if str_in.endswith("м/ч"):  # если строка заканчивается на м/ч
        # срезом убираем м/ч, переводим в float и умножаем на 9
        str_in = float(str_in[:-3]) * 9

    elif str_in.endswith("км"):  # если строка заканчивается на км
        # срезом убираем км и переводим в float
        str_in = float(str_in[:-2])

    return str_in


product = "водяной насос"  # изделие по которому будут строится графики
client = "ЯМЗ - эксплуатация"  # потребитель


df_all = pd.read_excel(
    "2025-2019_ЖУРНАЛ УЧЁТА.xlsm",
    sheet_name="2025",
    usecols=[
        "Период выявления дефекта (отказа)",
        "Наименование изделия",
        "Обозначение изделия",
        "Дата изготовления изделия",
        "Транспортное средство (установка)",
        "Пробег, наработка",
    ],
    header=1,
)

# делаем выборку из общей базы по наименованию потребителя и изделия
df = df_all[(df_all["Период выявления дефекта (отказа)"] == client) & (df_all["Наименование изделия"] == product)]

df = df[(df["Пробег, наработка"].str.contains("км") == True) | (df["Пробег, наработка"].str.contains("м/ч") == True)]

# Применяем функцию преобразования
df["Пробег, наработка"] = df["Пробег, наработка"].map(value_probeg)

df = df[df["Пробег, наработка"] < 230000]

# Определяем максимальное значение для создания бинов
max_value = df["Пробег, наработка"].max()
print(max_value)

# Создаем бины с шагом 5000
bins = np.arange(0, max_value+2000, 10000)
print(bins)

# Создаем новый столбец с бинами
df["Пробег_бин"] = pd.cut(df["Пробег, наработка"], bins=bins, right=False)
# print(df)

# группируем по бинам
ser = df.groupby("Пробег_бин")["Пробег, наработка"].count()
print(ser)

# Строим график распределения по бинам
plt.figure(figsize=(12, 6))
sns.countplot(data=df, x="Пробег_бин")
plt.xticks(rotation=45)
plt.title("Распределение данных по пробегу с шагом 10000")
plt.xlabel("Пробег, наработка (бин)")
plt.ylabel("Количество")
plt.tight_layout()
plt.show()
