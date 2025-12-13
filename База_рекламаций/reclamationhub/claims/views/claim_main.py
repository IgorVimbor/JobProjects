# claims\views\claim_main.py
"""Представление для основной страницы аналитики претензий"""

from datetime import date
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from reclamations.models import Reclamation
from claims.models import Claim


# Декоратор @login_required проверяет - залогинен ли пользователь:
# если да → пускает на страницу, если нет → перенаправляет на страницу входа
# Настройка авторизации (settings.py):
# LOGIN_URL = "/admin/login/"  # Куда перенаправлять неавторизованных


# @login_required
def claim_page(request):
    # Получаем доступные годы из претензий
    available_years = list(
        Claim.objects.values_list("claim_date__year", flat=True)
        .distinct()
        .order_by("-claim_date__year")
    )

    # Если нет данных - добавляем текущий год
    current_year = date.today().year
    if not available_years:
        available_years = [current_year]

    context = {
        "page_title": "Анализ претензий",
        "description": "Выбор вида анализа претензий",
        "available_years": available_years,
        "current_year": current_year,
        "current_date": date.today().strftime("%d.%m.%Y"),
    }
    return render(request, "claims/claim_main.html", context)
