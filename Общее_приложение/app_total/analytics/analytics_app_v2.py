import tkinter as tk
from tkinter import ttk
from tkinter import font

from analytics.accept_defect_app import AcceptDefect


class AnalyticsApp(tk.Toplevel):
    def __init__(self, master=None):
        super().__init__(master)

        self.title("Аналитика базы рекламаций ОТК")
        self.iconbitmap("app_total/IconBZA.ico")

        width = 750
        heigh = 550
        screenwidth = self.winfo_screenwidth()
        screenheight = self.winfo_screenheight()
        self.geometry("%dx%d+%d+%d" % (width, heigh, (screenwidth - width) / 2, (screenheight - heigh) / 3))

        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(main_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        canvas = tk.Canvas(main_frame, yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=canvas.yview)

        content_frame = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=content_frame, anchor='nw')

        bold_font = font.Font(weight="bold")
        bold_underline_font = font.Font(weight="bold", underline=True)

        # Добавляем первую разделительную линию
        first_separator = ttk.Separator(content_frame, orient='horizontal')
        first_separator.pack(fill=tk.X, padx=20, pady=10)

        links_data = [
            ("Количество признанных / не признанных рекламаций",
             "Справка о количестве признанных / не признанных рекламаций накопительным итогом с начала года для отчетности",
             self.open_accept_defect),
            ("Длительность исследования рекламаций",
             "Статистика длительности исследования рекламаций для показателей премирования",
             self.open_duration_study),
            ("Не закрытые акты рекламаций",
             "Перечень рекламационных актов, по которым нет актов исследования",
             self.open_not_reports),
            ("Диаграммы по данным базы рекламаций",
             "Диаграммы по данным базы рекламаций по потребителям и/или изделиям и др. критериям",
             self.open_diagrams),
            ("Даты уведомления по рекламациям",
             "Справка по актам исследования и датам уведомления при рассмотрении претензий потребителей для передачи в ПЭО",
             self.open_date_notification)
        ]

        for i, (link_text, description, command) in enumerate(links_data):
            block_frame = ttk.Frame(content_frame)
            block_frame.pack(fill=tk.X, padx=20, pady=10)

            link = tk.Label(block_frame,
                          text=link_text,
                          font=bold_font,
                          fg="blue",
                          cursor="hand2")
            link.pack(anchor='w')

            link.bind("<Enter>", lambda e, l=link, uf=bold_underline_font: self.on_enter(l, uf))
            link.bind("<Leave>", lambda e, l=link, f=bold_font: self.on_leave(l, f))
            link.bind("<Button-1>", lambda e, cmd=command: cmd())

            description_label = tk.Label(block_frame,
                                      text=description,
                                      wraplength=700,
                                      justify=tk.LEFT)
            description_label.pack(anchor='w', pady=(5, 0))

            # Добавляем разделительные линии между блоками
            separator = ttk.Separator(content_frame, orient='horizontal')
            separator.pack(fill=tk.X, padx=20, pady=10)

        content_frame.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))

    def on_enter(self, label, underline_font):
        """Эффект при наведении курсора"""
        label.config(font=underline_font, fg='#0066CC')

    def on_leave(self, label, normal_font):
        """Эффект при уходе курсора"""
        label.config(font=normal_font, fg='blue')

    def open_accept_defect(self):
        new_window = AcceptDefect(self)
        new_window.lift()
        new_window.focus_set()

    def open_duration_study(self):
        new_window = tk.Toplevel(self)
        new_window.title("Длительность исследования рекламаций")
        new_window.geometry("600x400")

    def open_not_reports(self):
        new_window = tk.Toplevel(self)
        new_window.title("Не закрытые акты рекламаций")
        new_window.geometry("600x400")

    def open_diagrams(self):
        new_window = tk.Toplevel(self)
        new_window.title("Диаграммы по данным базы рекламаций")
        new_window.geometry("600x400")

    def open_date_notification(self):
        new_window = tk.Toplevel(self)
        new_window.title("Даты уведомления по рекламациям")
        new_window.geometry("600x400")
