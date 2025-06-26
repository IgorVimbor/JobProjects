import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from editable_treeview import EditableTreeview
from file_handler import ExcelFileHandler
from undo_redo_manager import UndoRedoManager
from context_menu import ContextMenuManager
from analysis_dialogs import AnalysisDialogs

"""
Модули включают:
    editable_treeview.py — класс для редактируемой таблицы
    file_handler.py — загрузка и сохранение Excel файлов с сохранением форматирования
    undo_redo_manager.py — управление undo/redo операциями
    context_menu.py — контекстное меню с копированием, вставкой и удалением
    analysis_dialogs.py — диалоги для статистического и корреляционного анализа
    main_app.py — основной класс приложения, связывающий все модули и реализующий GUI
"""

class ExcelViewer(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title('Просмотр Excel')  # Устанавливаем заголовок окна
        self.geometry('1024x768')  # Устанавливаем размер окна

        # Инициализация менеджеров для работы с файлами и отменой/повтором действий
        self.file_handler = ExcelFileHandler()
        self.undo_redo_manager = UndoRedoManager()

        # Инициализация переменных состояния
        self.current_file = None  # Текущий открытый файл
        self.current_sheet = None  # Текущий выбранный лист
        self.sheets = []  # Список листов в файле
        self.original_data = None  # Исходные данные из Excel
        self.changes_made = False  # Флаг наличия изменений

        # Создаем главное меню
        self.create_menu()

        # Основной фрейм для размещения виджетов
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Создаем верхнюю панель с кнопками и выбором листа
        self.create_top_panel()

        # Создаем панель фильтрации данных
        self.create_filter_panel()

        # Создаем таблицу для отображения данных
        self.create_table()

        # Строка состояния для отображения сообщений пользователю
        self.status_var = tk.StringVar(value='Готов к работе')
        self.status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # Менеджер контекстного меню для операций копирования, вставки и удаления
        self.context_menu_manager = ContextMenuManager(self.tree, self, self.status_var, self.undo_redo_manager)

        # Создаем контекстное меню и меню управления столбцами
        self.create_context_menu()
        self.create_column_menu()

        # Обработчик закрытия окна
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Привязываем горячие клавиши
        self.bind_shortcuts()

        # Менеджер диалогов анализа данных
        self.analysis_dialogs = AnalysisDialogs(self, self.original_data, self.display_data, self.status_var, self.save_plot)

    def create_menu(self):
        """Создает главное меню программы"""
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        # Меню Файл
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Файл", menu=file_menu)
        file_menu.add_command(label="Открыть", command=self.load_file, accelerator="Ctrl+O")
        file_menu.add_command(label="Сохранить", command=self.save_changes, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.on_closing, accelerator="Alt+F4")

        # Меню Правка
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Правка", menu=edit_menu)
        edit_menu.add_command(label="Отменить", command=self.undo, accelerator="Ctrl+Z")
        edit_menu.add_command(label="Повторить", command=self.redo, accelerator="Ctrl+Y")
        edit_menu.add_separator()
        edit_menu.add_command(label="Копировать", command=self.context_menu_manager.copy_selection, accelerator="Ctrl+C")
        edit_menu.add_command(label="Вставить", command=self.context_menu_manager.paste_selection, accelerator="Ctrl+V")

        # Меню Вид
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Вид", menu=view_menu)
        view_menu.add_command(label="Управление столбцами", command=self.show_column_manager)
        view_menu.add_command(label="Сбросить фильтр", command=self.clear_filter)

        # Меню Анализ
        analysis_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Анализ", menu=analysis_menu)

        # Подменю Статистика
        statistics_menu = tk.Menu(analysis_menu, tearoff=0)
        analysis_menu.add_cascade(label="Статистика", menu=statistics_menu)
        statistics_menu.add_command(label="Описательная статистика", command=self.analysis_dialogs.show_descriptive_statistics)
        statistics_menu.add_command(label="Корреляционный анализ", command=self.analysis_dialogs.show_correlation_analysis)

        # Здесь можно добавить дополнительные меню для агрегации и визуализации

    # Другие методы, такие как create_top_panel, create_filter_panel, create_table, create_context_menu, create_column_menu,
    # load_file, save_changes, undo, redo, display_data, сортировка, фильтрация и т.д. будут реализованы здесь,
    # используя импортированные модули и классы.

def main():
    app = ExcelViewer()
    app.mainloop()

if __name__ == '__main__':
    main()
