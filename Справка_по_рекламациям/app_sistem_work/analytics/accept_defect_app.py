import os
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import pandas as pd

import paths_work # импортируем файл с путями до базы данных, отчетов и др.


class AcceptDefect(tk.Toplevel):
    def __init__(self, master=None):
        super().__init__(master)

        # Блокируем взаимодействие с родительским окном
        self.grab_set()
        self.transient(master)

        # Настройка окна
        self.title("Количество признанных рекламаций")
        self.iconbitmap("IconBZA.ico")

        width = 400
        heigh = 200
        screenwidth = self.winfo_screenwidth()
        screenheight = self.winfo_screenheight()
        self.geometry("%dx%d+%d+%d" % (width, heigh, (screenwidth - width) / 2, (screenheight - heigh) / 3))

        # Добавляем элементы интерфейса
        self.label = tk.Label(self, text="Обработка данных...")
        self.label.pack(pady=20)

        # Прогресс-бар
        self.progress = ttk.Progressbar(self, mode='determinate', maximum=100)
        self.progress.pack(pady=10, padx=20, fill=tk.X)

        # Запускаем обработку после полной инициализации окна
        self.after(100, self.start_processing)

    def start_processing(self):
        """Запускает процесс обработки с анимацией прогресс-бара"""
        self.progress["value"] = 0
        self.update_progress(0)

    def update_progress(self, value):
        """Обновляет прогресс-бар с анимацией"""
        if value < 100:
            self.progress["value"] = value
            self.after(20, lambda: self.update_progress(value + 2))
        else:
            # Когда прогресс достиг 100%, запускаем обработку данных
            self.after(100, self.process_data)

    def process_data(self):
        """Обработка данных из базы данных ОТК и вывод результата"""
        # Импортируем переменные из модуля paths_home
        self.year_now = paths_work.year_now  # текущий год
        self.date_new = paths_work.date_new  # сегодняшняя дата
        self.file = paths_work.file_database  # путь к базе данных ОТК
        self.file_txt = paths_work.accept_defect_otchet  # путь к файлу с отчетом

        try:
            # Обновляем статус в окне приложения
            self.label.config(text="Обработка данных...")

            # Создаем датафрейм из файла Excel базы ОТК
            df = pd.read_excel(
                self.file,
                sheet_name=str(self.year_now),
                usecols=[
                    "Период выявления дефекта (отказа)",
                    "Наименование изделия",
                    "Количество предъявленных изделий",
                    "Виновник дефекта - БЗА",
                    "Виновник дефекта - потребитель",
                    "Изделие соответствует  ТУ",
                    "Виновник не установлен",
                ],
                header=1,
            )

            # Переименовываем столбцы
            df.rename(
                columns={
                    "Период выявления дефекта (отказа)": "Потребитель",
                    "Наименование изделия": "Изделие",
                    "Количество предъявленных изделий": "Количество",
                    "Виновник дефекта - БЗА": "вин-БЗА",
                    "Виновник дефекта - потребитель": "вин-Потребитель",
                    "Изделие соответствует  ТУ": "вин-ТУ",
                    "Виновник не установлен": "вин-НЕТ",
                },
                inplace=True,
            )

            # Создаем временный датафрейм - копию исходного
            df_temp = df.copy()
            vin_columns = ['вин-БЗА', 'вин-Потребитель', 'вин-ТУ', 'вин-НЕТ']

            for col in vin_columns:
                df_temp[f"{col}_value"] = df_temp['Количество'] * df_temp[col].eq('+').astype(int)

            res_df = df_temp.groupby(['Потребитель', 'Изделие']).agg(
                Количество=('Количество', 'sum'),
                **{col: (f"{col}_value", 'sum') for col in vin_columns}
            ).reset_index()

            res_df[vin_columns] = res_df[vin_columns].astype(int)
            res_df['Количество'] = res_df['Количество'].astype(int)

            del df_temp  # Удаляем временный датафрейм

            res_df["Признано"] = res_df["вин-БЗА"] + res_df["вин-НЕТ"]
            res_df["Отклонено"] = res_df["вин-ТУ"] + res_df["вин-Потребитель"]
            res_df["Не поступало"] = res_df["Количество"] - (res_df["Признано"] + res_df["Отклонено"])

            self.res_df = res_df[['Потребитель', 'Изделие', 'Количество', 'Признано', 'Отклонено', 'Не поступало']]

            # Записываем результаты в файл
            with open(self.file_txt, "w", encoding="utf-8") as f:
                print(f"\n\n\tСправка по количеству признанных рекламаций на {self.date_new}\n\n", file=f)
                f.write(self.res_df.to_string())

            # Обновляем интерфейс
            self.label.config(text="Обработка завершена!")

            # Показываем сообщение
            answer = messagebox.askyesno(
                "ИНФОРМАЦИЯ",
                f"Справка успешно создана и сохранена в файл:\n\n{self.file_txt}\n\nОткрыть файл?",
                parent=self
            )

            if answer:  # Если пользователь нажал "Да"
                self._open_file(self.file_txt)

            # Закрываем окно после успешного завершения
            self.destroy()

        except Exception as e:
            self.label.config(text="Ошибка обработки!")
            messagebox.showerror(
                "ОШИБКА",
                f"Произошла ошибка при работе приложения:\n\n{e}",
                parent=self
            )
            self.destroy()

    def _open_file(self, file_path):
        """Открывает файл с помощью стандартного приложения Windows"""
        try:
            # Нормализация пути (устраняет проблемы с косыми чертами)
            normalized_path = os.path.abspath(file_path)
            os.startfile(normalized_path)
        except Exception as e:
            messagebox.showwarning(
                "Ошибка открытия",
                f"Не удалось открыть файл:\n{str(e)}",
                parent=self
            )
