# Программа выводит в консоль информацию из ВСЕЙ базы:
# - сколько всего сообщений зафиксировано в базе,
# - наименование потребителя и количество сообщений по нему

import pandas as pd
from datetime import date
import warnings


# Команда для удаления предупреждений Pandas в консоли
warnings.simplefilter(action="ignore", category=Warning)
# То есть предупреждения типа:
""" A value is trying to be set on a copy of a slice from a DataFrame.
    Try using .loc[row_indexer,col_indexer] = value instead  """
# не будут показываться


year_now = date.today().year  # текущий год
# имя файла с учетом текущего года
file = f"//Server/otk/1 ГАРАНТИЯ на сервере/{str(year_now)}-2019_ЖУРНАЛ УЧЁТА.xlsm"

sheet = str(year_now)  # делаем активным лист базы ОТК по году поиска
# читаем файл Excel и создаем датафрейм
df = pd.read_excel(file, sheet_name=sheet, header=1)
k = 3  # поправочный коэффициент нумерации строк

# создаем датафрейм по двум столбцам базы - месяцу и потребителю
# сразу удаляем пустые значения методом dropna()
all_count_defects = df[
    ["Месяц регистрации", "Период выявления дефекта (отказа)"]
].dropna()
# print(count_defects_month.head())

print("-" * 50)
# вывод в консоль
print(f"Всего поступило {len(all_count_defects)} сообщений.")

# кортеж названий потребителей из датафрейма (по этому кортежу считаем количество повторений)
tp_defect = tuple(all_count_defects["Период выявления дефекта (отказа)"])

# словарь дефектов: ключ - где выявлен дефект, значение - количество дефектов
dct_defect = {}
for t in tp_defect:
    dct_defect.setdefault(t, tp_defect.count(t))

# сортируем словарь по убыванию количества дефектов и сохраняем в список дефектов
# в котором хранятся кортежи (потребитель, количество дефектов)
lst_defect = sorted(dct_defect.items(), key=lambda x: x[1], reverse=True)

# вывод в консоль
print()

for key, value in lst_defect:
    print(f"{key}: {value}")  # выводим в консоль данные из списка дефектов

print("-" * 50)
