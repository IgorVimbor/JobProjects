from django.apps import AppConfig


class ReportsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "reports"
    # меняем отображение заголовка приложения
    verbose_name = "Аналитика и отчеты"
