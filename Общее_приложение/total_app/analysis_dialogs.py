import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class AnalysisDialogs:
    """
    Класс AnalysisDialogs предоставляет диалоги для анализа данных:
    описательная статистика, корреляционный анализ и визуализация.
    """
    def __init__(self, parent, data, display_callback, status_var, save_plot_callback):
        self.parent = parent  # Родительское окно
        self.data = data  # Данные для анализа (pandas DataFrame)
        self.display_data = display_callback  # Функция для отображения данных
        self.status_var = status_var  # Переменная для строки состояния
        self.save_plot = save_plot_callback  # Функция для сохранения графиков

    def show_descriptive_statistics(self):
        """
        Показывает окно с описательной статистикой и выбором столбцов.
        """
        if self.data is None:
            messagebox.showwarning("Предупреждение", "Нет данных для анализа")
            return

        stats_window = tk.Toplevel(self.parent)
        stats_window.title("Описательная статистика")
        stats_window.geometry("800x600")

        selection_frame = ttk.LabelFrame(stats_window, text="Выбор столбцов")
        selection_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        canvas = tk.Canvas(selection_frame)
        scrollbar = ttk.Scrollbar(selection_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        numeric_columns = self.data.select_dtypes(include=[np.number]).columns

        self.column_vars = {}
        for col in numeric_columns:
            var = tk.BooleanVar(value=True)
            self.column_vars[col] = var
            ttk.Checkbutton(scrollable_frame, text=col, variable=var).pack(anchor=tk.W, padx=5)

        ttk.Button(stats_window, text="Обновить",
                   command=lambda: self.update_statistics(stats_window)).pack(side=tk.RIGHT, padx=5, pady=5)

        self.stats_text = tk.Text(stats_window, wrap=tk.WORD, width=80, height=20)
        self.stats_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.update_statistics(stats_window)

    def update_statistics(self, window):
        """
        Обновляет статистику в текстовом поле на основе выбранных столбцов.
        """
        selected_columns = [col for col, var in self.column_vars.items() if var.get()]

        if not selected_columns:
            messagebox.showwarning("Предупреждение", "Выберите хотя бы один столбец")
            return

        stats = self.data[selected_columns].describe()
        stats.loc['median'] = self.data[selected_columns].median()
        stats.loc['mode'] = self.data[selected_columns].mode().iloc[0]
        stats.loc['skew'] = self.data[selected_columns].skew()
        stats.loc['kurtosis'] = self.data[selected_columns].kurtosis()

        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(tk.END, "Описательная статистика:\n\n")
        self.stats_text.insert(tk.END, stats.round(2).to_string())

        self.stats_text.insert(tk.END, "\n\nДополнительная информация:\n")
        for col in selected_columns:
            null_count = self.data[col].isnull().sum()
            unique_count = self.data[col].nunique()
            self.stats_text.insert(tk.END,
                                   f"\n{col}:\n"
                                   f"Пропущенные значения: {null_count}\n"
                                   f"Уникальные значения: {unique_count}\n")

    def show_correlation_analysis(self):
        """
        Показывает окно с корреляционной матрицей и тепловой картой.
        """
        if self.data is None:
            messagebox.showwarning("Предупреждение", "Нет данных для анализа")
            return

        corr_window = tk.Toplevel(self.parent)
        corr_window.title("Корреляционный анализ")
        corr_window.geometry("800x600")

        numeric_data = self.data.select_dtypes(include=[np.number])

        if numeric_data.empty:
            messagebox.showwarning("Предупреждение", "Нет числовых данных для анализа")
            return

        corr_matrix = numeric_data.corr()

        fig, ax = plt.subplots(figsize=(10, 8))
        im = ax.imshow(corr_matrix, cmap='coolwarm')

        ax.set_xticks(np.arange(len(corr_matrix.columns)))
        ax.set_yticks(np.arange(len(corr_matrix.columns)))
        ax.set_xticklabels(corr_matrix.columns, rotation=45, ha='right')
        ax.set_yticklabels(corr_matrix.columns)

        for i in range(len(corr_matrix.columns)):
            for j in range(len(corr_matrix.columns)):
                ax.text(j, i, f"{corr_matrix.iloc[i, j]:.2f}",
                        ha="center", va="center", color="black")

        plt.colorbar(im)

        canvas = FigureCanvasTkAgg(fig, master=corr_window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        ttk.Button(corr_window, text="Сохранить график",
                   command=lambda: self.save_plot(fig)).pack(pady=5)
