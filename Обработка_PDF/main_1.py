import tkinter as tk
from tkinter import filedialog, ttk, scrolledtext, messagebox
from temp_1 import (
    ExcelError, PDFProcessorYMZ, PDFProcessorRSM,
    PDFProcessorMAZ, PDFProcessorMAZ_2, PDFProcessorAnother
    )
from excel_handler import ExcelHandler


class MainApplication:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF to Excel Converter")
        self.root.geometry("800x600")

        # Создаем верхний фрейм для кнопок и чек-боксов
        self.top_frame = ttk.Frame(root)
        self.top_frame.pack(pady=10, padx=10, fill='x')

        # Создаем фрейм для кнопок (левая часть)
        self.button_frame = ttk.Frame(self.top_frame)
        self.button_frame.pack(side='left', padx=(0, 20))

        # Настраиваем стили
        style = ttk.Style()

        # Стиль для кнопок
        style.configure(
            'Custom.TButton',
            background='#4a90e2',
            foreground='black',
            padding=(5, 5),  # горизонтальный и вертикальный отступы
            font=('Arial', 9, 'bold'),
            relief='solid',  # 'raised', 'sunken', 'flat', 'ridge', 'solid', or 'groove'
            borderwidth=2
        )

        # Кнопки
        self.select_button = ttk.Button(
            self.button_frame,
            text="Выбрать PDF файл",
            command=self.select_pdf,
            style='Custom.TButton'
        )
        self.select_button.pack(side='left', padx=5)

        self.process_button = ttk.Button(
            self.button_frame,
            text="Распознать текст",
            command=self.process_file,
            style='Custom.TButton',
            state='disabled'
        )
        self.process_button.pack(side='left', padx=5)

        # Создаем фрейм для чек-боксов (правая часть)
        self.checkbox_frame = ttk.LabelFrame(
            self.top_frame,
            text="Выберите стандартную форму акта рекламации:",
            padding=(5, 5)
        )
        self.checkbox_frame.pack(side='left', fill='x', expand=True)

        # Стиль для радиокнопок
        style.configure(
            'Custom.TRadiobutton',
            font=('Arial', 9),
            padding=5
        )

        # Переменная для чек-боксов
        self.selected_form = tk.StringVar()

        # Создаем радиокнопки
        forms = ["Группа ГАЗ", "Ростсельмаш", "СЦ МАЗ", "СЦ МАЗ ///", "Другая"]
        for form in forms:
            rb = ttk.Radiobutton(
                self.checkbox_frame,
                text=form,
                value=form,
                variable=self.selected_form
            )
            rb.pack(side='left', padx=7)

        # По умолчанию выбираем первую форму
        self.selected_form.set("Группа ГАЗ")

        # Остальные фреймы для организации элементов
        self.preview_frame = ttk.Frame(root)
        self.preview_frame.pack(pady=10, padx=10, fill='both', expand=True)

        # Создаем Notebook (вкладки) для предпросмотра
        self.notebook = ttk.Notebook(self.preview_frame)
        self.notebook.pack(fill='both', expand=True)

        # Вкладка с данными таблицы
        self.table_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.table_frame, text='Данные таблицы')

        # Вкладка с распознанным текстом
        self.text_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.text_frame, text='Распознанный текст')

        # Текстовое поле для просмотра распознанного текста
        self.text_preview = scrolledtext.ScrolledText(
            self.text_frame,
            wrap=tk.WORD,
            width=70,
            height=20
        )
        self.text_preview.pack(padx=10, pady=10, fill='both', expand=True)

        # Таблица для просмотра данных
        self.create_table_preview()

        # Фрейм для кнопок управления данными
        self.control_frame = ttk.Frame(self.preview_frame)
        self.control_frame.pack(pady=10, fill='x')

        self.save_button = ttk.Button(
            self.control_frame,
            text="Сохранить в Excel",
            command=self.save_to_excel,
            style='Custom.TButton',
            state='disabled'
        )
        self.save_button.pack(side='right', padx=5)

        self.edit_button = ttk.Button(
            self.control_frame,
            text="Редактировать",
            command=self.enable_editing,
            style='Custom.TButton',
            state='disabled'
        )
        self.edit_button.pack(side='right', padx=5)

        # Добавляем отслеживание нажатия кнопок чек-боксов
        # Метод trace_add должен вызываться после создания всех кнопок
        self.selected_form.trace_add('write', self.on_form_select)

        # Создаем строку внизу основного окна с текстом "Development by IGOR VASILENOK"
        self.footer_label = ttk.Label(root, text=f"   Development by IGOR VASILENOK", anchor='w')
        self.footer_label.pack(side='bottom', fill='x', pady=5)

        # Инициализация переменных
        self.pdf_path = None
        self.extracted_data = None


    def on_form_select(self, *args):
        """Обработчик выбора формы"""
        selected = self.selected_form.get()
        if selected in ["СЦ МАЗ", "СЦ МАЗ ///", "Другая"]:
            # Для форм МАЗ, МАЗ/// и Другая активируем кнопку редактирования
            self.edit_button.config(state='normal')
            # Деактивируем кнопку распознавания
            self.process_button.config(state='disabled')

            # Очищаем предыдущие данные
            self.text_preview.delete('1.0', tk.END)
            self.tree.delete(*self.tree.get_children())
            self.save_button.config(state='disabled')

            # Инициализируем пустые данные для форм МАЗ, МАЗ/// и Другая
            processors = {
                "СЦ МАЗ": PDFProcessorMAZ,
                "СЦ МАЗ ///": PDFProcessorMAZ_2,
                "Другая": PDFProcessorAnother
            }
            processor = processors[selected]("")  # Пустой путь к файлу, так как он не нужен
            self.extracted_data = processor.data
        else:
            # Для других форм возвращаем стандартное поведение
            self.edit_button.config(state='disabled')
            self.process_button.config(state='normal' if self.pdf_path else 'disabled')
            self.extracted_data = None  # Сбрасываем данные


    def create_table_preview(self):
        """Создание таблицы для предпросмотра данных"""
        # Создаем фрейм для таблицы с прокруткой
        self.table_container = ttk.Frame(self.table_frame)
        self.table_container.pack(fill='both', expand=True, padx=10, pady=10)

        # Создаем стиль для увеличенного шрифта
        style = ttk.Style()
        style.configure("Treeview", font=('TkDefaultFont', 11))  # Увеличиваем шрифт на 2 пункта
        style.configure("Treeview.Heading", font=('TkDefaultFont', 10, 'bold'))  # Для заголовков

        # Создаем Treeview с двумя колонками
        self.tree = ttk.Treeview(self.table_container, columns=('Поле', 'Значение'),
                                show='headings',
                                style="Treeview")

        # Настраиваем заголовки колонок
        self.tree.heading('Поле', text='Поле')
        self.tree.heading('Значение', text='Значение')

        # Настраиваем ширину колонок
        self.tree.column('Поле', width=150)
        self.tree.column('Значение', width=300)

        # Добавляем полосу прокрутки
        scrollbar = ttk.Scrollbar(self.table_container, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Размещаем элементы
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')


    def select_pdf(self):
        """Выбор PDF файла"""
        self.pdf_path = filedialog.askopenfilename(
            filetypes=[("PDF files", "*.pdf")]
        )
        if self.pdf_path:
            selected = self.selected_form.get()
            if selected not in ["СЦ МАЗ", "СЦ МАЗ ///", "Другая"]:
                # Активируем кнопку распознавания только для ЯМЗ и РСМ форм
                self.process_button.config(state='normal')

            # Очищаем предыдущие данные
            self.text_preview.delete('1.0', tk.END)
            self.tree.delete(*self.tree.get_children())
            self.save_button.config(state='disabled')


    def process_file(self):
        """Обработка PDF файла"""
        if self.pdf_path:
            # Словарь соответствия форм и процессоров
            processors = {
                "Группа ГАЗ": PDFProcessorYMZ,
                "Ростсельмаш": PDFProcessorRSM,
                "СЦ МАЗ": PDFProcessorMAZ,
                "СЦ МАЗ ///": PDFProcessorMAZ_2,
                "Другая": PDFProcessorAnother,
            }

            selected_form = self.selected_form.get()
            processor_class = processors.get(selected_form)

            if not processor_class:
                return

            processor = processor_class(self.pdf_path)

            # Для форм МАЗ, МАЗ/// и Другая обработка не требуется,
            # так как данные инициализированы в on_form_select()
            if selected_form in ["СЦ МАЗ", "СЦ МАЗ ///", "Другая"]:
                return

            # Для остальных форм - обычная обработка
            raw_text = processor.get_raw_text()
            self.text_preview.delete('1.0', tk.END)
            self.text_preview.insert('1.0', raw_text)

            # Получаем структурированные данные
            self.extracted_data = processor.extract_data()

            # Обновляем таблицу
            self.update_table_preview()

            # Активируем кнопки
            self.save_button.config(state='normal')
            self.edit_button.config(state='normal')


    def update_table_preview(self):
        """Обновление таблицы с данными"""
        # Очищаем существующие данные
        self.tree.delete(*self.tree.get_children())

        # Добавляем новые данные
        if self.extracted_data:
            for key, value in self.extracted_data.items():
                self.tree.insert('', 'end', values=(key, value))


    def enable_editing(self):
        """Включение режима редактирования данных"""
        # Создаем новое окно для редактирования
        edit_window = tk.Toplevel(self.root)
        edit_window.title("Редактирование данных")
        edit_window.geometry("600x450")

        # Создаем основной фрейм с отступами
        main_frame = ttk.Frame(edit_window, padding="10")
        main_frame.pack(fill='both', expand=True)

        # Создаем стиль для меток и полей
        label_font = ('TkDefaultFont', 10)
        entry_font = ('TkDefaultFont', 11)
        entry_width = 35

        # Загружаем список моделей двигателей
        try:
            with open('engine_models.txt', 'r', encoding='utf-8') as file:
                self.engine_models = sorted(line.strip() for line in file.readlines())
        except Exception as e:
            self.engine_models = ["53435", "534450", "53435-А02", "53445.1000140-АЗ2"]
            raise ExcelError(f"Ошибка при загрузке списка моделей: {str(e)}")

        # Создаем и размещаем элементы управления
        entries = {}
        for key, value in self.extracted_data.items():
            frame = ttk.Frame(main_frame)
            frame.pack(fill='x', pady=5)

            # Метка с фиксированной шириной
            label = ttk.Label(frame, text=key, font=label_font, width=25)
            label.pack(side='left', padx=(0, 10))

            # Для модели двигателя используем Combobox с автодополнением
            if key == "Модель двигателя":
                entry = ttk.Combobox(
                    frame,
                    font=entry_font,
                    width=entry_width,
                    values=self.engine_models
                )
                entry.set(value)
            else:
                # Для остальных полей используем обычные Entry
                entry = ttk.Entry(frame, font=entry_font, width=entry_width)
                entry.insert(0, value)

            entry.pack(side='left', fill='x', expand=True)
            entries[key] = entry

        # Фрейм для кнопок
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=20, fill='x')

        def save_changes():
            # Сначала обрабатываем модель двигателя, если она новая
            engine_entry = entries.get("Модель двигателя")
            if engine_entry:
                current_value = engine_entry.get()
                if current_value and current_value not in self.engine_models:
                    self.engine_models.append(current_value)
                    self.engine_models.sort()

            # Сохраняем измененные данные
            new_data = {}
            for key, entry in entries.items():
                new_data[key] = entry.get()

            self.extracted_data = new_data
            self.update_table_preview()

            # Сохраняем обновленный список моделей в файл
            try:
                with open('engine_models.txt', 'w', encoding='utf-8') as file:
                    file.write('\n'.join(self.engine_models))
            except Exception as e:
                raise ExcelError(f"Ошибка при сохранении списка моделей: {str(e)}")

            # Активируем кнопку "Сохранить в Excel"
            self.save_button.config(state='normal')

            edit_window.destroy()

        # Кнопка сохранения
        ttk.Button(
            button_frame,
            text="Сохранить",
            command=save_changes,
            style='Custom.TButton'
        ).pack(pady=10)

        # Центрируем окно
        edit_window.transient(self.root)
        edit_window.grab_set()
        edit_window.update_idletasks()
        width = edit_window.winfo_width()
        height = edit_window.winfo_height()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (width // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (height // 2)
        edit_window.geometry(f'+{x}+{y}')


    def save_to_excel(self):
        """Сохранение данных в Excel"""
        try:
            if self.extracted_data:
                excel_path = filedialog.asksaveasfilename(
                    defaultextension=".xlsx",
                    filetypes=[("Excel files", "*.xlsx")]
                )
                if excel_path:
                    excel_handler = ExcelHandler(excel_path)
                    excel_handler.write_data(self.extracted_data)
                    messagebox.showinfo("Успех", "Данные успешно сохранены в Excel")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при сохранении в ЖУРНАЛ УЧЕТА рекламаций: {str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = MainApplication(root)
    root.mainloop()
