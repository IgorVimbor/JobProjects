import pandas as pd
from datetime import datetime, date
import warnings


# Команда для удаления предупреждений Pandas в консоли
warnings.simplefilter(action="ignore", category=Warning)
# То есть предупреждения типа:
""" A value is trying to be set on a copy of a slice from a DataFrame.
    Try using .loc[row_indexer,col_indexer] = value instead  """
# не будут показываться


year = 2023  # год поиска
client = "ЯМЗ - эксплуатация"  # Потребитель
product = "водяной насос"  # изделие по которому будет формироваться отчет

# наименования столбцов из базы для формирования выборки по потребителю
name_cols = {
    1: "Дата изготовления изделия",
    2: "Пробег, наработка",
    3: "Заявленный дефект изделия",
    4: "Номер акта исследования",
    5: "Виновник дефекта - БЗА",
    6: "Виновник дефекта - потребитель",
    7: "Изделие соответствует  ТУ",
    8: "Виновник не установлен",
    9: "Причины возникновения дефектов",
    10: "Пояснения к причинам возникновения дефектов",
    11: "Поставщик дефектного комплектующего",
}

# перечень столбцов по которым будет делаться анализ
cols_selection = (1, 9, 10, 11)

year_now = date.today().year  # текущий год

# расположение базы ОТК и имя файла с учетом текущего года
file_in = f"//Server/otk/1 ГАРАНТИЯ на сервере/{str(year_now)}-2019_ЖУРНАЛ УЧЁТА.xlsx"

# расположение файла в который будет сохраняться отчет
file_out = (
    f"//Server/otk/ОТЧЕТНОСТЬ БЗА/АНАЛИЗ дефектности БЗА/Отчет за {year} по_{client}_"
    + str(date.today())
    + ".txt"
)

sheet = str(year)  # делаем активным Лист базы ОТК по году поиска
# читаем файл Excel и создаем датафрейм
df = pd.read_excel(file_in, sheet_name=sheet, header=1)
k = 3  # поправочный коэффициент нумерации строк


# полная выборка из базы по двум столбцам (client и product), где & = И, | = ИЛИ
all_frame = df[
    (df["Период выявления дефекта (отказа)"] == client)
    & (df["Наименование изделия"] == product)
]
# print(all_frame.shape)  # размер датафрейма (строк, столбцов) ... (160, 68)

# выборка по столбцам из полной выборки
frame = all_frame[[v for v in name_cols.values()]]
# print(frame.shape)    # размер датафрейма


def show_not_isnull():
    """функция возвращает количество НЕпустых строк (null) в столбцах"""
    return all_frame.shape[0] - frame.isnull().sum()


def get_lst_sort(iterable):
    """
    функция создания сортированного списка
    вначале создается словарь: ключ - параметр, значение - количество повторов по параметру
    затем сортируем по количеству повторов (по убыванию) и сохраняем в список
    """
    dct_count = {}
    for t in iterable:
        dct_count.setdefault(t, iterable.count(t))

    for key in dct_count.keys():
        if type(key) == date:
            lst_sort_value = sorted(
                dct_count.items(),
                key=lambda x: (x[1], datetime.strptime(x[0], "%m.%y")),
                reverse=True,
            )
        else:
            lst_sort_value = sorted(dct_count.items(), key=lambda x: x[1], reverse=True)

    return lst_sort_value


# формируем сводные данные по отдельным столбцам (список кортежей данных по столбцам)
lst_data = []
for num in cols_selection:
    lst_data.append(get_lst_sort(tuple(frame[name_cols[num]].dropna())))

# результаты анализа записываем в файл
with open(file_out, "w", encoding="utf-8") as res_file:
    # информация по общему количеству рекламаций по потребителю
    print(
        f"\n\nОбщее количество рекламаций в базе по изделию\n{product} на {client}: {frame.shape[0]}",
        file=res_file,
    )
    print(
        f"\nКоличество ячеек с информацией по столбцам:\n",
        "-" * 55,
        sep="",
        file=res_file,
    )
    print(show_not_isnull(), file=res_file)
    print(file=res_file)

    # информация по столбцам из списка cols_selection
    for num, lst in zip(cols_selection, lst_data):
        print(name_cols[num], file=res_file)
        print("-" * 50, file=res_file)
        for key, value in lst:
            print(f"{key}: {value}", file=res_file)
        print(file=res_file)
    print(file=res_file)

# сообщение в консоль об успешной записи файла
print("Файл записан")
