# project_docs/generators/analyzers.py
"""Анализаторы структуры Django-проекта."""

from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from django.apps import apps
from django.conf import settings

from .parsers import FileParser


@dataclass
class FileNode:
    """Узел дерева файлов."""

    name: str
    path: Path
    is_dir: bool
    description: str = ""
    children: List["FileNode"] = field(default_factory=list)
    node_type: str = ""  # 'app', 'templates', 'static', 'modules', ''


@dataclass
class AppInfo:
    """Информация о Django-приложении."""

    name: str
    verbose_name: str
    path: Path
    models: List[Dict[str, str]]
    description: str = ""


class ProjectAnalyzer:
    """Анализатор структуры Django-проекта."""

    IGNORE_DIRS = {
        "__pycache__",
        "migrations",
        "venv",
        "env",
        "staticfiles",  # collectstatic
        "media",  # загруженные пользователями файлы
        "logs",  # логи
        "node_modules",
        "htmlcov",
        "dist",
        "build",
        ".vscode",  # настройки редактора
        ".venv",
        ".git",
        ".idea",
        ".pytest_cache",
        ".tox",
        ".mypy_cache",
        ".coverage",  # отчёты покрытия
    }

    IGNORE_FILES = {".pyc", ".pyo", ".DS_Store"}

    def __init__(self):
        self.parser = FileParser()
        self.base_dir = Path(settings.BASE_DIR)

    def get_django_apps(self) -> List[AppInfo]:
        """Получает информацию о Django-приложениях проекта."""
        project_apps = []

        for app_config in apps.get_app_configs():
            # Пропускаем стандартные Django и сторонние приложения
            app_path = Path(app_config.path)

            if not self._is_project_app(app_path):
                continue

            # Получаем модели
            models = []
            for model in app_config.get_models():
                doc = model.__doc__ or ""
                if doc:
                    doc = doc.strip().split("\n")[0]
                models.append({"name": model.__name__, "docstring": doc})

            # Получаем описание приложения
            description = ""
            apps_file = app_path / "apps.py"
            if apps_file.exists():
                description = self.parser.get_description(apps_file)

            if not description:
                description = app_config.verbose_name

            project_apps.append(
                AppInfo(
                    name=app_config.name,
                    verbose_name=app_config.verbose_name,
                    path=app_path,
                    models=models,
                    description=description,
                )
            )

        return sorted(project_apps, key=lambda x: x.name)

    def _is_project_app(self, app_path: Path) -> bool:
        """Проверяет, является ли приложение частью проекта."""
        try:
            app_path.relative_to(self.base_dir)
            return True
        except ValueError:
            return False

    def build_file_tree(self, root: Optional[Path] = None) -> FileNode:
        """Строит дерево файлов проекта."""
        if root is None:
            root = self.base_dir

        return self._build_tree_recursive(root)

    def _build_tree_recursive(self, path: Path, level: int = 0) -> FileNode:
        """Рекурсивно строит дерево."""
        node = FileNode(name=path.name, path=path, is_dir=path.is_dir())

        if not path.is_dir():
            node.description = self.parser.get_description(path)
            return node

        # Определяем тип директории
        node.node_type = self._get_dir_type(path)

        # Ограничиваем глубину
        if level > 15:
            return node

        # Получаем содержимое
        try:
            entries = sorted(
                path.iterdir(), key=lambda e: (e.is_file(), e.name.lower())
            )
        except PermissionError:
            return node

        # Фильтруем
        entries = [
            e
            for e in entries
            if e.name not in self.IGNORE_DIRS
            and e.suffix not in self.IGNORE_FILES
            and not (e.name.startswith(".") and e.is_dir())
        ]

        for entry in entries:
            child = self._build_tree_recursive(entry, level + 1)
            node.children.append(child)

        return node

    def _get_dir_type(self, path: Path) -> str:
        """Определяет тип директории."""
        # Django-приложение
        if (path / "apps.py").exists():
            return "app"

        # Специальные папки
        name = path.name.lower()
        if name == "templates":
            return "templates"
        if name in ("static", "assets"):
            return "static"
        if name == "modules":
            return "modules"
        if name in ("management", "commands"):
            return "management"
        if name == "views":
            return "views"
        if name in ("tests", "test"):
            return "tests"

        return ""

    def analyze_modules_dir(self, modules_path: Path) -> List[Dict[str, str]]:
        """
        Анализирует директорию modules/ и views/ — извлекает docstring модулей.
        Рекурсивно обходит вложенные папки.

        Returns:
            Список {'file': str, 'docstring': str}
        """
        results = []

        if not modules_path.exists():
            return results

        # for py_file in modules_path.glob("*.py"):
        #     if py_file.name == "__init__.py":
        #         continue

        #     # description = self.parser.get_description(py_file)
        #     description = self.parser.get_full_description(py_file)
        #     results.append({"file": py_file.name, "docstring": description})

        # rglob — рекурсивный поиск
        for py_file in modules_path.rglob("*.py"):
            if py_file.name == "__init__.py":
                continue

            # Относительный путь от modules/
            try:
                relative_path = py_file.relative_to(modules_path)
            except ValueError:
                relative_path = py_file.name

            description = self.parser.get_full_description(py_file)
            results.append({"file": str(relative_path), "docstring": description})

        # return sorted(results, key=lambda x: x["file"])
        return results

    def analyze_templates_dir(self, templates_path: Path) -> List[Dict[str, str]]:
        """
        Анализирует директорию templates/ — извлекает описания из HTML.

        Returns:
            Список {'file': str, 'docstring': str}
        """
        results = []

        if not templates_path.exists():
            return results

        # Ищем HTML-файлы рекурсивно (учитываем вложенные папки)
        for html_file in templates_path.rglob("*.html"):
            description = self.parser.get_description(html_file)

            # Получаем относительный путь от templates/
            try:
                relative_path = html_file.relative_to(templates_path)
            except ValueError:
                relative_path = html_file.name

            results.append({"file": str(relative_path), "docstring": description})

        # return sorted(results, key=lambda x: x["file"])
        return results

    # def analyze_views_dir(self, views_path: Path) -> List[Dict[str, str]]:
    #     """
    #     Анализирует директорию views/ — извлекает docstring модулей.

    #     Returns:
    #         Список {'file': str, 'docstring': str}
    #     """
    #     results = []

    #     if not views_path.exists():
    #         return results

    #     for py_file in views_path.glob("*.py"):
    #         if py_file.name == "__init__.py":
    #             continue

    #         description = self.parser.get_description(py_file)
    #         results.append({"file": py_file.name, "docstring": description})

    #     return sorted(results, key=lambda x: x["file"])

    # def analyze_views_dir(self, views_path: Path) -> List[Dict[str, str]]:
    #     """
    #     Анализирует директорию views/ — извлекает классы и функции.

    #     Returns:
    #         Список {'file': str, 'class': str, 'docstring': str}
    #     """
    #     results = []

    #     if not views_path.exists():
    #         return results

    #     for py_file in views_path.glob("*.py"):
    #         if py_file.name == "__init__.py":
    #             continue

    #         # Сначала пробуем получить классы
    #         classes = self.parser.get_classes(py_file)

    #         if classes:
    #             for cls in classes:
    #                 results.append(
    #                     {
    #                         "file": py_file.name,
    #                         "class": cls["name"],
    #                         "docstring": cls["docstring"],
    #                     }
    #                 )
    #         else:
    #             # Если классов нет, берём docstring модуля
    #             description = self.parser.get_description(py_file)
    #             results.append(
    #                 {"file": py_file.name, "class": "", "docstring": description}
    #             )

    #     return sorted(results, key=lambda x: x["file"])
