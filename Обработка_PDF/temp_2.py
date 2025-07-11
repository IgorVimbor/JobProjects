import tkinter as tk
from tkinter import filedialog, ttk, scrolledtext, messagebox
from temp_1 import PDFProcessorYMZ
from excel_handler import ExcelHandler

class MainApplication:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF to Excel Converter")
        self.root.geometry("800x600")

        # Настраиваем стили
        style = ttk.Style()

        # Вариант 1: Современный объемный стиль
        style.configure(
            'Custom.TButton',
            background='#4a90e2',
            foreground='black',
            padding=(5, 5),  # горизонтальный и вертикальный отступы
            font=('Arial', 8, 'bold'),
            relief='solid',  # 'raised', 'sunken', 'flat', 'ridge', 'solid', or 'groove'
            borderwidth=2
        )

        # Вариант 2: Более классический объемный стиль
        # style.configure(
        #     'Custom.TButton',
        #     padding=(5, 5),
        #     font=('Arial', 8, 'bold'),
        #     background='#e1e1e1',
        #     relief='raised',
        #     borderwidth=2
        # )
        # style.map('Custom.TButton',
        #     background=[('active', '#d1d1d1')],
        #     relief=[('pressed', 'sunken')],
        #     borderwidth=[('pressed', 3)]
        # )

        # # Настройка стиля при наведении
        # style.map('Custom.TButton',
        #     background=[('active', '#357abd')],
        #     relief=[('pressed', 'sunken')]
        # )

        # # Вариант 3: Минималистичный стиль
        # style.configure(
        #     'Custom.TButton',
        #     padding=(5, 5),
        #     font=('Arial', 8),
        #     background='#ffffff',
        #     relief='flat',
        #     borderwidth=1
        # )
        # style.map('Custom.TButton',
        #     background=[('active', '#f0f0f0')],
        #     borderwidth=[('active', 2)]
        # )

        # Создаем верхний фрейм для кнопок и радиокнопок
        self.top_frame = ttk.Frame(root)
        self.top_frame.pack(pady=10, padx=10, fill='x')

        # Кнопки
        self.select_button = ttk.Button(
            self.top_frame,
            text="Выбрать PDF файл",
            command=self.select_pdf,
            style='Custom.TButton'
        )
        self.select_button.pack(side='left', padx=5)

        self.process_button = ttk.Button(
            self.top_frame,
            text="Распознать текст",
            command=self.process_file,
            state='disabled',
            style='Custom.TButton'
        )
        self.process_button.pack(side='left', padx=5)

        # Создаем фрейм для радиокнопок
        self.radio_frame = ttk.LabelFrame(
            self.top_frame,
            text="Выберите стандартную форму акта рекламации:",
            padding=(10, 5)
        )
        self.radio_frame.pack(side='left', padx=20, fill='x', expand=True)

        # Стиль для радиокнопок
        style.configure(
            'Custom.TRadiobutton',
            font=('Arial', 9),
            padding=5
        )

        # Переменная для радиокнопок
        self.selected_form = tk.StringVar()

        # Создаем радиокнопки
        forms = ["Группа ГАЗ", "Ростсельмаш", "СЦ МАЗ", "СЦ МАЗ ///"]
        for form in forms:
            rb = ttk.Radiobutton(
                self.radio_frame,
                text=form,
                value=form,
                variable=self.selected_form,
                style='Custom.TRadiobutton'
            )
            rb.pack(side='left', padx=10)

        # По умолчанию выбираем первую форму
        self.selected_form.set("Группа ГАЗ")


    def select_pdf(self):
        pass


    def process_file(self):
        pass


if __name__ == "__main__":
    root = tk.Tk()
    app = MainApplication(root)
    root.mainloop()