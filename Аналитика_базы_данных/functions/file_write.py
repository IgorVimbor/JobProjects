import pandas as pd
import win32com.client
import os


def excel_close_write():
    """функция для записи итогового датафрейма в файл Excel переменной file_out.
    Если file_out (файл Excel) открыт, то перед записью файл закрывается."""
    try:  # попытка обратится к файлу
        # переименовываем файл по существующему имени (оставляем старое имя)
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


if __name__ == "__main__":

    file_out = "D:\РАБОТА\Лист Microsoft Excel.xlsx"

    data = {
        "Name": ["John", "Mary", "David"],
        "Age": [25, 31, 42],
        "City": ["New York", "London", "Paris22"],
    }
    df = pd.DataFrame(data).set_index("Name")

    excel_close_write()
