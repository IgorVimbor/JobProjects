# investigations/storages.py

# Файл для переопределения стандартного класса Storage.
# Кастомный класс Storage нужен, чтобы изменить поведение по умолчанию Django,
# когда при сохранении файлов с одинаковым именем добавляется рандомный суффикс.
# Акты исследования могут быть оформлены на несколько рекламаций. Без переопределения Storage
# Django сохраняет файлы с суффиксом: 2025__1009_ММЗ_ТН_0080279.pdf и 2025__1009_ММЗ_ТН_0080279_9Vb3S5K.pdf


import os
from django.core.files.storage import FileSystemStorage
from django.conf import settings


class NoDuplicateFileStorage(FileSystemStorage):
    """Класс Storage который не создает дубликаты файлов"""

    def get_available_name(self, name, max_length=None):
        """
        Переопределяем метод, который добавляет суффиксы.
        Если файл существует - возвращаем существующий путь.
        """
        if self.exists(name):
            # Файл уже существует - возвращаем существующий путь
            if settings.DEBUG:
                print(f"Файл {name} уже существует, используем существующий")
            return name

        # Файла нет - возвращаем оригинальное имя для создания нового
        if settings.DEBUG:
            print(f"Создаем новый файл {name}")
        return name

    def _save(self, name, content):
        """
        Переопределяем сохранение.
        Если файл уже существует - не сохраняем контент.
        """
        if self.exists(name):
            # Файл уже существует - не сохраняем, просто возвращаем имя
            if settings.DEBUG:
                print(f"Файл {name} уже существует, пропускаем сохранение")
            return name

        # Файла нет - сохраняем как обычно
        return super()._save(name, content)
