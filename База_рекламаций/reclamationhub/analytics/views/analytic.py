# analytics\views\analytic.py
"""Представление для основной страницы аналитики"""

from datetime import date
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from reclamations.models import Reclamation


# Декоратор @login_required проверяет - залогинен ли пользователь:
# если да → пускает на страницу, если нет → перенаправляет на страницу входа
# Настройка авторизации (settings.py):
# LOGIN_URL = "/admin/login/"  # Куда перенаправлять неавторизованных


# # @login_required
def analytic_page(request):
    # Получаем выбранный год (по умолчанию текущий)
    selected_year = int(request.GET.get("year", date.today().year))

    # Получаем данные для карточек ЗА ВЫБРАННЫЙ ГОД
    total_reclamations = Reclamation.objects.filter(year=selected_year).count()
    new_reclamations = Reclamation.objects.filter(
        year=selected_year, status="new"
    ).count()
    in_progress = Reclamation.objects.filter(
        year=selected_year, status="in_progress"
    ).count()
    closed_reclamations = Reclamation.objects.filter(
        year=selected_year, status="closed"
    ).count()

    context = {
        "page_title": "Аналитика",
        "description": "Генерация аналитических материалов по дефектности изделий и претензиям",
        # Данные для карточек
        "total_reclamations": total_reclamations,
        "new_reclamations": new_reclamations,
        "in_progress": in_progress,
        "closed_reclamations": closed_reclamations,
    }
    return render(request, "analytics/analytic.html", context)
