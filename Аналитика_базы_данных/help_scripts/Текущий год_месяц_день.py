from datetime import datetime, date

# today = date.today()
# print('Текущий год:', today.year, type(today.year))
# print('Текущий месяц:', today.month, type(today.month))
# print('Текущий день:', today.day, type(today.day))
# print('Текущая дата:', today.strftime('%d.%m.%Y'), type(today.strftime('%d.%m.%Y')))

lst_day = ['03.21', '03.22', '01.20', '05.21', '04.21']  # список строковых дат

# сортируем список по датам, переведенным в класс datetime
day_sort = sorted(lst_day, key=lambda x: datetime.strptime(x, '%m.%y'), reverse=True)
print(day_sort)    # ['03.22', '05.21', '04.21', '03.21', '01.20']

# day = '03.21'
# dt = datetime.strptime(day, '%m.%y')  # перевод строковой даты в дату объекта класса datetime
# print(dt, type(dt))                   # 2021-03-01 00:00:00  <class 'datetime.datetime'>
# day_obj = dt.strftime('%m.%y')        # обратный перевод из класса datetime в строковый тип
# print(day_obj, type(day_obj))         # 03.21 <class 'str'>
