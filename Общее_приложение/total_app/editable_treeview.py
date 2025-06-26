import tkinter as tk
from tkinter import ttk

class EditableTreeview(ttk.Treeview):
    """
    Класс EditableTreeview расширяет стандартный ttk.Treeview,
    добавляя возможность редактирования ячеек по двойному клику.
    """
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        # Создаем виджет Entry для редактирования ячеек
        self.editor = ttk.Entry(master)
        self.editor.place(x=0, y=0, width=0, height=0)

        # Привязываем события для открытия и закрытия редактора
        self.bind('<Double-1>', self.on_double_click)
        self.editor.bind('<Return>', self.on_editor_return)
        self.editor.bind('<Escape>', self.on_editor_escape)
        self.editor.bind('<FocusOut>', self.on_editor_escape)

        self.editing_cell = None  # Текущая редактируемая ячейка (item, column, column_num)
        self.original_value = None  # Исходное значение ячейки перед редактированием

    def on_double_click(self, event):
        """
        Обработчик двойного клика мыши.
        Определяет ячейку, открывает редактор для ввода нового значения.
        """
        region = self.identify('region', event.x, event.y)
        if region != 'cell':
            return

        column = self.identify_column(event.x)
        item = self.identify_row(event.y)

        if not item or not column:
            return

        # Получаем координаты и размеры ячейки для позиционирования редактора
        x, y, w, h = self.bbox(item, column)

        # Определяем индекс колонки и текущее значение ячейки
        column_num = int(column[1]) - 1
        values = self.item(item)['values']
        if not values or column_num >= len(values):
            value = ''
        else:
            value = values[column_num]

        # Сохраняем информацию о редактируемой ячейке
        self.editing_cell = (item, column, column_num)
        self.original_value = value

        # Настраиваем и отображаем виджет редактора
        self.editor.delete(0, tk.END)
        self.editor.insert(0, value)
        self.editor.selection_range(0, tk.END)
        self.editor.place(x=x, y=y, width=w, height=h)
        self.editor.focus_set()

    def on_editor_return(self, event):
        """
        Обработчик нажатия Enter в редакторе.
        Сохраняет новое значение в ячейку и скрывает редактор.
        """
        if not self.editing_cell:
            return

        item, column, column_num = self.editing_cell
        new_value = self.editor.get()

        # Обновляем значение в таблице
        values = list(self.item(item)['values'])
        values[column_num] = new_value
        self.item(item, values=values)

        # Скрываем редактор
        self.editor.place_forget()
        self.editing_cell = None

        # Генерируем событие изменения ячейки
        self.event_generate('<<TreeviewCellEdited>>')

    def on_editor_escape(self, event):
        """
        Обработчик нажатия Escape или потери фокуса редактором.
        Отменяет редактирование и скрывает редактор.
        """
        self.editor.place_forget()
        self.editing_cell = None
