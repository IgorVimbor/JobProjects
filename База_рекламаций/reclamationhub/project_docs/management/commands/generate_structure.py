# project_docs/management/commands/generate_structure.py
"""
Management command для генерации документации проекта.

Использование:
    python manage.py generate_structure
    python manage.py generate_structure --output DOCS.md
    python manage.py generate_structure --name "Мой проект"
"""

from pathlib import Path

from django.core.management.base import BaseCommand
from django.conf import settings

from project_docs.generators import ProjectAnalyzer, MarkdownFormatter


class Command(BaseCommand):
    help = "Генерирует документацию структуры проекта в Markdown"

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            "-o",
            type=str,
            default="PROJECT_STRUCTURE.md",
            help="Имя выходного файла (по умолчанию: PROJECT_STRUCTURE.md)",
        )
        parser.add_argument(
            "--name",
            "-n",
            type=str,
            default=None,
            help="Название проекта для заголовка",
        )

    def handle(self, *args, **options):
        # Определяем название проекта
        project_name = options["name"]
        if not project_name:
            project_name = Path(settings.BASE_DIR).name

        self.stdout.write(f"✅ Генерация документации для: {project_name}")

        # Создаём анализатор и форматировщик
        analyzer = ProjectAnalyzer()
        formatter = MarkdownFormatter(analyzer)

        # Генерируем документацию
        content = formatter.generate(project_name)

        # Сохраняем
        output_path = Path(settings.BASE_DIR) / options["output"]
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

        self.stdout.write(
            self.style.SUCCESS(f"✅ Документация сохранена: {output_path}")
        )
        self.stdout.write(f"✅ Размер: {output_path.stat().st_size:,} байт")
