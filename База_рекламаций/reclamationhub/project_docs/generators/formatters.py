# project_docs/generators/formatters.py
"""
Форматировщик вывода в Markdown.
"""

from datetime import datetime
from pathlib import Path
from typing import List

from .analyzers import ProjectAnalyzer, FileNode, AppInfo


class MarkdownFormatter:
    """Форматирует структуру проекта в Markdown."""

    # FILE_ICONS = {
    #     ".py": "🐍",
    #     ".html": "📄",
    #     ".htm": "📄",
    #     ".js": "📜",
    #     ".ts": "📘",
    #     ".css": "🎨",
    #     ".scss": "🎨",
    #     ".json": "📋",
    #     ".yaml": "📋",
    #     ".yml": "📋",
    #     ".md": "📝",
    #     ".txt": "📝",
    #     ".sql": "🗃️",
    # }

    # DIR_ICONS = {
    #     "app": "📦",
    #     "templates": "📄",
    #     "static": "🎨",
    #     "modules": "⚙️",
    #     "views": "👁️",
    #     "tests": "🧪",
    #     "management": "🔧",
    # }

    def __init__(self, analyzer: ProjectAnalyzer):
        self.analyzer = analyzer

    def generate(self, project_name: str = "Django Project") -> str:
        """Генерирует полную документацию в Markdown."""
        lines = []

        # Заголовок
        # lines.append(f"# 📚 Структура проекта: {project_name}")
        lines.append(f"# СТРУКТУРА ПРОЕКТА {project_name}")
        lines.append("")
        lines.append(f"*Создано: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Django-приложения
        lines.extend(self._format_apps_section())

        # Дерево файлов
        lines.extend(self._format_tree_section())

        # # Легенда
        # lines.extend(self._format_legend())

        return "\n".join(lines)

    def _format_apps_section(self) -> List[str]:
        """Форматирует раздел Django-приложений."""
        lines = []
        # lines.append("## 📦 Django-приложения")
        lines.append("## Django-приложения")
        lines.append("")

        apps = self.analyzer.get_django_apps()

        if not apps:
            lines.append("*Приложения проекта не найдены*")
            lines.append("")
            return lines

        for app in apps:
            lines.append(f"### `{app.name}`")
            lines.append("")

            # if app.description:
            #     lines.append(f"> {app.description}")
            #     lines.append("")

            # Модели
            if app.models:
                lines.append("**Модели:**")
                lines.append("")
                for model in app.models:
                    doc = model["docstring"] or "—"
                    lines.append(f"- `{model['name']}` — {doc}")
                lines.append("")

            # Модули (processors)
            modules_path = app.path / "modules"
            if modules_path.exists():
                modules = self.analyzer.analyze_modules_dir(modules_path)
                if modules:
                    lines.append("**Модули (modules):**")
                    lines.append("")
                    for mod in modules:
                        doc = mod["docstring"] or "—"
                        lines.append(f"- `{mod['file']}` — ")
                        for line in doc.split("\n"):
                            # line = line.strip()
                            if line:
                                lines.append(f"  {line}  ")  # два пробела в конце
                                # В Markdown одиночный перенос строки игнорируется. Нужно:
                                # - Два пробела в конце строки, или
                                # - Пустая строка между строками
                    lines.append("")

            # Представления (views/)
            views_path = app.path / "views"
            if views_path.exists():
                views = self.analyzer.analyze_modules_dir(views_path)
                if views:
                    lines.append("**Представления (views):**")
                    lines.append("")
                    for view in views:
                        doc = view["docstring"] or "—"
                        lines.append(f"- `{view['file']}` — {doc}")
                    lines.append("")

            # Шаблоны (templates/)
            templates_path = app.path / "templates"
            if templates_path.exists():
                templates = self.analyzer.analyze_templates_dir(templates_path)
                if templates:
                    lines.append("**Шаблоны (templates):**")
                    lines.append("")
                    for tpl in templates:
                        doc = tpl["docstring"] or "—"
                        lines.append(f"- `{tpl['file']}` — {doc}")
                    lines.append("")

            # Пользовательские теги (templatetags)
            tags_path = app.path / "templatetags"
            if tags_path.exists():
                modules = self.analyzer.analyze_modules_dir(tags_path)
                if modules:
                    lines.append("**Пользовательские теги (templatetags):**")
                    lines.append("")
                    for mod in modules:
                        doc = mod["docstring"] or "—"
                        lines.append(f"- `{mod['file']}` — ")
                        for line in doc.split("\n"):
                            # line = line.strip()
                            if line:
                                lines.append(f"  {line}  ")  # два пробела в конце
                                # В Markdown одиночный перенос строки игнорируется. Нужно:
                                # - Два пробела в конце строки, или
                                # - Пустая строка между строками
                    lines.append("")

            lines.append("---")
            lines.append("")

        return lines

    def _format_tree_section(self) -> List[str]:
        """Форматирует раздел с деревом файлов."""
        lines = []
        # lines.append("## 🌳 Дерево файлов")
        lines.append("## ДЕРЕВО ФАЙЛОВ")
        lines.append("")
        lines.append("```")

        tree = self.analyzer.build_file_tree()
        lines.append(f"{tree.name}/")
        lines.extend(self._render_tree(tree, ""))

        lines.append("```")
        lines.append("")

        return lines

    def _render_tree(self, node: FileNode, prefix: str, level: int = 0) -> List[str]:
        """Рекурсивно рендерит дерево."""
        lines = []

        children = node.children
        for i, child in enumerate(children):
            is_last = i == len(children) - 1
            connector = "└── " if is_last else "├── "
            extension = "    " if is_last else "│   "

            if child.is_dir:
                # icon = self.DIR_ICONS.get(child.node_type, "📁")
                type_label = self._get_dir_label(child.node_type)
                # label = f"  # {icon} {type_label}" if type_label else ""
                label = f"  # {type_label}" if type_label else ""
                lines.append(f"{prefix}{connector}{child.name}/{label}")
                lines.extend(self._render_tree(child, prefix + extension, level + 1))

                # Добавляем пустую строку после директорий на корневом уровне
                if level == 0 and not is_last:
                    lines.append(f"{prefix}│")
            else:
                # icon = self.FILE_ICONS.get(child.path.suffix.lower(), "📄")
                desc = f"  # {child.description}" if child.description else ""
                # lines.append(f"{prefix}{connector}{icon} {child.name}{desc}")
                lines.append(f"{prefix}{connector} {child.name}{desc}")

        return lines

    def _get_dir_label(self, node_type: str) -> str:
        """Возвращает метку для типа директории."""
        labels = {
            "app": "Django App",
            "templates": "Шаблоны",
            "templatetags": "Пользовательские теги",
            "static": "Статика",
            "modules": "Процессоры",
            "views": "Представления",
            "tests": "Тесты",
            "management": "Команды",
        }
        return labels.get(node_type, "")

    # def _format_legend(self) -> List[str]:
    #     """Форматирует легенду."""
    #     lines = []
    #     lines.append("## 📖 Легенда")
    #     lines.append("")
    #     lines.append("| Иконка | Тип |")
    #     lines.append("|--------|-----|")
    #     lines.append("| 📦 | Django-приложение |")
    #     lines.append("| 📄 | Шаблоны |")
    #     lines.append("| 🎨 | Стили/Статика |")
    #     lines.append("| 📜 | JavaScript |")
    #     lines.append("| 🐍 | Python |")
    #     lines.append("| ⚙️ | Процессоры/Модули |")
    #     lines.append("")

    #     return lines
