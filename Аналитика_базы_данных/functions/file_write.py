import pandas as pd
import win32com.client
import os
from openpyxl import load_workbook
from openpyxl.styles import Alignment, Font, Border, Side


def excel_close_write(df: pd.DataFrame):
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


def transform_excel(df: pd.DataFrame):
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
        sheet[f"{col + str(1)}"].alignment = Alignment(
            wrap_text=True, horizontal="center"
        )

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
            sheet[f"{i + str(j)}"].border = Border(
                top=thins, bottom=thins, left=thins, right=thins
            )
            # выравниваем текст в ячейках по центру
            sheet[f"{i+str(j)}"].alignment = Alignment(horizontal="center")

    # сохраняем изменения
    wb.save(file_out)


if __name__ == "__main__":

    file_out = "D:\РАБОТА\Лист Microsoft Excel.xlsx"

    dict_data = {
        "Номер акта исследования": [123, 256, 378, 412, 589, 632],
        "Дата акта исследования": [
            "12.02.23",
            "20.02.23",
            "15.04.23",
            "20.05.23",
            "25.06.23",
            "05.01.24",
        ],
        "Дата поступления сообщения в ОТК": [
            "10.01.23",
            "20.01.23",
            "15.03.23",
            "15.04.23",
            "20.05.23",
            "14.11.23",
        ],
    }
    df_data = pd.DataFrame(dict_data).set_index("Номер акта исследования")

    excel_close_write(df_data)
    transform_excel(df_data)
