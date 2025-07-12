import tkinter as tk
from tkinter import filedialog, ttk, scrolledtext, messagebox
from temp_2 import PDFProcessorYMZ, PDFProcessorRSM
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

        # Переменные для чек-боксов
        self.selected_form = tk.StringVar()

        # Создаем чек-боксы
        forms = ["Группа ГАЗ", "Ростсельмаш", "СЦ МАЗ", "СЦ МАЗ ///"]
        for form in forms:
            rb = ttk.Radiobutton(
                self.checkbox_frame,
                text=form,
                value=form,
                variable=self.selected_form
            )
            rb.pack(side='left', padx=10)

        # По умолчанию выбираем первую форму
        self.selected_form.set("Группа ГАЗ")

        # Остальные фреймы для организации элементов
        self.preview_frame = ttk.Frame(root)
        self.preview_frame.pack(pady=10, padx=10, fill='both', expand=True)

        # Создаем Notebook (вкладки) для предпросмотра
        self.notebook = ttk.Notebook(self.preview_frame)
        self.notebook.pack(fill='both', expand=True)

        # Вкладка с распознанным текстом
        self.text_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.text_frame, text='Распознанный текст')

        # Вкладка с данными таблицы
        self.table_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.table_frame, text='Данные таблицы')

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

        # Инициализация переменных
        self.pdf_path = None
        self.extracted_data = None


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
            self.process_button.config(state='normal')
            # Очищаем предыдущие данные
            self.text_preview.delete('1.0', tk.END)
            self.tree.delete(*self.tree.get_children())
            self.save_button.config(state='disabled')
            self.edit_button.config(state='disabled')


    def process_file(self):
        """Обработка PDF файла"""
        if self.pdf_path:
            # Выбираем соответствующий процессор в зависимости от выбранной формы
            processors = {
                "Группа ГАЗ": PDFProcessorYMZ,
                "Ростсельмаш": PDFProcessorRSM,
                # Добавим остальные процессоры позже
            }

            processor_class = processors.get(self.selected_form.get())
            if not processor_class:
                messagebox.showinfo("Информация", "Обработка данной формы пока не реализована")
                return

            processor = processor_class(self.pdf_path)

            # Получаем распознанный текст
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
        edit_window.geometry("600x400")  # Увеличиваем размер окна

        # Создаем основной фрейм с отступами
        main_frame = ttk.Frame(edit_window, padding="10")
        main_frame.pack(fill='both', expand=True)

        # Создаем стиль для меток
        label_font = ('TkDefaultFont', 10)
        entry_font = ('TkDefaultFont', 11)

        # Определяем максимальную ширину для полей ввода
        entry_width = 35  # Устанавливаем одинаковую ширину для всех полей

        # Создаем и размещаем элементы управления
        row = 0
        entries = {}
        for key, value in self.extracted_data.items():
            frame = ttk.Frame(main_frame)
            frame.pack(fill='x', pady=5)

            # Метка с фиксированной шириной
            label = ttk.Label(frame, text=key, font=label_font, width=25)
            label.pack(side='left', padx=(0, 10))

            # Поле ввода
            entry = ttk.Entry(frame, font=entry_font, width=entry_width)
            entry.insert(0, value)
            entry.pack(side='left', fill='x', expand=True)

            entries[key] = entry
            row += 1

        # Фрейм для кнопок
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=20, fill='x')

        def save_changes():
            # Сохраняем измененные данные
            new_data = {}
            for key, entry in entries.items():
                new_data[key] = entry.get()

            self.extracted_data = new_data
            self.update_table_preview()
            edit_window.destroy()

        # Кнопка сохранения с увеличенным шрифтом
        save_button = ttk.Button(
            button_frame,
            text="Сохранить",
            command=save_changes,
            style='Large.TButton'
        )
        save_button.pack(pady=10)

        # Создаем стиль для кнопки
        style = ttk.Style()
        style.configure('Large.TButton', font=('TkDefaultFont', 10))

        # Центрируем окно относительно главного окна
        edit_window.transient(self.root)
        edit_window.grab_set()

        # Размещаем окно по центру главного окна
        edit_window.update_idletasks()
        width = edit_window.winfo_width()
        height = edit_window.winfo_height()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (width // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (height // 2)
        edit_window.geometry(f'+{x}+{y}')


    def save_to_excel(self):
        """Сохранение данных в Excel"""
        if self.extracted_data:
            excel_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx")]
            )
            if excel_path:
                excel_handler = ExcelHandler(excel_path)
                excel_handler.write_data(self.extracted_data)
                messagebox.showinfo("Успех", "Данные успешно сохранены в Excel")


if __name__ == "__main__":
    root = tk.Tk()
    app = MainApplication(root)
    root.mainloop()
