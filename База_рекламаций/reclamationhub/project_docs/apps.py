# project_docs\apps.py
"""Конфигурация приложения для генерации документации проекта."""

from django.apps import AppConfig


class ProjectDocsConfig(AppConfig):
    """Приложение для генерации структуры и документации проекта."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "project_docs"
    verbose_name = "Документация проекта"
