# Вот пример реализации вашего приложения с использованием **wxPython**.

# В этом примере будет главное окно с кнопками, при нажатии на которые открываются дополнительные
# окна для выполнения конкретных задач.

# wxPython — это кроссплатформенная библиотека для создания GUI, которая предоставляет более современный
# внешний вид по сравнению с Tkinter и имеет богатый набор виджетов.

# Перед запуском кода убедитесь, что у вас установлена библиотека wxPython.
# Установить ее можно с помощью команды:  pip install wxPython

### Пример приложения на wxPython

import wx

# Класс главного окна
class MainWindow(wx.Frame):
    def __init__(self, parent, title):
        super(MainWindow, self).__init__(parent, title=title, size=(400, 300))

        # Создаем панель для размещения элементов
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        # Добавляем заголовок
        title_label = wx.StaticText(panel, label="Добро пожаловать в главное окно!", style=wx.ALIGN_CENTER)
        font = title_label.GetFont()
        font.PointSize += 4
        font = font.Bold()
        title_label.SetFont(font)
        vbox.Add(title_label, flag=wx.EXPAND | wx.ALL, border=20)

        # Кнопка для открытия окна задачи 1
        task1_button = wx.Button(panel, label="Открыть Задачу 1")
        task1_button.Bind(wx.EVT_BUTTON, self.on_open_task1)
        vbox.Add(task1_button, flag=wx.EXPAND | wx.ALL, border=10)

        # Кнопка для открытия окна задачи 2
        task2_button = wx.Button(panel, label="Открыть Задачу 2")
        task2_button.Bind(wx.EVT_BUTTON, self.on_open_task2)
        vbox.Add(task2_button, flag=wx.EXPAND | wx.ALL, border=10)

        # Кнопка для выхода
        exit_button = wx.Button(panel, label="Выход")
        exit_button.Bind(wx.EVT_BUTTON, self.on_exit)
        vbox.Add(exit_button, flag=wx.EXPAND | wx.ALL, border=10)

        # Устанавливаем компоновщик для панели
        panel.SetSizer(vbox)

        # Центрируем окно на экране
        self.Centre()
        self.Show(True)

    def on_open_task1(self, event):
        task1_window = Task1Window(self, "Задача 1")
        task1_window.Show()

    def on_open_task2(self, event):
        task2_window = Task2Window(self, "Задача 2")
        task2_window.Show()

    def on_exit(self, event):
        self.Close()

# Класс окна для задачи 1
class Task1Window(wx.Frame):
    def __init__(self, parent, title):
        super(Task1Window, self).__init__(parent, title=title, size=(300, 200))

        # Создаем панель
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        # Добавляем текст
        label = wx.StaticText(panel, label="Это окно для выполнения Задачи 1", style=wx.ALIGN_CENTER)
        vbox.Add(label, flag=wx.EXPAND | wx.ALL, border=20)

        # Кнопка для выполнения задачи
        action_button = wx.Button(panel, label="Выполнить задачу 1")
        action_button.Bind(wx.EVT_BUTTON, self.on_action)
        vbox.Add(action_button, flag=wx.EXPAND | wx.ALL, border=10)

        # Устанавливаем компоновщик
        panel.SetSizer(vbox)

        # Центрируем окно
        self.Centre()

    def on_action(self, event):
        wx.MessageBox("Задача 1 выполнена!", "Сообщение", wx.OK | wx.ICON_INFORMATION)

# Класс окна для задачи 2
class Task2Window(wx.Frame):
    def __init__(self, parent, title):
        super(Task2Window, self).__init__(parent, title=title, size=(300, 200))

        # Создаем панель
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        # Добавляем текст
        label = wx.StaticText(panel, label="Это окно для выполнения Задачи 2", style=wx.ALIGN_CENTER)
        vbox.Add(label, flag=wx.EXPAND | wx.ALL, border=20)

        # Поле ввода
        self.input_field = wx.TextCtrl(panel)
        vbox.Add(self.input_field, flag=wx.EXPAND | wx.ALL, border=10)

        # Кнопка для обработки ввода
        process_button = wx.Button(panel, label="Обработать ввод")
        process_button.Bind(wx.EVT_BUTTON, self.on_process)
        vbox.Add(process_button, flag=wx.EXPAND | wx.ALL, border=10)

        # Устанавливаем компоновщик
        panel.SetSizer(vbox)

        # Центрируем окно
        self.Centre()

    def on_process(self, event):
        user_input = self.input_field.GetValue()
        if user_input:
            wx.MessageBox(f"Вы ввели: {user_input}", "Результат", wx.OK | wx.ICON_INFORMATION)
        else:
            wx.MessageBox("Пожалуйста, введите данные!", "Ошибка", wx.OK | wx.ICON_ERROR)

# Запуск приложения
if __name__ == "__main__":
    app = wx.App(False)
    MainWindow(None, "Главное окно")
    app.MainLoop()


### Объяснение кода:

# 1. **Главное окно (`MainWindow`)**:
#    - Создается как класс, наследующий `wx.Frame`.
#    - В нем размещаются кнопки для открытия дополнительных окон и выхода из приложения.
#    - Используется `wx.BoxSizer` для компоновки элементов интерфейса (аналог `pack` или `grid` в Tkinter).

# 2. **Дополнительные окна (`Task1Window` и `Task2Window`)**:
#    - Каждое окно также создается как класс, наследующий `wx.Frame`.
#    - В окне для задачи 1 есть кнопка, которая показывает сообщение.
#    - В окне для задачи 2 есть поле ввода (`wx.TextCtrl`) и кнопка для обработки введенных данных.

# 3. **Обработка событий**:
#    - События (например, нажатие кнопок) обрабатываются с помощью метода `Bind`, который связывает событие
# (например, `wx.EVT_BUTTON`) с функцией-обработчиком.

# 4. **Диалоговые окна**:
#    - Для отображения сообщений используется `wx.MessageBox`, аналог `messagebox` в Tkinter.

# 5. **Запуск приложения**:
#    - Приложение запускается с помощью `wx.App` и метода `MainLoop`, что является стандартным для wxPython.

# ### Преимущества wxPython:
# - Более современный и нативный внешний вид по сравнению с Tkinter.
# - Богатый набор виджетов и возможностей для создания сложных интерфейсов.
# - Кроссплатформенность (работает на Windows, macOS, Linux).

# ### Ограничения wxPython:
# - Требует установки (в отличие от Tkinter, который встроен в Python).
# - Более сложный синтаксис и кривая обучения по сравнению с Tkinter.
# - Размер итогового приложения может быть больше из-за зависимостей.

# ### Рекомендация:
# Если вам нужен современный интерфейс и вы готовы потратить немного времени на изучение wxPython, это отличный выбор.
# Если же вы хотите что-то еще более мощное и современное, рассмотрите PyQt или PySide.
