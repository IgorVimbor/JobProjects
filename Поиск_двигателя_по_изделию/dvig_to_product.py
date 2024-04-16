# модуль для определения номера двигателя и акта рекламации по номеру изделия

import pandas as pd
from datetime import date


year_now = date.today().year  # текущий год
file = '//Server/otk/1 ГАРАНТИЯ на сервере/' + str(year_now) + '-2019_ЖУРНАЛ УЧЁТА.xls'  # имя файла с учетом текущего года


# класс для определения номера двигателя и акта рекламации по номеру изделия
class Search:
    def __init__(self, year: int) -> None:
        self.year = str(year)    # год поиска (в каком году базы будем исать информацию)
        self.num_prod = tuple()
        sheet = self.year        # делаем активным Лист базы ОТК по году поиска
        self.df = pd.read_excel(file, sheet_name=sheet, header=1)  # читаем файл Excel и создаем датафрейм

    def all_num_prod(self):
        k = 3  # поправочный коэффициент нумерации строк
        self.num_prod = tuple(self.df['Заводской номер изделия'][3-k:1000-k])  # кортеж номеров изделий из базы
        return self.num_prod   # возвращаем кортеж номеров изделий
    
    def get_answer(self, value):
        if value not in self.all_num_prod():  # есть ли номер изделия в базе: True - есть, False - нет
            return 0
        res = self.df[self.df['Заводской номер изделия'] == value].index[0]  # номер строки по номеру изделия
        vid = self.df.iloc[res]['Наименование изделия']  # наименование изделия
        dvg = self.df.iloc[res]['Номер двигателя']       # номер двигателя
        act = self.df.iloc[res]['Номер рекламационного акта ПРИОБРЕТАТЕЛЯ изделия']  # номер рекламационного акта
        return res, vid, dvg, act

    def show(self, value):
        print('-'*50)
        for v in value.split():
            v = str(int(v))         # переводим в int и обратно в str для удаления незначащих нулей в вводимых номерах
            if self.get_answer(v):
                res, vid, dvg, act = self.get_answer(v)
                print(f'Изделие № {v} - {vid} - cтрока {res+3}')
                print(f'Двигатель № {dvg}, акт рекламации № {act}\n')
            else:
                print(f'Изделия № {v} нет в базе {self.year} года\n')
        print('-'*50)


if __name__ == '__main__':
    year = 2023                       # вводим год поиска
    product = '16503 48799 030943'    # вводим номера изделий через пробел (можно с незначащим нулем)

    pr = Search(year)                 # создаем экземпляр класса
    
    pr.show(product)                  # выводим результат
