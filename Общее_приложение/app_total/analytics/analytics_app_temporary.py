import tkinter as tk
from tkinter import ttk, messagebox


class AnalyticsApp(tk.Tk):
    def __init__(self):
        super().__init__()

        # self.iconbitmap("app_total/IconBZA.ico")  # Меняем логотип Tkinter на логотип БЗА
        self.title("Аналитика базы рекламаций ОТК")  # Заголовок приложения

        # Размер окна приложения
        # self.geometry("1000x700")
        width = 800  # ширина окна
        heigh = 550  # высота окна

        # Определяем координаты центра экрана и размещаем окно по центру экрана
        screenwidth = self.winfo_screenwidth()
        screenheight = self.winfo_screenheight()
        self.geometry("%dx%d+%d+%d" % (width, heigh, (screenwidth - width) / 2, (screenheight - heigh) / 3))

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
                            font=('Arial', 9, 'bold'),
                            # padding=5,
                            wraplength=600)

        # Создаем главное меню
        self.menubar = tk.Menu(self)
        self.config(menu=self.menubar)

        # Создаем основной контейнер
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill='both', expand=True, padx=20, pady=10)

        # Создаем строку внизу основного окна с текстом "Development by IGOR VASILENOK"
        self.footer_label = ttk.Label(self, text="Development by IGOR VASILENOK - версия 1.0  ", anchor='e')
        self.footer_label.pack(side='bottom', fill='x', pady=5)

        # Создаем заголовки
        self.headers_frame = ttk.Frame(self.main_frame)
        self.headers_frame.pack(fill='x', pady=5)

        ttk.Label(self.headers_frame, style='Header.TLabel').pack(side='left', padx=(0, 350))
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
            ("1",
             "",
             "Справка о количестве признанных рекламаций накопительным итогом с начала года",
             self.open_accept_defect),

            ("2",
             "",
             "Статистика длительности исследования рекламаций",
             self.open_duration_study),

            ("3",
             "",
             "Перечень рекламационных актов, по которым нет актов исследования",
             self.open_not_reports),

            ("4",
             "",
             "Диаграммы по данным базы рекламаций по потребителям или изделиям",
             self.open_diagrams),

            ("5",
             "",
             "Справка по актам исследования и датам уведомления при работе с претензиями потребителей",
             self.open_date_notification)
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
                                width=10)
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


    def open_accept_defect(self):
        pass


    def open_duration_study(self):
        pass


    def open_not_reports(self):
        pass


    def open_diagrams(self):
        pass


    def open_date_notification(self):
        pass



if __name__ == "__main__":
    app = AnalyticsApp()
    app.mainloop()