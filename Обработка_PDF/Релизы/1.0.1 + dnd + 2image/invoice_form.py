# импортируемый модуль invoice_form.py (импортируется в main.py)

import tkinter as tk
from tkinter import ttk, messagebox
from invoice_processor import InvoiceProcessor

class InvoiceForm:
    def __init__(self, parent, config):
        self.parent = parent
        self.config = config
        self.processor = None  # атрибут для хранения процессора
        self.create_form()

    def create_form(self):
        """Создание формы для ввода данных накладной"""
        # Создаем новое окно
        self.window = tk.Toplevel(self.parent)
        self.window.title("Ввод данных накладной")
        self.window.geometry("600x420")
        self.window.focus_set()

        # Создаем основной фрейм с отступами
        self.main_frame = ttk.Frame(self.window, padding="10")
        self.main_frame.pack(fill='both', expand=True)

        self.create_input_fields()
        self.create_hint_label()
        self.create_result_frame()
        self.create_buttons()
        self.center_window()


    def create_input_fields(self):
        """Создание полей ввода"""
        # Создаем стиль для меток и полей
        label_font = ('TkDefaultFont', 10)
        entry_font = ('TkDefaultFont', 11)
        entry_width = 35

        # Создаем и размещаем элементы управления
        self.entries = {}

        for field in self.config['invoice_fields']:
            frame = ttk.Frame(self.main_frame)
            frame.pack(fill='x', pady=5)

            # Метка с фиксированной шириной
            label = ttk.Label(frame, text=field, font=label_font, width=25)
            label.pack(side='left', padx=(0, 10))

            # Для номеров актов используем Text, для остальных полей Entry
            if field in ["Номер акта Приобретателя", "Номер акта Потребителя"]:
                self.create_text_field(frame, field, entry_font, entry_width)
            else:
                self.create_entry_field(frame, field, entry_font, entry_width)


    def create_text_field(self, parent, field, font, width):
        """Создание многострочного поля ввода"""
        text_frame = ttk.Frame(parent)
        text_frame.pack(side='left', fill='x', expand=True)

        text_widget = tk.Text(
            text_frame,
            font=font,
            width=width,
            height=3,
            wrap=tk.WORD
        )
        text_widget.pack(side='left', fill='both', expand=True)

        scrollbar = ttk.Scrollbar(text_frame, orient='vertical', command=text_widget.yview)
        scrollbar.pack(side='right', fill='y')
        text_widget.configure(yscrollcommand=scrollbar.set)

        self.entries[field] = text_widget


    def create_entry_field(self, parent, field, font, width):
        """Создание однострочного поля ввода"""
        entry = ttk.Entry(parent, font=font, width=width)
        entry.pack(side='left', fill='x', expand=True)
        self.entries[field] = entry


    def create_hint_label(self):
        """Создание подсказки"""
        hint_label = ttk.Label(
            self.main_frame,
            text="* Номера актов вводятся через запятую",
            font=('TkDefaultFont', 9, 'italic'),
            foreground='gray'
        )
        hint_label.pack(anchor='w', padx=10, pady=(0, 10))


    def create_result_frame(self):
        """Создание фрейма с результатами поиска"""
        result_frame = ttk.Frame(self.main_frame)
        result_frame.pack(fill='x', pady=20)

        result_label = ttk.Label(
            result_frame,
            text="Найдено строк:",
            font=('TkDefaultFont', 10, 'bold')
        )
        result_label.pack(side='left', padx=(0, 10))

        self.result_value = ttk.Label(
            result_frame,
            text="0",
            font=('TkDefaultFont', 11)
        )
        self.result_value.pack(side='left')


    def create_buttons(self):
        """Создание кнопок"""
        button_frame = ttk.Frame(self.main_frame)
        button_frame.pack(pady=20, fill='x')

        self.save_button = ttk.Button(
            button_frame,
            text="Сохранить в Excel",
            command=self.save_changes,
            style='Custom.TButton',
            state='disabled'
        )
        self.save_button.pack(side='right', padx=5)

        self.check_button = ttk.Button(
            button_frame,
            text="Проверить",
            command=self.check_data,
            style='Custom.TButton'
        )
        self.check_button.pack(side='right', padx=5)


    def center_window(self):
        """Центрирование окна"""
        self.window.transient(self.parent)
        self.window.grab_set()
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - (width // 2)
        y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - (height // 2)
        self.window.geometry(f'+{x}+{y}')


    def check_data(self):
        """Проверка данных и поиск строк"""
        try:
            # Показываем информационное окно
            indicator_window = tk.Toplevel(self.window)
            indicator_window.title("Поиск")

            # Размер и положение окна
            window_width = 300
            window_height = 100
            screen_width = indicator_window.winfo_screenwidth()
            screen_height = indicator_window.winfo_screenheight()
            x = (screen_width - window_width) // 2
            y = (screen_height - window_height) // 2
            indicator_window.geometry(f'{window_width}x{window_height}+{x}+{y}')

            # Настройка окна
            indicator_window.transient(self.window)
            indicator_window.grab_set()
            indicator_window.focus_set()
            indicator_window.resizable(False, False)

            # Добавляем текст
            label = ttk.Label(
                indicator_window,
                text="Подождите, производится поиск...",
                font=('TkDefaultFont', 10)
            )
            label.pack(pady=20)

            # Обновляем окно
            self.window.update()

            try:
                # Получаем данные из полей
                data = {}
                for field, entry in self.entries.items():
                    if isinstance(entry, tk.Text):
                        value = entry.get('1.0', 'end-1c').strip()
                        data[field] = value
                    else:
                        value = entry.get().strip()
                        data[field] = value

                # Объединяем номера актов (берем непустые)
                claim_numbers = set()
                if data["Номер акта Приобретателя"]:
                    nums = {num.strip() for num in data["Номер акта Приобретателя"].split(',')}
                    claim_numbers.update(nums)
                if data["Номер акта Потребителя"]:
                    nums = {num.strip() for num in data["Номер акта Потребителя"].split(',')}
                    claim_numbers.update(nums)

                claim_numbers.discard('')

                if not claim_numbers:
                    indicator_window.destroy()
                    raise ValueError("Необходимо указать номер акта приобретателя или потребителя")

                # Проверяем обязательные поля
                if not data["Номер накладной прихода"]:
                    indicator_window.destroy()
                    raise ValueError("Необходимо указать номер накладной")
                if not data["Дата накладной"]:
                    indicator_window.destroy()
                    raise ValueError("Необходимо указать дату накладной")

                # Создаем процессор и проверяем данные
                self.processor = InvoiceProcessor(self.config['excel_path'])
                found_rows = self.processor.find_rows(claim_numbers)

                # Закрываем окно индикации
                indicator_window.destroy()

                # Обновляем количество найденных строк
                self.result_value.config(text=str(found_rows))

                # Если найдены строки, сохраняем проверенные данные и активируем кнопку сохранения
                if found_rows > 0:
                    self.validated_data = data
                    self.save_button.config(state='normal')
                else:
                    self.save_button.config(state='disabled')

            except Exception as e:
                # В случае ошибки закрываем окно индикации
                indicator_window.destroy()
                raise e

        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
            self.result_value.config(text="0")
            self.save_button.config(state='disabled')


    def save_changes(self):
        """Сохранение данных в Excel"""
        try:
            # Показываем информационное окно
            indicator_window = tk.Toplevel(self.window)
            indicator_window.title("Сохранение")

            # Размер и положение окна
            window_width = 300
            window_height = 100
            screen_width = indicator_window.winfo_screenwidth()
            screen_height = indicator_window.winfo_screenheight()
            x = (screen_width - window_width) // 2
            y = (screen_height - window_height) // 2
            indicator_window.geometry(f'{window_width}x{window_height}+{x}+{y}')

            # Настройка окна
            indicator_window.transient(self.window)
            indicator_window.grab_set()
            indicator_window.focus_set()
            indicator_window.resizable(False, False)

            # Добавляем текст
            label = ttk.Label(
                indicator_window,
                text="Сохранение данных в ЖУРНАЛ УЧЕТА...",
                font=('TkDefaultFont', 10)
            )
            label.pack(pady=20)

            # Обновляем окно
            self.window.update()

            try:
                # Используем существующий процессор
                self.processor.save_data(
                    self.validated_data["Номер накладной прихода"],
                    self.validated_data["Дата накладной"]
                )

                # Закрываем окно индикации
                indicator_window.destroy()

                messagebox.showinfo("Сообщение", "Данные успешно сохранены в ЖУРНАЛ УЧЕТА")
                self.window.destroy()

            except Exception as e:
                # В случае ошибки закрываем окно индикации
                indicator_window.destroy()
                raise e

        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
