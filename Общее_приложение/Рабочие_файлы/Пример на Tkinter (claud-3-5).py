# claude-3-5-sonnet-20241022

# Да, такое приложение можно реализовать с помощью Tkinter. Вот пример базовой структуры такого приложения:

import tkinter as tk
from tkinter import ttk

class MainWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Главное окно")
        self.root.geometry("400x300")

        # Создаем кнопки
        btn1 = ttk.Button(root, text="Задача 1", command=self.open_task1)
        btn1.pack(pady=10)

        btn2 = ttk.Button(root, text="Задача 2", command=self.open_task2)
        btn2.pack(pady=10)

        btn3 = ttk.Button(root, text="Задача 3", command=self.open_task3)
        btn3.pack(pady=10)

    def open_task1(self):
        task_window = tk.Toplevel(self.root)
        task_window.title("Задача 1")
        task_window.geometry("300x200")

        label = ttk.Label(task_window, text="Это окно задачи 1")
        label.pack(pady=20)

    def open_task2(self):
        task_window = tk.Toplevel(self.root)
        task_window.title("Задача 2")
        task_window.geometry("300x200")

        label = ttk.Label(task_window, text="Это окно задачи 2")
        label.pack(pady=20)

    def open_task3(self):
        task_window = tk.Toplevel(self.root)
        task_window.title("Задача 3")
        task_window.geometry("300x200")

        label = ttk.Label(task_window, text="Это окно задачи 3")
        label.pack(pady=20)

if __name__ == "__main__":
    root = tk.Tk()
    app = MainWindow(root)
    root.mainloop()

# В этом примере:
# 1. Создается главное окно с тремя кнопками
# 2. Каждая кнопка при нажатии открывает новое окно (Toplevel)
# 3. Новые окна можно настраивать независимо друг от друга
# 4. Главное окно остается активным, пока открыты дочерние окна

# Альтернативные варианты для создания такого приложения:
# 1. PyQt/PySide - более мощный фреймворк с современным дизайном
# 2. wxPython - нативный внешний вид на разных платформах
# 3. Kivy - хорош для создания приложений с современным интерфейсом

# Хотите, чтобы я показал пример реализации на одном из этих фреймворков?