# python -m unittest test_excel_viewer.py

import unittest
import os
import tempfile
import pandas as pd
from main_app import ExcelViewer
from file_handler import ExcelFileHandler

class TestExcelViewer(unittest.TestCase):
    def setUp(self):
        # Создание временного Excel файла для тестирования
        self.test_file = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
        df = pd.DataFrame({
            'A': [1, 2, 3],
            'B': ['x', 'y', 'z']
        })
        df.to_excel(self.test_file.name, index=False)
        self.test_file.close()

        # Инициализация экземпляра приложения ExcelViewer
        self.app = ExcelViewer()
        self.app.update()

    def tearDown(self):
        # Закрытие приложения и удаление временного файла
        self.app.destroy()
        os.unlink(self.test_file.name)

    def test_load_file(self):
        # Тестирование загрузки Excel файла
        self.app.current_file = self.test_file.name
        self.app.sheets = ['Sheet1']
        self.app.sheet_choice['values'] = self.app.sheets
        self.app.sheet_choice.current(0)
        self.app.sheet_choice['state'] = 'readonly'
        self.app.current_sheet = 'Sheet1'
        self.app.on_sheet_selected()

        # Проверка, что данные успешно загружены
        self.assertIsNotNone(self.app.original_data)
        self.assertEqual(list(self.app.original_data.columns), ['A', 'B'])
        self.assertEqual(len(self.app.original_data), 3)

    def test_display_data(self):
        # Тестирование отображения данных в таблице
        df = pd.DataFrame({
            'Col1': [10, 20],
            'Col2': ['a', 'b']
        })
        self.app.display_data(df)
        self.assertEqual(len(self.app.tree.get_children()), 2)

    def test_undo_redo(self):
        # Тестирование функций отмены и повтора изменений
        df = pd.DataFrame({
            'Col1': [10, 20],
            'Col2': ['a', 'b']
        })
        self.app.display_data(df)
        # Симуляция редактирования данных
        first_item = self.app.tree.get_children()[0]
        self.app.undo_redo_manager.add_undo_action({
            'item': first_item,
            'column': 'Col1',
            'old_value': '10',
            'new_value': '15'
        })
        self.app.tree.set(first_item, 'Col1', '15')
        self.app.undo()
        self.assertEqual(self.app.tree.set(first_item, 'Col1'), '10')
        self.app.redo()
        self.assertEqual(self.app.tree.set(first_item, 'Col1'), '15')

    def test_copy_paste_delete(self):
        # Тестирование функций копирования, вставки и удаления строк
        df = pd.DataFrame({
            'Col1': [10, 20],
            'Col2': ['a', 'b']
        })
        self.app.display_data(df)
        # Выбор первой строки
        first_item = self.app.tree.get_children()[0]
        self.app.tree.selection_set(first_item)
        # Копирование выделенной строки
        self.app.context_menu_manager.copy_selection()
        # Вставка (симуляция вставки в новую строку)
        self.app.context_menu_manager.paste_selection()
        self.assertEqual(len(self.app.tree.get_children()), 3)
        # Удаление выделенной строки
        self.app.tree.selection_set(first_item)
        self.app.context_menu_manager.delete_selection()
        self.assertEqual(len(self.app.tree.get_children()), 2)

if __name__ == '__main__':
    unittest.main()
