# Формирование отчета по датам уведомления (поступления сообщения в ОТК)
# с привязкой к номерам актов исследования для рассмотрения претензий ЯМЗ

import pandas as pd
from datetime import date
import warnings

# Команда для удаления предупреждений Pandas в консоли
warnings.simplefilter(action="ignore", category=Warning)
# То есть предупреждения типа:
''' A value is trying to be set on a copy of a slice from a DataFrame.
    Try using .loc[row_indexer,col_indexer] = value instead  '''
# не будут показываться

# --------------------- Вспомогательные функции и переменные ----------------------------

year_now = str(date.today().year)    # текущий год
file = '//Server/otk/1 ГАРАНТИЯ на сервере/' + \
    str(year_now) + '-2019_ЖУРНАЛ УЧЁТА.xls'  # имя файла с учетом текущего года

# ----------------------------------------------------------------------------------------


class Date_to_act():
    def __init__(self, year: int, client: str, product: str, nums_act: list) -> None:
        self.year = str(year)
        self.client = client
        self.product = product
        self.acts = nums_act

    @staticmethod
    def get_num(str_in):
        """функция срезом из строки выделяет номер акта и переводит в числовой тип"""
        return int(str(str_in).strip()[7:10])

    def get_frame(self):
        """функция возвращает датафрейм с двумя столбцами: дата уведомления и номер акта"""
        # считываем файл Excel и создаем датафрейм
        df = pd.read_excel(
            file,
            sheet_name=self.year,
            usecols=[
                'Дата поступления сообщения в ОТК',
                'Период выявления дефекта (отказа)',
                'Наименование изделия',
                'Номер акта исследования',
                'Дата акта исследования'],
            header=1)

        # делаем выборку из общей базы по наименованию потребителя и изделия
        df_client = df[(df['Период выявления дефекта (отказа)'] == self.client) & (
            df['Наименование изделия'] == self.product)]

        # удаляем пустые строки, в которых нет номеров актов
        df_cl = df_client.dropna(subset=['Номер акта исследования'])

        # переводим номер акта в числовой тип
        df_cl['Номер акта исследования'] = df_cl['Номер акта исследования'].map(
            self.get_num)

        # датафрейм с датами уведомления и номерами актов исследования
        df_cl = df_cl[['Номер акта исследования', 'Дата акта исследования',
                       'Дата поступления сообщения в ОТК']]

        # итоговый датафрейм с датами уведомления и номерами актов, сортированный по номеру акта
        res_df = df_cl[df_cl['Номер акта исследования'].isin(self.acts)].sort_values(
            'Номер акта исследования').set_index('Номер акта исследования')

        # изменяем вывод даты на '%d.%m.%Y'
        res_df['Дата поступления сообщения в ОТК'] = pd.to_datetime(
            res_df['Дата поступления сообщения в ОТК']).dt.strftime('%d.%m.%Y')

        res_df['Дата акта исследования'] = pd.to_datetime(
            res_df['Дата акта исследования']).dt.strftime('%d.%m.%Y')

        return res_df


if __name__ == '__main__':

    client = 'ЯМЗ - эксплуатация'   # потребитель
    product = 'водяной насос'       # изделие по которому будет формироваться отчет

    # список актов исследования из претензий
    nums_act = [623, 669, 668, 622, 671, 621, 674, 620, 670, 676, 672, 667, 683,
                684, 616, 529, 590, 619, 617, 589, 531, 526, 530, 516, 682]

    result = Date_to_act(2023, client, product, nums_act).get_frame()
    print(result)
    print('Количество актов в списке -', len(result))

    result.to_excel(
        '//Server/otk/Support_files_не_удалять!!!/Претензии_даты для ПЭО.xlsx')
    print('Файл записан')

    # with open('///Server/otk/Support_files_не_удалять!!!/Претензии_даты для ПЭО.txt', 'w') as file:
    #     print(result, file=file)
    #     print('Файл записан')
