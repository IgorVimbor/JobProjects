from pprint import pprint
import pandas as pd
from datetime import datetime, date
import matplotlib.pyplot as plt
import numpy as np
import warnings


# Команда для удаления предупреждений Pandas в консоли
warnings.simplefilter(action="ignore", category=Warning)
# То есть предупреждения типа:
''' A value is trying to be set on a copy of a slice from a DataFrame.
    Try using .loc[row_indexer,col_indexer] = value instead  '''
# не будут показываться


year = 2023                     # год поиска
client = 'ЯМЗ - эксплуатация'   # Потребитель
product = 'водяной насос'       # изделие по которому будет формироваться отчет

year_now = date.today().year  # текущий год
file = '//Server/otk/1 ГАРАНТИЯ на сервере/' + \
    str(year_now) + '-2019_ЖУРНАЛ УЧЁТА.xls'  # имя файла с учетом текущего года

sheet = str(year)   # делаем активным Лист базы ОТК по году поиска
# читаем файл Excel и создаем датафрейм
df = pd.read_excel(file, sheet_name=sheet, header=1)
k = 3  # поправочный коэффициент нумерации строк

all_count_defects = df[(df['Период выявления дефекта (отказа)'] == client)
                       &
                       (df['Наименование изделия'] == product)
                       ]

# общее количество поступивших сообщений с начала года
all_count = len(all_count_defects)

# столбец 'Дата изготовления изделия' переводим в формат времени datetime
all_count_defects['Дата изготовления изделия'] = pd.to_datetime(
    all_count_defects['Дата изготовления изделия'], format='%m.%y')

# убираем пустые ячейки
defects = all_count_defects['Дата изготовления изделия'].dropna()

# сортированный кортеж по возрастанию даты
tp_defect = tuple(sorted(defects))

# словарь дефектов: ключ - дата, значение - количество дефектов
dct_defect = {}
for t in tp_defect:
    dct_defect.setdefault(t.strftime('%m.%y'), tp_defect.count(t))

ln = len(dct_defect)   # длина словаря

name_date = []    # инициируем список имен потребителей
cnt_defect = []   # инициируем список количества дефектов

for key, value in dct_defect.items():
    # формируем список имен потребителей
    name_date.append('\n'.join(key.split(' - ')))
    cnt_defect.append(value)   # формируем список количества дефектов
# print(name_user)
# print(cnt_defect_user)

# создаем график и задаем размеры (ширина, высота)
plt.figure(figsize=(15, 5))
# устанавливаем размер шрифта подписей данных по оси Х
plt.rc('xtick', labelsize=6)
# создаем массив numpy с количеством столбцов диаграммы (количеством потребителей)
index = np.arange(ln)
# наносим на график столбцы диаграммы в соответствии с количеством дефектов
plt.bar(index, cnt_defect)
# подписываем столбцы диаграммы по оси Х
plt.xticks(index, name_date)

# циклом добавляем число сверху на каждый столбец и устанавливаем его по центру
for x, y in zip(index, cnt_defect):
    plt.text(x, y, f'{y}', ha='center', va='bottom')

# создаем легенду и вносим текст
plt.legend(fontsize=10, title=f'Всего сообщений {all_count}')
# создаем заголовок графика
plt.title(f'Количество сообщений: {product} {client} с начала {year} года')

# path = '//Server/otk/1 ГАРАНТИЯ на сервере/' + str(date.today().year) + '-2019_ЖУРНАЛ УЧЁТА.xls'
plt.savefig(
    f'//Server/otk/ОТЧЕТНОСТЬ БЗА/АНАЛИЗ дефектности БЗА/Информация за {year}_{product} {client}_' + str(date.today()) + '.pdf')
print('Файл сохранен')
plt.show()
