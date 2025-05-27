# ВАРИАНТ 1. Используем xlrd (файл .xls)
import xlrd
from datetime import date
import time

start = time.time()
year = date.today().year
path = 'E://' + str(year) + '-2019_ЖУРНАЛ УЧЁТА.xls'
# file = r'//Server/otk/1 ГАРАНТИЯ на сервере/2023-2019_ЖУРНАЛ УЧЁТА.xls'
wb = xlrd.open_workbook(path)  # открываем файл
sheet = wb.sheet_by_name('2022')  # создаем workbook для работы по имени Листа с соответствующим годом

cells_dvigs = tuple(sheet.col_slice(19, 2))
dvg = tuple(str(int(cell.value)) if type(cell.value) is float else cell.value for cell in cells_dvigs)
print(time.time() - start)  # 1.0280585289
print(len(dvg))             # 889
print(dvg.__sizeof__())     # 3568
print(dvg)


# ВАРИАНТ 2. Используем pandas (файл .xlsx)
# import pandas as pd
# from datetime import date
# import time

# start = time.time()
# year = date.today().year  # текущий год
# file = 'E://' + str(year) + '-2019_ЖУРНАЛ УЧЁТА.xlsx'  # имя файла с учетом текущего года
# sheet = '2022'  # год поиска (в каком году базы будем исать информацию)
# df = pd.read_excel(file, sheet_name=sheet, header=1)  # читаем файл Excel  и создаем датафрейм

# k = 3  # поправочный коэффициент нумерации строк
# dvg = tuple(df['Номер двигателя'][3-k:1000-k])  # кортеж номеров двигателей из базы
# print(time.time() - start)  # 2.9341678619
# print(len(dvg))             # 889
# print(dvg.__sizeof__())     # 3568
# print(dvg)


# ВАРИАНТ 3. Используем openpyxl (файл .xlsx)
# import openpyxl
# from datetime import date
# import time

# start = time.time()
# year = date.today().year
# filename1 = 'E://' + str(year) + '-2019_ЖУРНАЛ УЧЁТА.xlsx'
# wb1 = openpyxl.load_workbook(filename1, data_only=True)  # флаг True - считываем только значение ячейки
# ws1 = wb1['2022']    # получаем Лист по имени

# # strok = tuple(value for row in ws1.values for value in row)  # печать всего содержимого всех строк
# dvg = tuple(ws1.cell(row=i, column=20).value for i in range(3, ws1.max_row+1))  # кортеж номеров двигателей из базы
# print(time.time() - start)  # 14.396834897
# print(len(dvg))             # 902
# print(dvg.__sizeof__())     # 3620
# print(dvg)