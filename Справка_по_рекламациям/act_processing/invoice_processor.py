# импортируемый модуль invoice_processor.py (импортируется в invoice_form.py)

import xlwings as xw
from datetime import datetime


class InvoiceProcessor:
    def __init__(self, excel_path):
        self.excel_path = excel_path
        self.found_rows = []  # Список для хранения найденных строк
        self.wb = None
        self.sheet = None
        self.initialize_workbook()


    def initialize_workbook(self):
        """Инициализация рабочей книги"""
        try:
            self.wb = xw.books.active
            self.sheet = self.wb.sheets.active
        except Exception as e:
            raise Exception(f"Ошибка при инициализации Excel: {str(e)}")


    def find_rows(self, claim_numbers):
        """
        Поиск строк по номерам актов рекламации
        claim_numbers (set): Множество номеров актов рекламации
        Returns (int): Количество найденных строк
        """
        try:
            self.found_rows = []

            # Ищем последнюю заполненную строку
            last_row = 1
            for row in range(1, self.sheet.used_range.last_cell.row + 1):
                if all(self.sheet.cells(row, col).value for col in [7, 8, 9]):
                    last_row = row

            # Преобразуем номера актов в строки без десятичной части
            claim_numbers = {str(num).split('.')[0] for num in claim_numbers}

            # Ищем строки в столбцах 13 и 17 по номерам актов
            for row in range(1, last_row + 1):
                # Получаем значения и преобразуем их в строки без десятичной части
                cell_value_13 = str(self.sheet.cells(row, 13).value or '').split('.')[0].strip()
                cell_value_14 = str(self.sheet.cells(row, 17).value or '').split('.')[0].strip()

                if cell_value_13 in claim_numbers or cell_value_14 in claim_numbers:
                    self.found_rows.append(row)

            return len(self.found_rows)

        except Exception as e:
            raise Exception(f"Ошибка при поиске строк: {str(e)}")


    def save_data(self, invoice_number, invoice_date):
        """
        Сохранение данных - номера и даты накладной
        invoice_number (str): Номер накладной
        invoice_date (str): Дата накладной
        """
        try:
            if not self.validate_date(invoice_date):
                raise ValueError("Неверный формат даты накладной (требуется дд.мм.гггг)")

            if not self.found_rows:
                raise ValueError("Нет найденных строк для сохранения")

            # Обновляем данные в найденных строках
            for row in self.found_rows:
                # Записываем номер накладной в столбец 36
                self.sheet.cells(row, 36).value = invoice_number
                # Записываем дату накладной в столбец 37
                self.sheet.cells(row, 37).value = invoice_date

            # Сохраняем изменения
            self.wb.save()

        except Exception as e:
            raise Exception(f"Ошибка при сохранении данных: {str(e)}")


    @staticmethod
    def validate_date(date_str):
        """Проверка корректности даты"""
        try:
            datetime.strptime(date_str, '%d.%m.%Y')
            return True
        except ValueError:
            return False
