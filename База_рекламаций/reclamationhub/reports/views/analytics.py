# Представление для основной страницы аналитики

from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from reclamations.models import Reclamation


# Декоратор @login_required проверяет - залогинен ли пользователь:
# если да → пускает на страницу, если нет → перенаправляет на страницу входа
# Настройка авторизации (settings.py):
# LOGIN_URL = "/admin/login/"  # Куда перенаправлять неавторизованных


# @login_required
def analytics_page(request):
    # Получаем данные для карточек, как на главной странице
    total_reclamations = Reclamation.objects.count()
    new_reclamations = Reclamation.objects.filter(status="new").count()
    in_progress = Reclamation.objects.filter(status="in_progress").count()
    closed_reclamations = Reclamation.objects.filter(status="closed").count()

    context = {
        "page_title": "Аналитика данных",
        "description": "Генерация отчетов и справок по дефектности изделий БЗА",
        # Данные для карточек
        "total_reclamations": total_reclamations,
        "new_reclamations": new_reclamations,
        "in_progress": in_progress,
        "closed_reclamations": closed_reclamations,
    }
    return render(request, "reports/analytics.html", context)
