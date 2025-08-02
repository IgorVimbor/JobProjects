from django.apps import AppConfig


class InvestigationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "investigations"
    # меняем отображение заголовка приложения
    verbose_name = "Акты исследования и виновник, утилизация и возврат изделий"
