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

# print(df)
"""
    Дата_регистрации_акта_НП Наименование_детали Обозначение_детали  ...  Операция  Описание_дефектов_и_причин  Основание_для_списания (КТУ, акт, протокол и др.)
0        2024-01-18 00:00:00  корпус компрессора        700-1118020  ...       020                         NaN                       ММЗ акт №15-4461 от 28.11.23
1        2024-01-10 00:00:00            шестерня         50-1403228  ...       005          замена инструмента                                                NaN
2        2024-01-10 00:00:00            шестерня        240-1403228  ...       005          замена инструмента                                                NaN
3        2024-01-10 00:00:00            шестерня        245-1403228  ...       005          замена инструмента                                                NaN
4        2024-01-10 00:00:00            шестерня         А29.01.200  ...       005          замена инструмента                                                NaN
..                       ...                 ...                ...  ...       ...                         ...                                                ...
491                      NaN                 NaN                NaN  ...       NaN                         NaN                                                NaN
492                      NaN                 NaN                NaN  ...       NaN                         NaN                                                NaN
493                      NaN                 NaN                NaN  ...       NaN                         NaN                                                NaN
494                      NaN                 NaN                NaN  ...       NaN                         NaN                                                NaN
495                      NaN                 NaN                NaN  ...       NaN                         NaN                                                NaN
"""
# изменяем тип данных в столбце "Дата_регистрации_акта_НП" на datetime
df["Дата_регистрации_акта_НП"] = pd.to_datetime(
    df["Дата_регистрации_акта_НП"], errors="coerce"
)

# удаляем пустые строки в столбце "Сумма_по_акту"
df.dropna(subset=["Сумма_по_акту"], inplace=True)

# -------------------------------------------- ТОП 10 по ВСЕМ месяцам года ------------------------------------------------------
# вспомогательный словарь номера и наименования месяца года
dct = {
    1: "январь",
    2: "февраль",
    3: "март",
    4: "апрель",
    5: "май",
    6: "июнь",
    7: "июль",
    8: "август",
    9: "сентябрь",
    10: "октябрь",
    11: "ноябрь",
    12: "декабрь",
}

# сохраняем в переменную год по которому делаем анализ
year = int(df["Дата_регистрации_акта_НП"].dt.year.unique()[0])
# создаем список месяцев года по которым есть информация в базе
monthes = df["Дата_регистрации_акта_НП"].dt.month.unique().tolist()

# открываем файл для записи (создаем новый или очищаем существующий)
with open(
    f"ОТЧЕТЫ/2.1 Отчет ТОП-10 по месяцам {year} года.txt", "w", encoding="utf-8"
) as file:
    pass

# циклом по номерам месяцев (ключам словаря)
for key in dct.keys():
    # если номер месяца есть в списке
    if key in monthes:
        # из исходного фрейма по номеру месяца оставляем только нужные столбцы
        df_tmp = df[df["Дата_регистрации_акта_НП"].dt.month == key][
            ["Наименование_детали", "Обозначение_детали", "Количество", "Сумма_по_акту"]
        ]

        # группируем по Наименованию и Обозначению и считаем суммы по столбцам Количество и Сумма по акту
        df_tmp_top = (
            df_tmp.groupby(["Наименование_детали", "Обозначение_детали"])
            .agg({"Количество": sum, "Сумма_по_акту": sum})
            .astype({"Количество": "int"})
        )
        # Сумма по столбцу 'Сумма_по_акту' таблицы df_tmp_top
        total_df_top = df_tmp_top["Сумма_по_акту"].sum()

        # формируем итоговый фрейм ТОП-10 по столбцу Сумма по акту
        res = df_tmp_top.nlargest(10, columns="Сумма_по_акту")
        # Сумма по столбцу 'Сумма_по_акту' таблицы res
        total_res = res["Сумма_по_акту"].sum()
        # добавляем столбец с кумулятивной суммой по столбцу Сумма по акту
        # res["С накоплением"] = res["Сумма_по_акту"].cumsum().round(2)

        # доля списания в выборке ТОП от общей суммы за месяц
        procent = round(total_res / total_df_top * 100, 2)

        # выводим в консоль
        print(f"\n\tДанные за {dct[key]} {year}")
        print(res)
        print()
        print(f"Сумма списания брака в выборке ТОП: {total_res} руб.")
        print(
            f"Сумма в выборке ТОП составляет {procent}% от общей суммы списания за {dct[key]}."
        )

        # сохраняем в файл .txt по номеру года
        with open(
            f"ОТЧЕТЫ/2.1 Отчет ТОП-10 по месяцам {year} года.txt", "a", encoding="utf-8"
        ) as file:
            print(f"\n\n\tДанные за {dct[key]} {year}", file=file)
            print(res, file=file)
            print(file=file)
            print(f"Сумма списания брака в выборке ТОП: {total_res} руб.", file=file)
            print(
                f"Сумма в выборке ТОП составляет {procent}% от общей суммы списания за {dct[key]}.",
                file=file,
            )

print("Файл записан")
