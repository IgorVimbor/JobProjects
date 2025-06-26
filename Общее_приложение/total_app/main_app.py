import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import openpyxl

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

        # Менеджер диалогов анализа данных
        self.analysis_dialogs = AnalysisDialogs(self, self.original_data, self.display_data, self.status_var, self.save_plot)

        # Создаем главное меню
        self.create_menu()

    def save_plot(self, *args, **kwargs):
        """Заглушка для метода save_plot, необходимого для AnalysisDialogs"""
        pass

    def create_context_menu(self):
        """Создает контекстное меню для таблицы"""
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Копировать", command=self.context_menu_manager.copy_selection)
        self.context_menu.add_command(label="Вставить", command=self.context_menu_manager.paste_selection)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Удалить", command=self.context_menu_manager.delete_selection)

        # Привязываем появление меню к правому клику мыши
        self.tree.bind("<Button-3>", self.show_context_menu)

    def show_context_menu(self, event):
        """Показывает контекстное меню по правому клику"""
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def create_column_menu(self):
        """Создает меню управления видимостью столбцов"""
        self.column_menu = tk.Menu(self, tearoff=0)
        self.visible_columns = {}  # Словарь для хранения состояния видимости столбцов

    def show_column_manager(self):
        """Показывает окно управления столбцами"""
        column_window = tk.Toplevel(self)
        column_window.title("Управление столбцами")
        column_window.geometry("300x400")

        for column in self.tree['columns']:
            var = tk.BooleanVar(value=self.visible_columns.get(column, True))
            self.visible_columns[column] = var
            ttk.Checkbutton(column_window, text=column, variable=var,
                            command=lambda c=column: self.toggle_column(c)).pack(anchor=tk.W)

    def toggle_column(self, column):
        """Переключает видимость столбца"""
        if self.visible_columns[column].get():
            self.tree.column(column, width=100)
        else:
            self.tree.column(column, width=0)

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
        edit_menu.add_command(label="Копировать", command=self.copy_selection, accelerator="Ctrl+C")
        edit_menu.add_command(label="Вставить", command=self.paste_selection, accelerator="Ctrl+V")

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

        # Дополнительные меню для агрегации и визуализации
        aggregation_menu = tk.Menu(analysis_menu, tearoff=0)
        analysis_menu.add_cascade(label="Агрегация", menu=aggregation_menu)
        aggregation_menu.add_command(label="Группировка данных", command=self.show_grouping_dialog)
        aggregation_menu.add_command(label="Сводная таблица", command=self.show_pivot_dialog)

        visualization_menu = tk.Menu(analysis_menu, tearoff=0)
        analysis_menu.add_cascade(label="Визуализация", menu=visualization_menu)
        visualization_menu.add_command(label="Гистограмма", command=lambda: self.show_plot_dialog('histogram'))
        visualization_menu.add_command(label="График рассеяния", command=lambda: self.show_plot_dialog('scatter'))
        visualization_menu.add_command(label="Линейный график", command=lambda: self.show_plot_dialog('line'))
        visualization_menu.add_command(label="Круговая диаграмма", command=lambda: self.show_plot_dialog('pie'))

    # Здесь необходимо реализовать остальные методы:
    # create_top_panel, create_filter_panel, create_table, create_context_menu, create_column_menu,
    # load_file, save_changes, undo, redo, display_data, сортировка, фильтрация, show_grouping_dialog,
    # show_pivot_dialog, show_plot_dialog, save_plot, on_closing, bind_shortcuts, update_undo_redo_buttons,
    # и другие необходимые методы.

    def show_grouping_dialog(self):
        """Показывает диалог группировки данных"""
        messagebox.showinfo("Группировка данных", "Функция группировки данных пока не реализована.")

    def show_pivot_dialog(self):
        """Показывает диалог создания сводной таблицы"""
        messagebox.showinfo("Сводная таблица", "Функция создания сводной таблицы пока не реализована.")

    def show_plot_dialog(self, plot_type):
        """Показывает диалог построения графика"""
        messagebox.showinfo("Визуализация", f"Функция построения графика типа '{plot_type}' пока не реализована.")

    def create_top_panel(self):
        """Создает верхнюю панель с кнопками и выбором листа"""
        top_panel = ttk.Frame(self.main_frame)
        top_panel.pack(fill=tk.X, pady=(0, 5))

        self.load_button = ttk.Button(top_panel, text='Открыть Excel файл', command=self.load_file)
        self.load_button.pack(side=tk.LEFT, padx=5)

        self.sheet_var = tk.StringVar()
        self.sheet_choice = ttk.Combobox(top_panel, textvariable=self.sheet_var, state='disabled')
        self.sheet_choice.pack(side=tk.LEFT, padx=5)
        self.sheet_choice.bind('<<ComboboxSelected>>', self.on_sheet_selected)

        self.save_button = ttk.Button(top_panel, text='Сохранить изменения', command=self.save_changes, state='disabled')
        self.save_button.pack(side=tk.LEFT, padx=5)

        self.undo_button = ttk.Button(top_panel, text='↶', command=self.undo, state='disabled')
        self.undo_button.pack(side=tk.LEFT, padx=2)
        self.redo_button = ttk.Button(top_panel, text='↷', command=self.redo, state='disabled')
        self.redo_button.pack(side=tk.LEFT, padx=2)

    def create_filter_panel(self):
        """Создает панель с фильтром"""
        filter_panel = ttk.Frame(self.main_frame)
        filter_panel.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(filter_panel, text="Фильтр:").pack(side=tk.LEFT, padx=5)

        self.filter_var = tk.StringVar()
        self.filter_var.trace('w', self.on_filter)
        self.filter_entry = ttk.Entry(filter_panel, textvariable=self.filter_var)
        self.filter_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        self.clear_filter_button = ttk.Button(filter_panel, text='Сбросить фильтр', command=self.clear_filter)
        self.clear_filter_button.pack(side=tk.LEFT, padx=5)

    def create_table(self):
        """Создает таблицу с прокруткой"""
        self.table_container = ttk.Frame(self.main_frame)
        self.table_container.pack(fill=tk.BOTH, expand=True)

        self.header_frame = ttk.Frame(self.table_container)
        self.header_frame.grid(row=0, column=0, sticky="ew")

        self.canvas = tk.Canvas(self.table_container)

        self.vsb = ttk.Scrollbar(self.table_container, orient="vertical", command=self.canvas.yview)
        self.hsb = ttk.Scrollbar(self.table_container, orient="horizontal", command=self.canvas.xview)

        self.table_frame = ttk.Frame(self.canvas)

        self.tree = EditableTreeview(self.table_frame, selectmode='extended')
        self.tree.pack(fill=tk.BOTH, expand=True)

        self.header_tree = ttk.Treeview(self.header_frame, show="headings", height=1)
        self.header_tree.pack(fill=tk.X, expand=True)

        self.canvas.configure(
            xscrollcommand=self.sync_scroll,
            yscrollcommand=self.vsb.set,
            scrollregion=self.canvas.bbox("all")
        )

        self.canvas_frame = self.canvas.create_window((0, 0), window=self.table_frame, anchor="nw")

        self.canvas.grid(row=1, column=0, sticky="nsew")
        self.vsb.grid(row=1, column=1, sticky="ns")
        self.hsb.grid(row=2, column=0, sticky="ew")

        self.table_container.grid_rowconfigure(1, weight=1)
        self.table_container.grid_columnconfigure(0, weight=1)

        self.canvas.bind('<Configure>', self.on_canvas_configure)
        self.table_frame.bind('<Configure>', self.on_frame_configure)

        self.tree.bind('<MouseWheel>', self.on_mousewheel_y)
        self.tree.bind('<Shift-MouseWheel>', self.on_mousewheel_x)
        self.tree.bind('<Button-4>', self.on_mousewheel_y)
        self.tree.bind('<Button-5>', self.on_mousewheel_y)
        self.tree.bind('<Shift-Button-4>', self.on_mousewheel_x)
        self.tree.bind('<Shift-Button-5>', self.on_mousewheel_x)

    def sync_scroll(self, *args):
        """Синхронизирует прокрутку заголовков и основной таблицы"""
        self.header_tree.xview_moveto(args[0])
        self.hsb.set(*args)

    def on_canvas_configure(self, event):
        """Обработчик изменения размера холста"""
        total_width = 0
        for col in self.tree['columns']:
            total_width += self.tree.column(col, option='width')
        new_width = max(event.width, total_width)
        self.canvas.itemconfig(self.canvas_frame, width=new_width)

    def on_frame_configure(self, event):
        """Обработчик изменения размера фрейма"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_mousewheel_y(self, event):
        """Обработчик вертикальной прокрутки колесиком мыши"""
        if event.num == 4 or event.delta > 0:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5 or event.delta < 0:
            self.canvas.yview_scroll(1, "units")

    def on_mousewheel_x(self, event):
        """Обработчик горизонтальной прокрутки колесиком мыши"""
        if event.num == 4 or event.delta > 0:
            self.canvas.xview_scroll(-1, "units")
        elif event.num == 5 or event.delta < 0:
            self.canvas.xview_scroll(1, "units")

    def display_data(self, df):
        """Отображает DataFrame в таблице с буферизацией"""
        BATCH_SIZE = 1000

        progress = ttk.Progressbar(self.main_frame, mode='determinate')
        progress.pack(fill=tk.X, padx=5, pady=5)

        try:
            for item in self.tree.get_children():
                self.tree.delete(item)
            for item in self.header_tree.get_children():
                self.header_tree.delete(item)

            columns = list(df.columns)
            self.tree['columns'] = columns
            self.tree['show'] = 'headings'
            self.header_tree['columns'] = columns
            self.header_tree['show'] = 'headings'

            for column in columns:
                header_width = len(str(column)) * 10
                max_content_width = df[column].astype(str).str.len().max() * 7
                column_width = max(header_width, max_content_width, 50)

                self.tree.heading(column, text=column, command=lambda c=column: self.sort_column(c))
                self.tree.column(column, width=column_width, minwidth=50)

                self.header_tree.heading(column, text=column)
                self.header_tree.column(column, width=column_width, minwidth=50)

            total_rows = len(df)
            max_height = 40
            self.tree.config(height=min(total_rows, max_height))

            for i in range(0, total_rows, BATCH_SIZE):
                batch = df.iloc[i:i+BATCH_SIZE]
                for index, row in batch.iterrows():
                    values = ['' if pd.isna(value) else str(value) for value in row]
                    self.tree.insert('', tk.END, values=values)

                progress['value'] = (i + len(batch)) / total_rows * 100
                self.update_idletasks()

            self.visible_columns = {column: tk.BooleanVar(value=True) for column in columns}

        finally:
            progress.destroy()
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def bind_shortcuts(self):
        """Привязывает горячие клавиши"""
        self.bind('<Control-o>', lambda e: self.load_file())
        self.bind('<Control-s>', lambda e: self.save_changes())
        self.bind('<Control-z>', lambda e: self.undo())
        self.bind('<Control-y>', lambda e: self.redo())
        self.bind('<Control-c>', lambda e: self.context_menu_manager.copy_selection())
        self.bind('<Control-v>', lambda e: self.context_menu_manager.paste_selection())
        self.bind('<Delete>', lambda e: self.delete_selection())

    def undo(self):
        """Отменяет последнее действие"""
        if not self.undo_redo_manager.can_undo():
            return

        self.undo_redo_manager.undo(self.tree)
        self.update_undo_redo_buttons()
        self.changes_made = True

    def redo(self):
        """Повторяет отмененное действие"""
        if not self.undo_redo_manager.can_redo():
            return

        self.undo_redo_manager.redo(self.tree)
        self.update_undo_redo_buttons()
        self.changes_made = True

    def update_undo_redo_buttons(self):
        """Обновляет состояние кнопок Undo/Redo"""
        self.undo_button['state'] = 'normal' if self.undo_redo_manager.can_undo() else 'disabled'
        self.redo_button['state'] = 'normal' if self.undo_redo_manager.can_redo() else 'disabled'

    def copy_selection(self):
        """Копирует выделенные ячейки в буфер обмена"""
        self.context_menu_manager.copy_selection()

    def paste_selection(self):
        """Вставляет данные из буфера обмена"""
        self.context_menu_manager.paste_selection()
        self.changes_made = True
        self.update_undo_redo_buttons()

    def delete_selection(self):
        """Удаляет выделенные строки"""
        self.context_menu_manager.delete_selection()
        self.changes_made = True
        self.update_undo_redo_buttons()

    def sort_column(self, column):
        """Сортирует данные по столбцу"""
        if not self.tree.get_children():
            return

        if not hasattr(self, 'last_sort_column') or self.last_sort_column != column:
            self.last_sort_ascending = True
        else:
            self.last_sort_ascending = not self.last_sort_ascending
        self.last_sort_column = column

        column_idx = self.tree['columns'].index(column)

        data = []
        for item in self.tree.get_children():
            values = self.tree.item(item)['values']
            try:
                sort_value = float(values[column_idx])
            except (ValueError, TypeError):
                sort_value = str(values[column_idx]).lower()
            data.append((sort_value, values, item))

        data.sort(key=lambda x: x[0], reverse=not self.last_sort_ascending)

        for idx, (_, values, item) in enumerate(data):
            self.tree.move(item, '', idx)

        sort_direction = "по возрастанию" if self.last_sort_ascending else "по убыванию"
        self.status_var.set(f'Отсортировано по {column} {sort_direction}')

    def on_filter(self, *args):
        """Обработчик фильтрации данных"""
        if self.original_data is None:
            return

        filter_text = self.filter_var.get().lower()

        if not filter_text:
            self.display_data(self.original_data)
            self.status_var.set(f'Найдено записей: {len(self.original_data)}')
            return

        mask = self.original_data.astype(str).apply(lambda x: x.str.lower()).apply(
            lambda x: x.str.contains(filter_text, na=False)).any(axis=1)
        filtered_data = self.original_data[mask]

        self.display_data(filtered_data)

        self.status_var.set(f'Найдено записей: {len(filtered_data)}')

    def clear_filter(self, event=None):
        """Обработчик сброса фильтра"""
        self.filter_var.set('')
        if self.original_data is not None:
            self.display_data(self.original_data)
            self.status_var.set('Фильтр сброшен')

    def load_file(self, event=None):
        """Открывает диалог выбора файла и загружает данные"""
        if self.changes_made:
            if not messagebox.askyesno("Подтверждение",
                                    "Есть несохраненные изменения. Продолжить?"):
                return

        file_path = filedialog.askopenfilename(
            filetypes=[('Excel files', '*.xlsx *.xlsm')],
            title='Выберите Excel файл'
        )

        if file_path:
            try:
                progress_window = tk.Toplevel(self)
                progress_window.title("Загрузка файла")
                progress_window.geometry("300x100")
                progress_window.transient(self)
                progress_window.grab_set()

                ttk.Label(progress_window, text="Загрузка файла...").pack(pady=10)
                progress = ttk.Progressbar(progress_window, mode='indeterminate')
                progress.pack(fill=tk.X, padx=20, pady=10)
                progress.start()

                self.update()

                workbook = openpyxl.load_workbook(file_path, read_only=True, keep_vba=True)
                self.sheets = workbook.sheetnames
                workbook.close()

                self.current_file = file_path
                self.sheet_choice['values'] = self.sheets
                self.sheet_choice.current(0)
                self.sheet_choice['state'] = 'readonly'
                self.save_button['state'] = 'normal'

                self.current_sheet = self.sheets[0]
                self.on_sheet_selected()

                self.undo_redo_manager.clear()
                self.update_undo_redo_buttons()

                self.title(f'Просмотр Excel - {Path(file_path).name}')

                progress_window.destroy()

            except Exception as e:
                messagebox.showerror('Ошибка', f'Ошибка при загрузке файла: {str(e)}')
                if 'progress_window' in locals():
                    progress_window.destroy()

    def on_sheet_selected(self, event=None):
        """Загружает данные из конкретного листа Excel файла"""
        sheet_name = self.sheet_var.get()
        if not sheet_name:
            return
        try:
            progress_window = tk.Toplevel(self)
            progress_window.title("Загрузка листа")
            progress_window.geometry("300x100")
            progress_window.transient(self)
            progress_window.grab_set()

            ttk.Label(progress_window, text=f"Загрузка листа {sheet_name}...").pack(pady=10)
            progress = ttk.Progressbar(progress_window, mode='determinate')
            progress.pack(fill=tk.X, padx=20, pady=10)

            self.update()

            self.original_data = pd.read_excel(self.current_file, sheet_name=sheet_name)

            self.display_data(self.original_data)

            filename = Path(self.current_file).name
            self.status_var.set(f'Загружен файл: {filename}, лист: {sheet_name}')

            self.filter_var.set('')

            self.changes_made = False
            self.undo_redo_manager.clear()
            self.update_undo_redo_buttons()

            progress_window.destroy()

        except Exception as e:
            messagebox.showerror('Ошибка', f'Ошибка при загрузке листа: {str(e)}')
            if 'progress_window' in locals():
                progress_window.destroy()

    def save_changes(self, event=None):
        """Сохраняет изменения в файл"""
        if not self.changes_made:
            messagebox.showinfo("Информация", "Нет изменений для сохранения")
            return

        if not messagebox.askyesno("Подтверждение", "Вы уверены, что хотите сохранить изменения?"):
            return

        try:
            progress_window = tk.Toplevel(self)
            progress_window.title("Сохранение")
            progress_window.geometry("300x100")
            progress_window.transient(self)
            progress_window.grab_set()

            ttk.Label(progress_window, text="Сохранение изменений...").pack(pady=10)
            progress = ttk.Progressbar(progress_window, mode='indeterminate')
            progress.pack(fill=tk.X, padx=20, pady=10)
            progress.start()
            self.update()

            data = []
            for item in self.tree.get_children():
                values = self.tree.item(item)['values']
                data.append(values)

            df = pd.DataFrame(data, columns=self.tree['columns'])

            self.file_handler.save_changes(self.current_file, self.current_sheet, df)

            self.changes_made = False
            self.save_button['state'] = 'disabled'
            self.status_var.set(f'Изменения сохранены в лист: {self.current_sheet}')

            progress_window.destroy()

            messagebox.showinfo('Информация', 'Файл успешно сохранен!')

        except Exception as e:
            messagebox.showerror('Ошибка', f'Ошибка при сохранении: {str(e)}')
            if 'progress_window' in locals():
                progress_window.destroy()

    def on_closing(self):
        """Обработчик закрытия окна"""
        if self.changes_made:
            answer = messagebox.askyesnocancel(
                "Подтверждение",
                "Есть несохраненные изменения. Сохранить перед выходом?"
            )
            if answer is None:
                return
            if answer:
                self.save_changes()
        self.destroy()


def main():
    app = ExcelViewer()
    app.mainloop()

if __name__ == '__main__':
    main()
