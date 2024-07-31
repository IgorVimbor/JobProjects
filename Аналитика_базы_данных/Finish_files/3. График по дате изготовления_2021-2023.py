import pandas as pd
from datetime import date
import matplotlib.pyplot as plt
import warnings


# Команда для удаления предупреждений Pandas в консоли
warnings.simplefilter(action="ignore", category=Warning)
# То есть предупреждения типа:
""" A value is trying to be set on a copy of a slice from a DataFrame.
    Try using .loc[row_indexer,col_indexer] = value instead  """
# не будут показываться


client = "ЯМЗ - эксплуатация"  # Потребитель
product = "водяной насос"  # изделие по которому будет формироваться отчет

year_now = date.today().year  # текущий год
# имя файла с учетом текущего года
file = f"//Server/otk/1 ГАРАНТИЯ на сервере/{str(year_now)}-2019_ЖУРНАЛ УЧЁТА.xlsx"

# sheet = str(2023)   # делаем активным Лист базы ОТК по году поиска
df_2023 = pd.read_excel(
    file,
    sheet_name="2023",
    usecols=[
        "Период выявления дефекта (отказа)",
        "Наименование изделия",
        "Дата изготовления изделия",
    ],
    header=1,
)  # читаем файл Excel и создаем датафрейм
# print(df_2023.head())
# print(df_2023.shape)  # (884, 3)

df_2022 = pd.read_excel(
    file,
    sheet_name="2022",
    usecols=[
        "Период выявления дефекта (отказа)",
        "Наименование изделия",
        "Дата изготовления изделия",
    ],
    header=1,
)  # читаем файл Excel и создаем датафрейм

# print(df_2022.head())
# print(df_2022.shape)  # (890, 3)

df_2021 = pd.read_excel(
    file,
    sheet_name="2021",
    usecols=[
        "Период выявления дефекта (отказа)",
        "Наименование изделия",
        "Дата изготовления изделия",
    ],
    header=1,
)  # читаем файл Excel и создаем датафрейм
# print(df_2021.head())
# print(df_2021.shape)  # (801, 3)


ymz_2023 = df_2023[
    (df_2023["Период выявления дефекта (отказа)"] == client)
    & (df_2023["Наименование изделия"] == product)
]
ymz_2023["Дата изготовления изделия"] = pd.to_datetime(
    ymz_2023["Дата изготовления изделия"], format="%m.%y"
)

lst_2023 = list(ymz_2023["Дата изготовления изделия"].dropna())
# print(len(lst_2023))  # 180


ymz_2022 = df_2022[
    (df_2022["Период выявления дефекта (отказа)"] == client)
    & (df_2022["Наименование изделия"] == product)
]
ymz_2022["Дата изготовления изделия"] = pd.to_datetime(
    ymz_2022["Дата изготовления изделия"], format="%m.%y"
)

lst_2022 = list(ymz_2022["Дата изготовления изделия"].dropna())
# print(len(lst_2022))  # 187


ymz_2021 = df_2021[
    (df_2021["Период выявления дефекта (отказа)"] == client)
    & (df_2021["Наименование изделия"] == product)
]
ymz_2021["Дата изготовления изделия"] = pd.to_datetime(
    ymz_2021["Дата изготовления изделия"], format="%m.%y"
)

lst_2021 = list(ymz_2021["Дата изготовления изделия"].dropna())
# print(len(lst_2021))  # 179

# общее количество поступивших сообщений за 2021 - 2023
all_defect = sorted(lst_2023 + lst_2022 + lst_2021)
all_count = len(all_defect)  # 546


# словарь дефектов: ключ - дата, значение - количество дефектов
dct_defect = {}
for t in all_defect:
    dct_defect.setdefault(t.strftime("%m.%y"), all_defect.count(t))

ln = len(dct_defect)  # длина словаря

# формируем список дат изготовления
name_date = [key for key in dct_defect.keys()]

# формируем список количества дефектов
cnt_defect = [value for value in dct_defect.values()]

# создаем график и задаем размеры (ширина, высота)
plt.figure(figsize=(20, 5))
# устанавливаем размер шрифта подписей данных по оси Х
plt.rc("xtick", labelsize=5)
# создаем массив numpy с количеством столбцов диаграммы (количеством дат изготовления)
# index = np.arange(ln)
index = list(range(len(name_date)))

# наносим на график столбцы диаграммы в соответствии с количеством дефектов
plt.bar(index, cnt_defect)
# подписываем столбцы диаграммы по оси Х (даты изготовления)
plt.xticks(index, name_date)

# циклом добавляем число сверху на каждый столбец и устанавливаем его по центру
for x, y in zip(index, cnt_defect):
    plt.text(x, y, f"{y}", ha="center", va="bottom")

# создаем легенду и вносим текст
plt.legend(fontsize=10, title=f"Всего сообщений {all_count}")
# создаем заголовок графика
plt.title(f"Количество сообщений: {product} {client} за 2021 - 2023 год")

# # path = '//Server/otk/1 ГАРАНТИЯ на сервере/' + str(date.today().year) + '-2019_ЖУРНАЛ УЧЁТА.xls'
# plt.savefig(f'//Server/otk/ОТЧЕТНОСТЬ БЗА/АНАЛИЗ дефектности БЗА/Информация по ЯМЗ_2021-2023' + '.pdf')
plt.show()
