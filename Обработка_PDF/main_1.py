import tkinter as tk
from tkinter import filedialog, ttk, scrolledtext
from temp_1 import PDFProcessor
from excel_handler import ExcelHandler

class MainApplication:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF to Excel Converter")
        self.root.geometry("800x600")

        # Создаем фреймы для организации элементов
        self.button_frame = ttk.Frame(root)
        self.button_frame.pack(pady=10, padx=10, fill='x')

        self.preview_frame = ttk.Frame(root)
        self.preview_frame.pack(pady=10, padx=10, fill='both', expand=True)

        # Кнопки в верхнем фрейме
        self.select_button = ttk.Button(
            self.button_frame,
            text="Выбрать PDF файл",
            command=self.select_pdf
        )
        self.select_button.pack(side='left', padx=5)

        self.process_button = ttk.Button(
            self.button_frame,
            text="Распознать текст",
            command=self.process_file,
            state='disabled'
        )
        self.process_button.pack(side='left', padx=5)

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
            state='disabled'
        )
        self.save_button.pack(side='right', padx=5)

        self.edit_button = ttk.Button(
            self.control_frame,
            text="Редактировать",
            command=self.enable_editing,
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

        # Создаем Treeview с двумя колонками
        self.tree = ttk.Treeview(self.table_container, columns=('Поле', 'Значение'), show='headings')

        # Настраиваем заголовки колонок
        self.tree.heading('Поле', text='Поле')
        self.tree.heading('Значение', text='Значение')

        # Настраиваем ширину колонок
        self.tree.column('Поле', width=150)
        self.tree.column('Значение', width=250)

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
            pdf_processor = PDFProcessor(self.pdf_path)

            # Получаем распознанный текст
            raw_text = pdf_processor.get_raw_text()
            self.text_preview.delete('1.0', tk.END)
            self.text_preview.insert('1.0', raw_text)

            # Получаем структурированные данные
            self.extracted_data = pdf_processor.extract_data()

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
        edit_window.geometry("400x300")

        # Создаем и размещаем элементы управления
        for key, value in self.extracted_data.items():
            frame = ttk.Frame(edit_window)
            frame.pack(fill='x', padx=5, pady=2)

            ttk.Label(frame, text=key).pack(side='left')
            entry = ttk.Entry(frame)
            entry.insert(0, value)
            entry.pack(side='right', expand=True, fill='x')

        def save_changes():
            # Сохраняем измененные данные
            new_data = {}
            for child in edit_window.winfo_children():
                if isinstance(child, ttk.Frame):
                    key = child.winfo_children()[0]['text']
                    value = child.winfo_children()[1].get()
                    new_data[key] = value

            self.extracted_data = new_data
            self.update_table_preview()
            edit_window.destroy()

        ttk.Button(edit_window, text="Сохранить", command=save_changes).pack(pady=10)

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
                tk.messagebox.showinfo("Успех", "Данные успешно сохранены в Excel")

if __name__ == "__main__":
    root = tk.Tk()
    app = MainApplication(root)
    root.mainloop()