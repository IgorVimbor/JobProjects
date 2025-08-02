from django.contrib.admin import AdminSite
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin, GroupAdmin


class CustomAdminSite(AdminSite):
    def get_app_list(self, request):
        app_list = super().get_app_list(request)
        # Сортируем приложения согласно ADMIN_APPS_ORDER в settings.py
        app_list.sort(key=lambda x: self.get_app_order(x["app_label"]))
        return app_list

    def get_app_order(self, app_label):
        from django.conf import settings

        return settings.ADMIN_APPS_ORDER.get(
            app_label, 999
        )  # 999 для неуказанных приложений


# Создаем экземпляр кастомного AdminSite
admin_site = CustomAdminSite(name="custom_admin")

# Регистрируем модели auth
admin_site.register(User, UserAdmin)
admin_site.register(Group, GroupAdmin)
