from django.apps import AppConfig


class SourcebookConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "sourcebook"
    verbose_name = "Справочники"  # меняем отображение заголовка приложения
