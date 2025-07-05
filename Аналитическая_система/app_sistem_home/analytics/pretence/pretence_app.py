import tkinter as tk
from tkinter import messagebox
from tkinter import ttk

from analytics.pretence.pretence_modul_1 import Date_to_act


class PretenceDateAct(tk.Toplevel):
    """Окно для ввода данных, их обработки и вывода результата"""
    def __init__(self, master=None):
        super().__init__(master)

        self.title("Даты уведомления по рекламациям")
        self.iconbitmap("IconBZA.ico")

        width = 900
        heigh = 850
        screenwidth = self.winfo_screenwidth()
        screenheight = self.winfo_screenheight()
        self.geometry("%dx%d+%d+%d" % (width, heigh, (screenwidth - width) / 2, (screenheight - heigh) / 3))

        self.date_to_act_obj = None

        # Установка стилей для заголовков фреймов (жирный шрифт и размер11)
        style = ttk.Style()
        style.configure("Bold.TLabelframe.Label", font=("TkDefaultFont", 11, "bold"))

        input_frame = ttk.LabelFrame(self, text="Введите данные")
        input_frame.pack(fill=tk.X, padx=10, pady=10)
        input_frame.configure(style="Bold.TLabelframe")  # применение стиля для заголовка input_frame

        # Создаем контейнер для полей ввода
        entry_container = ttk.Frame(input_frame)
        entry_container.grid(row=0, column=1, sticky=tk.EW)
        input_frame.columnconfigure(1, weight=1)

        ttk.Label(input_frame, text="Потребитель:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.client_entry = ttk.Entry(input_frame, width=100)
        self.client_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        self.client_entry.insert(0, "ЯМЗ - эксплуатация")

        ttk.Label(input_frame, text="Изделие:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.product_entry = ttk.Entry(input_frame, width=100)
        self.product_entry.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)
        self.product_entry.insert(0, "водяной насос")

        ttk.Label(input_frame, text="Акты исследования для проверки:").grid(row=2, column=0, sticky=tk.NW, padx=5, pady=5)
        self.acts_text = tk.Text(input_frame, height=5, width=100)
        self.acts_text.grid(row=2, column=1, sticky=tk.EW, padx=5, pady=5)

        button_container = ttk.Frame(input_frame)
        button_container.grid(row=3, column=1, pady=10, sticky=tk.E)

        process_button = ttk.Button(button_container, text="Обработать данные", command=self.process_data)
        process_button.pack(side=tk.LEFT, padx=(0, 10))

        clear_input_button = ttk.Button(button_container, text="Очистить", command=self.clear_input_fields)
        clear_input_button.pack(side=tk.LEFT)

        result_frame = ttk.LabelFrame(self, text="Результат проверки")
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        result_frame.configure(style="Bold.TLabelframe")

        self.result_text = tk.Text(result_frame, wrap=tk.WORD)
        self.result_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        button_frame = ttk.Frame(self)
        button_frame.pack(pady=10, anchor='e')

        save_button = ttk.Button(button_frame, text="Сохранить и записать", command=self.save_and_write)
        save_button.pack(side=tk.LEFT, padx=10)

        clear_result_button = ttk.Button(button_frame, text="Очистить", command=self.clear_result_field)
        clear_result_button.pack(side=tk.LEFT, padx=10)


    def write_to_result_text(self, text: str):
        self.result_text.insert(tk.END, text + "\n")
        self.result_text.see(tk.END)


    def clear_input_fields(self):
        self.client_entry.delete(0, tk.END)
        self.product_entry.delete(0, tk.END)
        self.acts_text.delete("1.0", tk.END)


    def clear_result_field(self):
        self.result_text.delete("1.0", tk.END)


    def acts_from_journal_print_results(self, acts_checker):
        """
        Перенос print_results() из класса ActsFromJournal с выводом в текстовое поле
        """
        if acts_checker.acts_in_journal:
            self.write_to_result_text(f"\nАкты, которые есть в Журнале {acts_checker.sheet_name} года:")
            for act in acts_checker.acts_in_journal:
                self.write_to_result_text(act)
        else:
            self.write_to_result_text(f"\nУказанных актов в Журнале {acts_checker.sheet_name} года нет.")

        self.write_to_result_text("\nСписок актов: " + str(acts_checker.numbers_acts))
        self.write_to_result_text("Всего актов: " + str(len(acts_checker.numbers_acts)))

        for year, acts in acts_checker.years_list_acts.items():
            self.write_to_result_text(f"Акты {year} года: {acts}")


    def date_to_act_print_results(self):
        """
        Перенос print_results() из класса Date_to_act с выводом в текстовое поле
        """
        # Итоговый датафрейм класса ActsFromJournal с развернутыми датами актов и уведомлений
        self.date_to_act_obj.result = self.date_to_act_obj.get_frame()
        # Итоговый датафрейм класса Date_to_act с короткими датами актов и уведомлений
        self.date_to_act_obj.df_journal = self.date_to_act_obj.get_small_frame()

        # Записываем в файл Excel (файл закрывается перед записью, если открыт)
        self.date_to_act_obj.excel_close_write(self.date_to_act_obj.result)
        # Редактируем стили таблицы в записанном файле Excel
        self.date_to_act_obj.transform_excel(self.date_to_act_obj.result)

        # Выводим результаты класса ActsFromJournal
        self.acts_from_journal_print_results(self.date_to_act_obj.acts_checker)
        self.write_to_result_text("")  # Пустая строка для разделения вывода

        self.write_to_result_text(" " * 30 + "Данные для внесения в Журнал претензий")
        self.write_to_result_text("")

        # Выводим результаты класса Date_to_act
        self.write_to_result_text("Количество актов в таблице - " + str(len(self.date_to_act_obj.result)))
        self.write_to_result_text("")
        # Выводим итоговый датафрейм с короткими датами актов и уведомлений
        self.write_to_result_text(str(self.date_to_act_obj.df_journal.set_index("Номер и дата акта исследования")))


    def process_data(self):
        client = self.client_entry.get().strip()
        product = self.product_entry.get().strip()
        acts_raw = self.acts_text.get("1.0", tk.END).strip()

        self.date_to_act_obj = Date_to_act(client, product, acts_raw)

        self.result_text.delete("1.0", tk.END)
        self.date_to_act_print_results()


    def save_and_write(self):
        if self.date_to_act_obj is None:
            messagebox.showwarning("Внимание", "Сначала обработайте данные.", parent=self)
            return

        self.date_to_act_obj.close_journal_write_value()

        messagebox.showinfo(
            "Информация",
            "Номера и даты актов исследования и даты уведомлений внесены в Журнал претензий.",
            parent=self
        )
