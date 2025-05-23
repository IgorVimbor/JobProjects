# Формирование отчета по датам уведомления (поступления сообщения в ОТК)
# с привязкой к номерам актов исследования для рассмотрения претензий ЯМЗ

import pandas as pd
from datetime import date
import warnings
import win32com.client
import os
from openpyxl import load_workbook
from openpyxl.styles import Alignment, Font, Border, Side

# Команда для удаления предупреждений Pandas в консоли
warnings.simplefilter(action="ignore", category=Warning)
# То есть предупреждения типа:
""" A value is trying to be set on a copy of a slice from a DataFrame.
    Try using .loc[row_indexer,col_indexer] = value instead  """
# не будут показываться

# --------------------- Вспомогательные функции и переменные ----------------------------

year_now = str(date.today().year)  # текущий год
# файл с базой данных с учетом текущего года
file = "//Server/otk/1 ГАРАНТИЯ на сервере/" + str(year_now) + "-2019_ЖУРНАЛ УЧЁТА.xlsm"
# файл для записи результата поиска
file_out = "//Server/otk/Support_files_не_удалять!!!/Претензии_даты для ПЭО.xlsx"

# ----------------------------------------------------------------------------------------


class Date_to_act:
    """класс формирует датафрейм с индексом - номер акта и двумя столбцами - дата акта и дата уведомления,
    записывает датафрейм в файл Excel и редактирует стили таблицы в записанном файле"""

    def __init__(self, year: int, client: str, product: str, nums_act: list) -> None:
        self.year = str(year)  # год поиска по базе
        self.client = client  # потребитель
        self.product = product  # наименование изделия
        self.acts = nums_act  # список номеров актов исследования

    @staticmethod
    def get_num(str_in):
        """функция выделяет номер акта и переводит в числовой тип"""
        _, _, num = str(str_in).strip().split()
        act = int(num) if "-" not in num else int(num.split("-")[0])
        return act

    def get_frame(self):
        """функция возвращает датафрейм с индексом - номер акта и двумя столбцами - дата акта и дата уведомления"""
        # считываем файл Excel и создаем датафрейм
        df = pd.read_excel(
            file,
            sheet_name=self.year,
            usecols=[
                "Дата поступления сообщения в ОТК",
                "Период выявления дефекта (отказа)",
                "Наименование изделия",
                "Номер акта исследования",
                "Дата акта исследования",
            ],
            header=1,
        )

        # делаем выборку из общей базы по наименованию потребителя и изделию
        df_client = df[
            (df["Период выявления дефекта (отказа)"] == self.client)
            & (df["Наименование изделия"].str.strip() == self.product)
        ]

        # удаляем пустые строки, в которых нет номеров актов
        df_cl = df_client.dropna(subset=["Номер акта исследования"])

        # переводим номер акта в числовой тип
        df_cl["Номер акта исследования"] = df_cl["Номер акта исследования"].map(self.get_num)

        # датафрейм с датами уведомления и номерами актов исследования
        df_cl = df_cl[
            [
                "Номер акта исследования",
                "Дата акта исследования",
                "Дата поступления сообщения в ОТК",
            ]
        ]

        # итоговый датафрейм с датами уведомления и номерами актов, сортированный по номеру акта
        res_df = df_cl[
            df_cl["Номер акта исследования"].isin(self.acts)
        ].sort_values("Номер акта исследования").set_index("Номер акта исследования")

        # изменяем вывод даты на '%d.%m.%Y'
        res_df["Дата поступления сообщения в ОТК"] = pd.to_datetime(res_df["Дата поступления сообщения в ОТК"]).dt.strftime("%d.%m.%Y")
        res_df["Дата акта исследования"] = pd.to_datetime(res_df["Дата акта исследования"]).dt.strftime("%d.%m.%Y")

        return res_df

    def excel_close_write(self, df: pd.DataFrame):
        """функция записывает итоговый датафрейм в файл Excel переменной file_out.
        Если file_out (файл Excel) открыт, то перед записью файл закрывается и производится запись.
        Args:
            df (pd.DataFrame): итоговый датафрейм с номерами, датами актов и датами сообщений.
        """
        try:  # попытка обратится к файлу
            # переименовываем файл по существующему имени, т.е. оставляем старое имя
            os.rename(file_out, file_out)
            df.to_excel(file_out)  # записываем в файл
            print("Файл записан сразу.")
        except PermissionError:  # если file_out (файл Excel) открыт
            # закрываем файл с помощью win32com.client
            excel = win32com.client.Dispatch("Excel.Application")
            workbook = excel.Workbooks.Open(file_out)
            workbook.Close(SaveChanges=False)  # без сохранения изменений
            # excel.Quit()  # закрываем процесс Excel (все открытые файлы Excel закроются)
            df.to_excel(file_out)  # записываем в файл
            print("Файл закрыт и записан.")

    def transform_excel(self, df: pd.DataFrame):
        """функция редактирует файл Excel (file_out) - вставляет столбец перед столбцом с номерами актов,
        изменяет высоту первой строки с названиями столбцов и их ширину, активирует перенос текста в ячейках
        с названиями столбцов, выравнивает текст в ячейках таблицы по центру и рисует границы по всей таблице.
        Args:
            df (pd.DataFrame): итоговый датафрейм с номерами, датами актов и датами сообщений.
        """
        wb = load_workbook(file_out)  # открываем файл Excel
        sheet = wb["Sheet1"]  # делаем активным Лист "Sheet1"

        # вставляем столбец в позицию 1 (счет начинается с 1)
        sheet.insert_cols(1)

        # задаем высоту строки 1 (с названиями столбцов)
        sheet.row_dimensions[1].height = 30

        cols = "B", "C", "D"
        for col in cols:
            # задаем ширину столбцов B, C, D
            sheet.column_dimensions[col].width = 18
            # активируем перенос текста в ячейках B1, C1, D1 (с названиями столбцов) и выравниваем по центру
            sheet[f"{col + str(1)}"].alignment = Alignment(wrap_text=True, horizontal="center")

        # определяем количество строк в таблице (длина итогового датафрейма)
        len_table = len(df)

        # изменяем шрифт в ячейках с номерами актов с жирного на обычный
        # начинаем со 2 строки, т.к. строка 1 - это названия столбцов
        for i in range(2, len_table + 2):
            sheet[f"B{str(i)}"].font = Font(bold=False)

        # рисуем границы в ячейках столбцов C и D (по количеству строк в таблице)
        for i in ("C", "D"):
            # начинаем со 2 строки, т.к. строка 1 - это названия столбцов
            for j in range(2, len_table + 2):
                # задаем стиль границы - тонкая линия и цвет черный
                thins = Side(border_style="thin", color="000000")
                # применяем заданный стиль границы к верхней, нижней, левой и правой границе ячеек по циклу
                sheet[f"{i + str(j)}"].border = Border(top=thins, bottom=thins, left=thins, right=thins)
                # выравниваем текст в ячейках по центру
                sheet[f"{i+str(j)}"].alignment = Alignment(horizontal="center")

        # сохраняем изменения
        wb.save(file_out)


if __name__ == "__main__":

    client = "ЯМЗ - эксплуатация"  # потребитель
    product = "водяной насос"  # изделие по которому будет формироваться отчет

    # ---------------- если акты одного календарного года --------------------
    # список актов исследования из претензий одного года
    nums_act_1 = [768, 769]
    obj_1 = Date_to_act(2024, client, product, nums_act_1)

    # формируем итоговую таблицу (датафрейм)
    result = obj_1.get_frame()  # СТРОКУ ЗАКОМЕНТИРОВАТЬ, если акты разных годов !!!
    # или поиск по базам разных годов !!!

    # --------- если акты разных годов или поиск по базам разных годов -------
    # # список актов исследования из претензий другого года
    # nums_act_2 = [889, 896, 897, 898, 899, 900, 901, 902, 903, 909, 945, 948, 949, 950]
    # obj_2 = Date_to_act(2023, client, product, nums_act_2)

    # # формируем итоговую таблицу (датафрейм)
    # result = pd.concat([obj_1.get_frame(), obj_2.get_frame()])
    # ------------------------------------------------------------------------

    print(result)
    print("Количество актов в списке -", len(result))

    # записываем в файл Excel (файл закрывается перед записью, если открыт)
    obj_1.excel_close_write(result)
    # редактируем стили таблицы в записанном файле Excel
    obj_1.transform_excel(result)
