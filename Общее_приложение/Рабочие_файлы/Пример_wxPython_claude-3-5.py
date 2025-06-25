# Вот пример аналогичного приложения на wxPython:

import wx

class TaskWindow(wx.Frame):
    def __init__(self, title):
        super().__init__(parent=None, title=title, size=(300, 200))
        panel = wx.Panel(self)

        # Создаем текст для окна задачи
        text = wx.StaticText(panel, label=f"Это окно {title}", pos=(20, 20))

        # Центрируем окно на экране
        self.Center()

class MainWindow(wx.Frame):
    def __init__(self):
        super().__init__(parent=None, title='Главное окно', size=(400, 300))

        # Создаем главную панель
        panel = wx.Panel(self)

        # Создаем вертикальный бокссайзер для размещения кнопок
        vbox = wx.BoxSizer(wx.VERTICAL)

        # Создаем кнопки
        btn1 = wx.Button(panel, label='Задача 1')
        btn2 = wx.Button(panel, label='Задача 2')
        btn3 = wx.Button(panel, label='Задача 3')

        # Привязываем обработчики событий к кнопкам
        btn1.Bind(wx.EVT_BUTTON, lambda evt: self.open_task("Задача 1"))
        btn2.Bind(wx.EVT_BUTTON, lambda evt: self.open_task("Задача 2"))
        btn3.Bind(wx.EVT_BUTTON, lambda evt: self.open_task("Задача 3"))

        # Добавляем кнопки в бокссайзер с отступами
        vbox.Add(btn1, 0, wx.ALL | wx.CENTER, 10)
        vbox.Add(btn2, 0, wx.ALL | wx.CENTER, 10)
        vbox.Add(btn3, 0, wx.ALL | wx.CENTER, 10)

        # Устанавливаем сайзер для панели
        panel.SetSizer(vbox)

        # Центрируем главное окно на экране
        self.Center()

        # Создаем строку состояния
        self.CreateStatusBar()
        self.SetStatusText("Готово")

    def open_task(self, title):
        task_window = TaskWindow(title)
        task_window.Show()

if __name__ == '__main__':
    app = wx.App()
    frame = MainWindow()
    frame.Show()
    app.MainLoop()


# Основные отличия от версии на Tkinter:

# 1. Более нативный внешний вид интерфейса для каждой операционной системы
# 2. Использование системы сайзеров (BoxSizer) для более гибкого управления расположением элементов
# 3. Отдельные классы для окон (Frame) вместо Toplevel
# 4. Встроенная строка состояния
# 5. Более удобная система обработки событий
# 6. Автоматическое центрирование окон

# Дополнительные возможности wxPython, которые можно добавить:

# 1. Меню и панели инструментов
# # Добавление меню
# menubar = wx.MenuBar()
# file_menu = wx.Menu()
# file_menu.Append(wx.ID_EXIT, 'Выход')
# menubar.Append(file_menu, 'Файл')
# self.SetMenuBar(menubar)

# 2. Иконки для кнопок
# btn = wx.Button(panel, label='Задача 1', bitmap=wx.Bitmap('icon.png'))

# 3. Диалоговые окна
# wx.MessageBox('Сообщение', 'Заголовок', wx.OK | wx.ICON_INFORMATION)

# 4. Гридсайзер для более сложных layouts
# grid = wx.GridSizer(rows=2, cols=2, vgap=5, hgap=5)
