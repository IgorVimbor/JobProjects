import tkinter as tk
from tkinter import messagebox
from tkinter import ttk

from analytics.pretence.pretence_modul_1_v2 import Date_to_act


class PretenceDateAct(tk.Toplevel):
    """Окно для ввода данных, их обработки и вывода результата"""
    def __init__(self, master=None):
        super().__init__(master)

        self.grab_set()
        self.transient(master)

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

        ttk.Label(input_frame, text="Потребитель:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.client_entry = ttk.Entry(input_frame)
        self.client_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)

        ttk.Label(input_frame, text="Изделие:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.product_entry = ttk.Entry(input_frame)
        self.product_entry.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)

        ttk.Label(input_frame, text="Акты исследования для проверки:").grid(row=2, column=0, sticky=tk.NW, padx=5, pady=5)
        self.acts_text = tk.Text(input_frame, height=5, width=40)
        self.acts_text.grid(row=2, column=1, sticky=tk.EW, padx=5, pady=5)

        input_frame.columnconfigure(1, weight=1)

        process_button = ttk.Button(input_frame, text="Обработать данные", command=self.process_data)
        process_button.grid(row=3, column=0, columnspan=2, pady=10)

        result_frame = ttk.LabelFrame(self, text="Результат проверки")
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        result_frame.configure(style="Bold.TLabelframe")  # применение стиля для заголовка result_frame

        self.result_text = tk.Text(result_frame, wrap=tk.WORD)
        self.result_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        save_button = ttk.Button(self, text="Сохранить и записать", command=self.save_and_write)
        save_button.pack(pady=10)

    def write_to_result_text(self, text: str):
        self.result_text.insert(tk.END, text + "\n")
        self.result_text.see(tk.END)

    def process_data(self):
        client = self.client_entry.get().strip()
        product = self.product_entry.get().strip()
        acts_raw = self.acts_text.get("1.0", tk.END).strip()

        self.date_to_act_obj = Date_to_act(client, product, acts_raw)

        self.result_text.delete("1.0", tk.END)

        # Выводим результаты из модуля pretence_modul_2_v2 и из модуля pretence_modul_1_v2
        self.date_to_act_obj.print_results(write_func=self.write_to_result_text)

    def save_and_write(self):
        if self.date_to_act_obj is None:
            messagebox.showwarning("Внимание", "Сначала обработайте данные.", parrent=self)
            return

        self.date_to_act_obj.fill_values()
        messagebox.showinfo(
            "Информация",
            "Номера и даты актов исследования и даты уведомлений внесены в Журнал претензий.",
            parrent=self
            )
