# Основной исполняемый модуль приложения <Аналитическая система УК>

import tkinter as tk
from tkinter import ttk, messagebox

from backup.backup_app import App
from db_search.db_search_app import AppSearch
from engine_search.engine_search_app import SearchEngine
from enquiry_period.enquiry_period_app import EnquiryPeriod
from copier.copier_app import CopierData


class MainApplication:
    def __init__(self, root):
        self.root = root

        # self.root.iconbitmap("app_total/IconBZA.ico")  # Меняем логотип Tkinter на логотип БЗА
        self.root.title("АНАЛИТИЧЕСКАЯ СИСТЕМА УПРАВЛЕНИЯ КАЧЕСТВА")  # Заголовок приложения

        # Размер окна приложения
        # self.root.geometry("1000x700")
        width = 1000  # ширина окна
        heigh = 840  # высота окна

        # Определяем координаты центра экрана и размещаем окно по центру экрана
        screenwidth = self.root.winfo_screenwidth()
        screenheight = self.root.winfo_screenheight()
        self.root.geometry("%dx%d+%d+%d" % (width, heigh, (screenwidth - width) / 2, (screenheight - heigh) / 3))

        # Настройка стилей
        self.style = ttk.Style()

        # Стиль для кнопок - шрифт Arial, размер 10, жирный
        self.style.configure('Custom.TButton',
                            padding=10,
                            font=('Arial', 10, 'bold'),
                            background='green')

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

        ttk.Label(self.headers_frame, text="Приложение", style='Header.TLabel').pack(side='left', padx=(50, 350))
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


    def open_analytics_window(self):
        window = tk.Toplevel(self.root)
        window.title("Аналитика базы ОТК")
        window.geometry("600x400")
        # Делаем окно активным
        window.lift()
        window.focus_set()

        # messagebox.showinfo(
        #     "Аналитика базы ОТК",
        #     "ПРИЛОЖЕНИЕ В РАЗРАБОТКЕ"
        # )


    def open_search_window(self):
        """метод для запуска приложения <Поиск по базе ОТК>"""
        db_search_app = AppSearch(self.root)
        # Делаем окно активным
        db_search_app.lift()
        db_search_app.focus_set()


    def open_search_by_product_window(self):
        """метод для запуска приложения <Поиск двигателя по изделию>"""
        engine_search_app = SearchEngine(self.root)
        # Делаем окно активным
        engine_search_app.lift()
        engine_search_app.focus_set()


    def open_claims_report_window(self):
        """метод для запуска приложения <Справка за период>"""
        enquiry_period_app = EnquiryPeriod(self.root)
        # Делаем окно активным
        enquiry_period_app.lift()
        enquiry_period_app.focus_set()


    def open_defects_analysis_window(self):
        # window = tk.Toplevel(self.root)
        # window.title("Анализ браковок")
        # window.geometry("600x400")
        # # Делаем окно активным
        # window.lift()
        # window.focus_set()
        messagebox.showinfo(
            "Анализ браковок",
            "ПРИЛОЖЕНИЕ В РАЗРАБОТКЕ"
        )


    def open_shipping_copy_window(self):
        """метод для запуска приложения <Копирование отгрузки>"""
        copier = CopierData(self.root)
        # Делаем окно активным
        copier.lift()
        copier.focus_set()


    def open_backup_window(self):
        """метод для запуска приложения <Резервное_копирование>"""
        backup_app = App(self.root)
        # Делаем окно активным
        backup_app.lift()
        backup_app.focus_set()


    def open_database_prep_window(self):
        window = tk.Toplevel(self.root)
        window.title("Очистка и подготовка базы ОТК")
        window.iconbitmap("app_total/IconBZA.ico")

        # window.geometry("400x190")
        width = 400  # ширина окна
        heigh = 190  # высота окна

        # Определяем координаты центра экрана и размещаем окно по центру экрана
        screenwidth = window.winfo_screenwidth()
        screenheight = window.winfo_screenheight()
        window.geometry("%dx%d+%d+%d" % (width, heigh, (screenwidth - width) / 2, (screenheight - heigh) / 3))

        # Делаем окно активным
        window.lift()
        window.focus_set()

        search_frame = ttk.LabelFrame(window, text="Для входа в приложение введите пароль", padding=20)
        search_frame.pack(fill='x', pady=10, padx=10)

        ttk.Label(search_frame, text="Пароль:").grid(row=0, column=0, padx=20, pady=5)
        password_entry = ttk.Entry(search_frame)
        password_entry.grid(row=0, column=1, pady=5)

        ttk.Button(search_frame, text="Отправить", style='Custom.TButton').grid(row=0, column=2, padx=20, pady=20)


    def show_about(self):
        messagebox.showinfo("О программе",
                          "Аналитическая система Управления качества БЗА\nВерсия 1.0\n\n" +
                          "Система состоит из приложений для анализа и обработки данных по рекламациям.\n\n\n" +
                          "Идея и реализация - Василёнок Игорь")


def main():
    root = tk.Tk()
    app = MainApplication(root)
    root.mainloop()

if __name__ == "__main__":
    main()
