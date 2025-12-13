# project_docs/generators/parsers.py
"""
Парсеры для извлечения описаний из файлов разных типов.
Поддерживает: Python, HTML, JavaScript, CSS.
"""

import ast
import re
from pathlib import Path
from typing import Optional


class FileParser:
    """Универсальный парсер для извлечения описаний из файлов."""

    # Стандартные описания для известных Django-файлов
    STANDARD_DESCRIPTIONS = {
        "models.py": "Модели данных (ORM)",
        "views.py": "Представления (контроллеры)",
        "urls.py": "Маршрутизация URL",
        "admin.py": "Настройка админ-панели",
        "apps.py": "Конфигурация приложения",
        "forms.py": "Формы Django",
        "serializers.py": "Сериализаторы DRF",
        "tests.py": "Тесты",
        "signals.py": "Сигналы Django",
        "tasks.py": "Celery-задачи",
        "manage.py": "CLI Django",
        "settings.py": "Настройки проекта",
        "wsgi.py": "WSGI-конфигурация",
        "asgi.py": "ASGI-конфигурация",
        "conftest.py": "Pytest-фикстуры",
        "__init__.py": "",
    }

    def get_description(self, filepath: Path) -> str:
        """
        Извлекает описание из файла.

        Args:
            filepath: Путь к файлу

        Returns:
            Строка с описанием или пустая строка
        """
        # Проверяем стандартные описания
        if filepath.name in self.STANDARD_DESCRIPTIONS:
            standard = self.STANDARD_DESCRIPTIONS[filepath.name]
            if standard:
                return standard

        # Выбираем парсер по расширению
        suffix = filepath.suffix.lower()

        # Для Python читаем весь файл (иначе ast.parse ломается)
        if suffix == ".py":
            content = self._read_file_full(filepath)
        else:  # Для остальных — только начало
            content = self._read_file_start(filepath)

        if not content:
            return ""

        # Выбираем парсер по расширению
        parsers = {
            ".py": self._parse_python,
            ".html": self._parse_html,
            ".htm": self._parse_html,
            ".js": self._parse_javascript,
            ".ts": self._parse_javascript,
            ".css": self._parse_css,
            ".scss": self._parse_css,
            ".sass": self._parse_css,
            ".less": self._parse_css,
        }

        parser = parsers.get(suffix)
        if parser:
            return parser(content)

        return ""

    def _read_file_start(self, filepath: Path, size: int = 1024) -> str:
        """Читает начало файла."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read(size)
        except (UnicodeDecodeError, FileNotFoundError, PermissionError):
            return ""

    def _read_file_full(self, filepath: Path) -> str:
        """Читает весь файл."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read()
        except (UnicodeDecodeError, FileNotFoundError, PermissionError):
            return ""

    def _parse_python(self, content: str) -> str:
        """Извлекает docstring модуля из Python-файла."""
        try:
            tree = ast.parse(content)
            docstring = ast.get_docstring(tree)
            if docstring:
                return docstring.split("\n")[0].strip()
        except SyntaxError:
            pass
        return ""

    def get_full_description(self, filepath: Path) -> str:
        """
        Извлекает полный docstring из Python-файла.
        Для не-Python файлов возвращает обычное описание.
        """
        if filepath.suffix.lower() != ".py":
            return self.get_description(filepath)

        content = self._read_file_full(filepath)
        if not content:
            return ""

        try:
            tree = ast.parse(content)
            docstring = ast.get_docstring(tree)
            return docstring.strip() if docstring else ""
        except SyntaxError:
            return ""

    def _parse_html(self, content: str) -> str:
        """
        Извлекает комментарий из HTML/Django-шаблона.
        Поддерживает: {# #}, <!-- -->, {% comment %}
        """
        patterns = [
            r"\{#\s*(.+?)\s*#\}",
            r"\{% comment %\}\s*(.+?)\s*\{% endcomment %\}",
            r"<!--\s*(.+?)\s*-->",
        ]

        for pattern in patterns:
            match = re.search(pattern, content, re.DOTALL)
            if match:
                comment = match.group(1).strip()
                first_line = comment.split("\n")[0].strip()
                first_line = re.sub(r"^[\s\-\*#]+", "", first_line)
                if first_line and len(first_line) > 3:
                    return first_line

        return ""

    def _parse_javascript(self, content: str) -> str:
        """
        Извлекает комментарий из JavaScript/TypeScript.
        Поддерживает: /** */, /* */, //
        """
        patterns = [
            r"/\*\*\s*\n?\s*\*?\s*(.+?)(?:\n|\*)",
            r"/\*\s*(.+?)\s*\*/",
            r"^//\s*(.+?)$",
        ]

        for pattern in patterns:
            match = re.search(pattern, content, re.MULTILINE)
            if match:
                comment = match.group(1).strip()
                if not comment.startswith("@"):
                    return comment[:100]

        return ""

    def _parse_css(self, content: str) -> str:
        """Извлекает комментарий из CSS/SCSS."""
        patterns = [
            r"/\*\s*\*?\s*(.+?)\s*\*/",
            r"^//\s*(.+?)$",
        ]

        for pattern in patterns:
            match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
            if match:
                comment = match.group(1).strip()
                first_line = comment.split("\n")[0].strip()
                first_line = re.sub(r"^[\s\*]+", "", first_line)
                if first_line:
                    return first_line

        return ""
