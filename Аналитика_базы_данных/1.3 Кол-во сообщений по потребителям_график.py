import pandas as pd
from datetime import date
import matplotlib.pyplot as plt
import numpy as np
import warnings


# Команда для удаления предупреждений Pandas в консоли
warnings.simplefilter(action="ignore", category=Warning)
# То есть предупреждения типа:
''' A value is trying to be set on a copy of a slice from a DataFrame.
    Try using .loc[row_indexer,col_indexer] = value instead  '''
# не будут показываться


year = 2023                   # год поиска
year_now = date.today().year  # текущий год

file = '//Server/otk/1 ГАРАНТИЯ на сервере/' + \
    str(year_now) + '-2019_ЖУРНАЛ УЧЁТА.xls'   # имя файла с учетом текущего года

sheet = str(year)   # делаем активным Лист базы ОТК по году поиска
# читаем файл Excel и создаем датафрейм
df = pd.read_excel(file, sheet_name=sheet, header=1)
k = 3  # поправочный коэффициент нумерации строк

all_count_defects = df[['Месяц регистрации',
                        'Период выявления дефекта (отказа)']].dropna()
# print(count_defects_month.head())

# общее количество поступивших сообщений с начала года
all_count = len(all_count_defects)

# кортеж названий потребителей из датафрейма (по этому кортежу считаем количество повторений)
tp_defect = tuple(all_count_defects['Период выявления дефекта (отказа)'])

# словарь дефектов: ключ - где выявлен дефект, значение - количество дефектов
dct_defect = {}
for t in tp_defect:
    dct_defect.setdefault(t, tp_defect.count(t))

# сортируем словарь по убыванию количества дефектов и сохраняем в список дефектов
# в котором хранятся кортежи (потребитель, количество дефектов)
lst_defect = sorted(dct_defect.items(), key=lambda x: x[1], reverse=True)
ln = len(lst_defect)   # количество потребителей - длина списка дефектов

name_user = []         # инициируем список имен потребителей
cnt_defect_user = []   # инициируем список количества дефектов

for key, value in lst_defect:
    # формируем список имен потребителей
    name_user.append('\n'.join(key.split(' - ')))
    cnt_defect_user.append(value)   # формируем список количества дефектов

# создаем график и задаем размеры (ширина, высота)
plt.figure(figsize=(15, 5))
# устанавливаем размер шрифта подписей данных по оси Х
plt.rc('xtick', labelsize=6)
# создаем массив numpy с количеством столбцов диаграммы (количеством потребителей)
index = np.arange(ln)
# наносим на график столбцы диаграммы в соответствии с количеством дефектов
plt.bar(index, cnt_defect_user)
# подписываем столбцы диаграммы по оси Х
plt.xticks(index, name_user)

# циклом добавляем число сверху на каждый столбец и устанавливаем его по центру
for x, y in zip(index, cnt_defect_user):
    plt.text(x, y, f'{y}', ha='center', va='bottom')

# создаем легенду и вносим текст
plt.legend(fontsize=10, title=f'Всего сообщений {all_count}')
# создаем заголовок графика
plt.title(f'Количество поступивших сообщений с начала {year} года')

# plt.savefig(f'//Server/otk/ОТЧЕТНОСТЬ БЗА/АНАЛИТИЗ дефектности БЗА/{year}_общее количество сообщений_' + str(date.today()) + '.pdf')
# plt.savefig(f'E:/{year}_общее количество сообщений_' + str(date.today()) + '.pdf')
plt.show()
