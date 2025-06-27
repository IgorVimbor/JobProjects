import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from PIL import Image, ImageTk
import os

from backup.backup_app_v5 import *


class MainApplication:
    def __init__(self, root):
        self.root = root
        self.root.title("Система анализа рекламаций")

        # self.root.geometry("1000x700")
        # размер окна приложения
        width = 1000  # ширина окна
        heigh = 700  # высота окна
        # определяем координаты центра экрана и размещаем окно по центру экрана
        screenwidth = self.root.winfo_screenwidth()
        screenheight = self.root.winfo_screenheight()
        self.root.geometry(
            "%dx%d+%d+%d"
            % (width, heigh, (screenwidth - width) / 2, (screenheight - heigh) / 3)
        )

        # Настройка стилей
        self.style = ttk.Style()

        # Стиль для кнопок - шрифт Arial, размер 10, жирный
        self.style.configure('Custom.TButton',
                            padding=10,
                            font=('Arial', 10, 'bold'))

        # Стиль для заголовков LabelFrame (Приложение и Описание)
        self.style.configure('Header.TLabel',
                            font=('Arial', 12, 'bold'),
                            padding=10)

        # Стиль для заголовка LabelFrame описаний
        self.style.configure('Desc.TLabelframe.Label',
                            font=('Arial', 10, 'bold'))

        # Стиль для текста описания действий
        self.style.configure('Description.TLabel',
                            font=('Arial', 9),
                            padding=5,
                            wraplength=650)

        # Создаем главное меню
        self.menubar = tk.Menu(root)
        self.root.config(menu=self.menubar)

        self.file_menu = tk.Menu(self.menubar, tearoff=0)
        self.help_menu = tk.Menu(self.menubar, tearoff=0)

        self.menubar.add_cascade(label="Файл", menu=self.file_menu)
        self.menubar.add_cascade(label="Справка", menu=self.help_menu)

        self.file_menu.add_command(label="Выход", command=root.quit)
        self.help_menu.add_command(label="О программе", command=self.show_about)

        # Создаем основной контейнер
        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(fill='both', expand=True, padx=20, pady=10)

        # Создаем строку внизу основного окна с текстом "Development by IGOR VASILENOK"
        self.footer_label = ttk.Label(root, text="Development by IGOR VASILENOK - версия 1.0  ", anchor='e')
        self.footer_label.pack(side='bottom', fill='x', pady=5)

        # Создаем заголовки
        self.headers_frame = ttk.Frame(self.main_frame)
        self.headers_frame.pack(fill='x', pady=5)

        ttk.Label(self.headers_frame, text="Приложение", style='Header.TLabel').pack(side='left', padx=(0, 400))
        ttk.Label(self.headers_frame, text="Описание", style='Header.TLabel').pack(side='left')

        # Создаем контейнер для содержимого с прокруткой
        self.canvas = tk.Canvas(self.main_frame)
        self.scrollbar = ttk.Scrollbar(self.main_frame, orient="vertical", command=self.canvas.yview)
        self.content_frame = ttk.Frame(self.canvas)

        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas_frame = self.canvas.create_window((0, 0), window=self.content_frame, anchor="nw")

        self.content_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", self.on_canvas_configure)

        # Список кнопок и их описаний
        self.buttons = [
            ("Аналитика базы ОТК",
             "Анализ базы рекламаций по выбранному (-ым) году (-ам)",
             "- статистика длительности исследования рекламаций;\n" +
             "- перечень рекламационных актов, по которым нет актов исследования;\n" +
             "- справка о количестве признанных (не признанных) рекламаций накопительным итогом с начала года;\n" +
             "- диаграммы по данным базы рекламаций по потребителям или изделиям, другая аналитика;\n" +
             "- справка по наличию актов исследований и дате уведомления при работе с претензиями потребителей.",
             self.open_analytics_window),

            ("Поиск по базе ОТК",
             "Получение данных по номеру двигателя и/или акта рекламации",
             "- показывает номер строки в базе ОТК при наличии двигателя и/или акта рекламации;\n" +
             "- делает отчет по данным базы рекламаций по указанным двигателям и/или актам и сохраняет в файл.",
             self.open_search_window),

            ("Поиск двигателя по изделию",
             "Получение данных по номеру изделия БЗА",
             "- показывает номер строки в базе по номеру изделия (если нет номера двигателя или акта рекламации).",
             self.open_search_by_product_window),

            ("Справка по рекламациям",
             "Справка по количеству рекламаций за период",
             "- создает справку по количеству рекламаций за период и сохраняет в файл.",
             self.open_claims_report_window),

            ("Анализ браковок",
             "Статистика по журналу учета актов о браке",
             "- статистика по списанию деталей и комплектующих по периоду, наименованию и обозначению, др.",
             self.open_defects_analysis_window),

            ("Копирование отгрузки",
             "Внесение данных по отгрузке в файлы ОТК",
             "- записываются данные по отгрузке за отчетный месяц, производится расчет гарантийного парка;\n" +
             "- заполняются таблицы в отчетах по дефектности БЗА.",
             self.open_shipping_copy_window),

            ("Резервное копирование",
             "Копирование выбранных файлов и папок",
             "- проводит копирование выбранных файлов и папок в указанное место",
             self.open_backup_window),

            ("Подготовка базы ОТК",
             "Подготавливает базу рекламаций на следующий год",
             "- очищает и подготавливает файл базы рекламаций на следующий календарный год",
             self.open_database_prep_window)
        ]

        # Создаем кнопки и описания
        for i, (btn_text, lbl_text, description, command) in enumerate(self.buttons):
            # Создаем строку для кнопки и описания
            row_frame = ttk.Frame(self.content_frame)
            row_frame.pack(fill='x', pady=5)

            # Создаем LabelFrame для кнопки
            btn_frame = ttk.LabelFrame(row_frame, text="")
            btn_frame.pack(side='left', padx=(0, 20))

            button = ttk.Button(btn_frame,
                              text=btn_text,
                              style='Custom.TButton',
                              command=command,
                              width=30)
            button.pack(padx=5, pady=5)

            # Создаем LabelFrame для описания
            # Применяем стиль 'Desc.TLabelframe.Label' для заголовка LabelFrame описаний
            desc_frame = ttk.LabelFrame(row_frame, text=lbl_text, style='Desc.TLabelframe')
            desc_frame.pack(side='left', fill='x', expand=True)

            desc_label = ttk.Label(desc_frame,
                                 text=description,
                                 style='Description.TLabel',
                                 justify='left')
            desc_label.pack(fill='x', padx=5, pady=5)

    def on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_frame, width=event.width)

    # [Остальные методы остаются без изменений]
    def open_analytics_window(self):
        window = tk.Toplevel(self.root)
        window.title("Аналитика базы ОТК")
        window.geometry("800x600")

        # Создаем вкладки
        notebook = ttk.Notebook(window)
        notebook.pack(fill='both', expand=True, pady=10, padx=10)

        # Вкладка статистики
        stats_frame = ttk.Frame(notebook)
        notebook.add(stats_frame, text="Статистика")

        # График
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.bar(['Янв', 'Фев', 'Мар', 'Апр'], [10, 15, 13, 17])
        ax.set_title('Количество рекламаций по месяцам')

        canvas = FigureCanvasTkAgg(fig, stats_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(pady=10)

        # Вкладка с таблицей
        table_frame = ttk.Frame(notebook)
        notebook.add(table_frame, text="Данные")

        # Создаем таблицу
        columns = ('Дата', 'Номер акта', 'Статус', 'Длительность')
        tree = ttk.Treeview(table_frame, columns=columns, show='headings')

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100)

        # Добавляем тестовые данные
        for i in range(10):
            tree.insert('', 'end', values=(f'2024-{i+1:02d}-01', f'АКТ-{i+1}', 'В работе', f'{i+5} дней'))

        tree.pack(pady=10, padx=10, fill='both', expand=True)

    def open_search_window(self):
        window = tk.Toplevel(self.root)
        window.title("Поиск по базе ОТК")
        window.geometry("600x400")

        # Создаем форму поиска
        search_frame = ttk.LabelFrame(window, text="Параметры поиска", padding=20)
        search_frame.pack(fill='x', pady=10, padx=10)

        ttk.Label(search_frame, text="Номер двигателя:").grid(row=0, column=0, pady=5)
        engine_entry = ttk.Entry(search_frame)
        engine_entry.grid(row=0, column=1, pady=5)

        ttk.Label(search_frame, text="Номер акта:").grid(row=1, column=0, pady=5)
        act_entry = ttk.Entry(search_frame)
        act_entry.grid(row=1, column=1, pady=5)

        ttk.Button(search_frame, text="Поиск", style='Custom.TButton').grid(row=2, column=0, columnspan=2, pady=20)

    def open_search_by_product_window(self):
        window = tk.Toplevel(self.root)
        window.title("Поиск двигателя по изделию")
        window.geometry("600x400")

    def open_claims_report_window(self):
        window = tk.Toplevel(self.root)
        window.title("Справка по рекламациям")
        window.geometry("600x400")

    def open_defects_analysis_window(self):
        window = tk.Toplevel(self.root)
        window.title("Анализ браковок")
        window.geometry("600x400")

    def open_shipping_copy_window(self):
        window = tk.Toplevel(self.root)
        window.title("Копирование отгрузки")
        window.geometry("600x400")

    def open_backup_window(self):
        # window = tk.Toplevel(self.root)
        # window.title("Резервное копирование")
        # window.geometry("600x400")
        backup_app = App()
        backup_app.winfo_toplevel()
        backup_app.mainloop()

    def open_database_prep_window(self):
        window = tk.Toplevel(self.root)
        window.title("Очистка и подготовка базы ОТК")
        window.geometry("600x400")

    def show_about(self):
        messagebox.showinfo("О программе",
                          "Система анализа рекламаций\nВерсия 1.0\n\n" +
                          "Программа для анализа и обработки данных по рекламациям")

def main():
    root = tk.Tk()
    app = MainApplication(root)
    root.mainloop()

if __name__ == "__main__":
    main()
