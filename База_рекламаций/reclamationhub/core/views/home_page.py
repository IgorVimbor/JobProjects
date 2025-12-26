# reclamationhub\core\views.py

"""Представление для главной страницы сайта с данными текущего года."""

from django.shortcuts import render
from django.db.models import Count, Q
from django.db.models.functions import TruncMonth
from django.http import JsonResponse
from datetime import datetime, timedelta
import json

from reclamations.models import Reclamation
from investigations.models import Investigation


def home_view(request):
    """Главная страница с данными текущего года по умолчанию"""
    current_year = datetime.now().year
    selected_year = request.GET.get("year", current_year)

    try:
        selected_year = int(selected_year)
    except (ValueError, TypeError):
        selected_year = current_year

    # Получаем доступные годы для селектора
    available_years = list(
        Reclamation.objects.values_list("year", flat=True).distinct().order_by("-year")
    )

    # Фильтруем данные по выбранному году
    year_filter = Q(year=selected_year)

    # Последние 5 рекламаций выбранного года
    latest_reclamations = (
        Reclamation.objects.select_related("product", "product_name")
        .filter(year_filter)
        .order_by("-yearly_number")[:5]
    )

    # Общее количество рекламаций за год
    total_reclamations = Reclamation.objects.filter(year_filter).count()

    # Статистика по статусам за год
    status_data = (
        Reclamation.objects.filter(year_filter)
        .values("status")
        .annotate(count=Count("id"))
        .order_by("-count")
    )

    # Статистика по изделиям за год
    products_data = (
        Reclamation.objects.filter(year_filter)
        .values("product_name__name")
        .annotate(count=Count("id"))
        .order_by("-count")
    )

    # Статистика по месяцам выбранного года
    monthly_data = list(
        Reclamation.objects.filter(year_filter)
        .annotate(month=TruncMonth("message_received_date"))
        .values("month")
        .annotate(count=Count("id"))
        .order_by("month")
    )

    # Преобразуем даты в строки
    for item in monthly_data:
        if item["month"]:
            item["month"] = item["month"].strftime("%Y-%m-%d")

    context = {
        "current_section": None,
        "selected_year": selected_year,
        "available_years": json.dumps(available_years),
        "latest_reclamations": latest_reclamations,
        "total_reclamations": total_reclamations,
        "status_data": json.dumps(list(status_data)),
        "products_data": json.dumps(list(products_data)),
        "monthly_data": json.dumps(monthly_data),
        "new_reclamations": Reclamation.objects.filter(
            year_filter, status=Reclamation.Status.NEW
        ).count(),
        "in_progress": Reclamation.objects.filter(
            year_filter, status=Reclamation.Status.IN_PROGRESS
        ).count(),
        "closed_reclamations": Reclamation.objects.filter(
            year_filter, status=Reclamation.Status.CLOSED
        ).count(),
    }

    return render(request, "home.html", context)


def ajax_year_data(request):
    """AJAX endpoint для получения данных по выбранному году"""
    year = request.GET.get("year")
    if not year:
        return JsonResponse({"error": "Не введен год"}, status=400)

    try:
        year = int(year)
    except ValueError:
        return JsonResponse({"error": "Выбранный год отсутствует"}, status=400)

    # Фильтр по году
    year_filter = Q(year=year)

    # Получаем данные
    latest_reclamations = list(
        Reclamation.objects.select_related("product", "product_name")
        .filter(year_filter)
        .order_by("-yearly_number")[:5]
        .values(
            "id",
            "product_name__name",
            "product__nomenclature",
            "defect_period__name",
            "claimed_defect",
            "products_count",
        )
    )

    # Статистика для карточек
    total_reclamations = Reclamation.objects.filter(year_filter).count()
    new_reclamations = Reclamation.objects.filter(
        year_filter, status=Reclamation.Status.NEW
    ).count()
    in_progress = Reclamation.objects.filter(
        year_filter, status=Reclamation.Status.IN_PROGRESS
    ).count()
    closed_reclamations = Reclamation.objects.filter(
        year_filter, status=Reclamation.Status.CLOSED
    ).count()

    # Данные для графиков
    products_data = list(
        Reclamation.objects.filter(year_filter)
        .values("product_name__name")
        .annotate(count=Count("id"))
        .order_by("-count")
    )

    monthly_data = list(
        Reclamation.objects.filter(year_filter)
        .annotate(month=TruncMonth("message_received_date"))
        .values("month")
        .annotate(count=Count("id"))
        .order_by("month")
    )

    # Преобразуем даты в строки
    for item in monthly_data:
        if item["month"]:
            item["month"] = item["month"].strftime("%Y-%m-%d")

    return JsonResponse(
        {
            "latest_reclamations": latest_reclamations,
            "total_reclamations": total_reclamations,
            "new_reclamations": new_reclamations,
            "in_progress": in_progress,
            "closed_reclamations": closed_reclamations,
            "products_data": products_data,
            "monthly_data": monthly_data,
        }
    )
