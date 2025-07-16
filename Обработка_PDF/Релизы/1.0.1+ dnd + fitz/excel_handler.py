# импортируемый модуль excel_handler.py

import xlwings as xw
import json


class ExcelHandler:
    def __init__(self, excel_path):
        self.excel_path = excel_path

        # Загружаем конфиг для получения ключей полей
        with open('config.json', 'r', encoding='utf-8') as file:
            config = json.load(file)
            self.fields = list(config['default_data'].keys())

        # Номера столбцов в базе ОТК для соответствующих полей
        self.columns = [5, 13, 14, 15, 16, 19, 20, 21, 24, 25, 26]

        # Создаем словарь соответствия динамически
        self.column_mapping = dict(zip(self.fields, self.columns))

    def write_data(self, data):
        """Запись данных в Excel"""
        try:
            # Получаем активную книгу
            wb = xw.books.active
            sheet = wb.sheets.active

            # Ищем последнюю заполненную строку
            last_row = 1
            for row in range(1, sheet.used_range.last_cell.row + 1):
                if all(sheet.cells(row, col).value for col in [7, 8, 9]):
                    last_row = row

            # Записываем данные в нужные ячейки
            for field, column in self.column_mapping.items():
                sheet.cells(last_row, column).value = data[field]

            # Заливаем строку желтым цветом
            range_to_fill = sheet.range(f"B{last_row}:BP{last_row}")
            range_to_fill.color = (255, 255, 0)  # RGB для желтого

            # Сохраняем изменения
            wb.save()

        except Exception as e:
            raise Exception(f"Ошибка при сохранении в ЖУРНАЛ УЧЕТА: {str(e)}")
