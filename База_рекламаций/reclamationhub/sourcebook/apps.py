from django.apps import AppConfig


class SourcebookConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "sourcebook"
    # меняем отображение заголовка приложения на вкладке браузера (title)
    verbose_name = "Справочники"
