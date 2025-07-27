from django.apps import AppConfig


class ReclamationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "reclamations"
    # меняем отображение заголовка приложения
    verbose_name = "Регистрация рекламаций и прихода изделий"
