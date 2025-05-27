import pandas as pd
from datetime import datetime, date


year_now = date.today().year  # текущий год
file = '//Server/otk/1 ГАРАНТИЯ на сервере/' + str(year_now) + '-2019_ЖУРНАЛ УЧЁТА.xls'  # имя файла с учетом текущего года

sheet = str(year_now)         # делаем активным Лист базы ОТК по году поиска
df = pd.read_excel(file, sheet_name=sheet, header=1)  # читаем файл Excel и создаем датафрейм
k = 3  # поправочный коэффициент нумерации строк

# выборка из базы водяных насосов ЯМЗ (сразу по двум столбцам, где & - И, | - ИЛИ)
nasos_ymz = df[
    (df['Период выявления дефекта (отказа)'] == 'ЯМЗ - эксплуатация') 
    & 
    (df['Наименование изделия'] == 'водяной насос')
    ]

# строки из датафрейма nasos_ymz по наименованию колонок
defect_nasos_ymz = nasos_ymz[['Пояснения к причинам возникновения дефектов', 'Дата изготовления изделия']]
# print(defect_nasos_ymz.isnull().sum())  # количество пустых строк (null) в столбцах

defect_ymz = defect_nasos_ymz.dropna()  # удаляем пустые строки (null)
# print(defect_ymz)  # выводим выборку по дефектам и датам

tp_defect = tuple(defect_ymz['Пояснения к причинам возникновения дефектов'])
# [print(t) for t in tp_defect]   # печать кортежа строк из колонки 'Пояснения к причинам дефектов'
# print(len(tp_defect))  # 59

tp_data = tuple(defect_ymz['Дата изготовления изделия'])
# [print(t) for t in tp_data]   # печать кортежа строк из колонки 'Дата изготовления изделия'
# print(len(tp_data))  # 59

dct_defect = {}     # словарь дефектов: ключ - дефект, значение - количество дефектов
for t in tp_defect:
    dct_defect.setdefault(t, tp_defect.count(t))
# сортируем по убыванию количества дефектов
lst_defect = sorted(dct_defect.items(), key=lambda x: x[1], reverse=True)
# выводим на печать данные из словаря дефектов
cnt_defect = 0
print('-'*50)
for key, value in lst_defect:
    cnt_defect += value
    print(f'{key}: {value}')
print('\nОбщее количество:', cnt_defect)
print('-'*50)

dct_data = {}     # словарь дат: ключ - дата, значение - количество дат
for t in tp_data:
    dct_data.setdefault(t, tp_data.count(t))
# сортируем по убыванию количества дефектов, а затем по дате изготовления
lst_data = sorted(dct_data.items(), key=lambda x: (x[1], datetime.strptime(x[0], '%m.%y')), reverse=True)
# выводим на печать данные из словаря дат
cnt_data = 0
print('-'*50)
for key, value in lst_data:
    cnt_data += value
    print(f'{key}:  {value}')
print('\nОбщее количество:', cnt_data)
print('-'*50)
