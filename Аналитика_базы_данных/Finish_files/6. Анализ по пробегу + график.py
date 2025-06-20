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


year_now = date.today().year  # текущий год
# имя файла с учетом текущего года
file = "//Server/otk/1 ГАРАНТИЯ на сервере/" + str(year_now) + "-2019_ЖУРНАЛ УЧЁТА.xlsm"

product = "водяной насос"  # изделие по которому будут строится графики
client = "ЯМЗ - эксплуатация"  # потребитель
year = "2025"  # год по которому проводится анализ


df_all = pd.read_excel(
    file,
    sheet_name=year,
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
# df = df[df["Пробег, наработка"] < 10000]
print(len(df))

# Определяем максимальное значение для создания бинов
max_value = df["Пробег, наработка"].max()
print(max_value)

# Создаем бины с шагом (1000, 5000 или 10000)
bins = np.arange(0, max_value+500, 10000)
print(bins)

# Создаем новый столбец с бинами
df["Пробег_бин"] = pd.cut(df["Пробег, наработка"], bins=bins, right=False)
# print(df)

# группируем по бинам
ser = df.groupby("Пробег_бин")["Пробег, наработка"].count()
print(ser)
ser.to_excel(f"Количество по диапазонам пробегов - {year}.xlsx")

# Строим график распределения по бинам
plt.figure(figsize=(12, 6))
ax = sns.countplot(data=df, x="Пробег_бин")
ax.bar_label(ax.containers[0], label_type='edge')

plt.xticks(rotation=45)
plt.title(f"Распределение по пробегу с шагом 10000 за {year} год")
plt.legend(fontsize=10, title=f"Всего дефектных изделий {len(df)} шт.")
plt.xlabel("Пробег, наработка (диапазоны)")
plt.ylabel("Количество")
plt.tight_layout()
plt.show()
