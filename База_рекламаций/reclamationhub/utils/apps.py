from django.apps import AppConfig


class UtilsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "utils"
    verbose_name = "Утилиты"  # отображение в админке

    def ready(self):
        # Код, который выполнится при загрузке приложения
        pass
