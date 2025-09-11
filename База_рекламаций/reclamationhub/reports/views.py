from django.shortcuts import render
from django.contrib.auth.decorators import login_required


# Декоратор @login_required проверяет - залогинен ли пользователь:
# если да → пускает на страницу, если нет → перенаправляет на страницу входа
# Настройка авторизации (settings.py):
# LOGIN_URL = "/admin/login/"  # Куда перенаправлять неавторизованных


# @login_required
def analytics_page(request):
    """Страница аналитики"""  # пока просто рендерим шаблон
    context = {
        "page_title": "Аналитика данных",
        "description": "Генерация отчетов и справок за период",
    }
    return render(request, "reports/analytics.html", context)
