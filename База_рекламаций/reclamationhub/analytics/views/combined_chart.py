"""Представления для модуля анализа по датам изготовления изделия и уведомления о дефектах"""

from datetime import datetime
from django.shortcuts import redirect, render
from django.contrib import messages

from analytics.modules.combined_chart_modul import DefectDateReportManager
from reclamations.models import Reclamation


# def combined_chart_page(request):
#     """Заглушка для модуля 'Совмещенная диаграмма'"""
#     context = {
#         "page_title": "Совмещенная диаграмма",
#         "module_name": "Combined Chart",
#         "description": "Диаграмма по пробегу (наработке) в эксплуатации по виду изделия и потребителю",
#         "status": "В разработке...",
#     }
#     return render(request, "analytics/combined_chart.html", context)


def combined_chart_page(request):
    """Страница модуля 'Диаграммы по дате уведомления, дате изготовления и совмещенная'"""

    if request.method == "POST":
        return generate_combined_report(request)

    # GET запрос - показываем актуальную информацию
    download_info = request.session.get("combined_chart_info", None)
    if download_info:
        del request.session["combined_chart_info"]

    # Получаем доступные годы для селектора
    available_years = ["all"] + list(
        Reclamation.objects.values_list("year", flat=True).distinct().order_by("-year")
    )

    # Получаем всех потребителей из модели PeriodDefect
    available_consumers_raw = (
        Reclamation.objects.select_related("defect_period")
        .values_list("defect_period__name", flat=True)
        .distinct()
        .order_by("defect_period__name")
    )

    available_consumers = [
        {"value": consumer, "name": consumer}
        for consumer in available_consumers_raw
        if consumer
    ]

    # Получаем список изделий из модели ProductType
    available_products_raw = (
        Reclamation.objects.select_related("product_name")
        .values_list("product_name__name", flat=True)
        .distinct()
        .order_by("product_name__name")
    )

    available_products = [
        {"value": product, "name": product}
        for product in available_products_raw
        if product
    ]

    context = {
        "page_title": "Диаграммы по датам",
        "description": "Диаграммы по дате уведомления о дефекте, изготовления изделия или совмещенная диаграмма",
        "download_info": download_info,
        "available_years": available_years,
        "current_year": datetime.now().year,
        "available_consumers": available_consumers,
        "available_products": available_products,
    }
    return render(request, "analytics/combined_chart.html", context)


def generate_combined_report(request):
    """Генерация отчета по датам"""

    # Получаем данные из POST
    year = request.POST.get("year")  # Год данных или "all"
    chart_type = request.POST.get("chart_type", "all")  # Тип графика

    # Получаем выбранных потребителей и изделие
    selected_consumers = request.POST.getlist("consumers")
    selected_product = request.POST.get("product")

    # Валидация года
    try:
        if year == "all":
            year_value = "all"
        else:
            year_value = int(year) if year else datetime.now().year
    except (ValueError, TypeError):
        messages.error(request, "Некорректный год")
        return redirect("analytics:combined_chart")

    # Проверка года (если не "all")
    if year_value != "all":
        current_year = datetime.now().year
        if year_value > current_year:
            messages.error(
                request, f"Нельзя формировать отчет за будущий {year_value} год"
            )
            return redirect("analytics:combined_chart")

    # Валидация типа графика
    valid_chart_types = ["product", "manufacture", "message", "combined", "all"]
    if chart_type not in valid_chart_types:
        messages.error(request, "Некорректный тип графика")
        return redirect("analytics:combined_chart")

    # Проверка наличия изделия - обязательно должно быть выбрано
    if not selected_product:
        messages.warning(request, "⚠️ Выберите изделие для анализа")
        return redirect("analytics:combined_chart")

    # Валидация изделия
    valid_products = list(
        Reclamation.objects.values_list("product_name__name", flat=True).distinct()
    )

    if selected_product not in valid_products:
        messages.error(request, "Выбрано некорректное изделие")
        return redirect("analytics:combined_chart")

    # Валидация потребителей
    consumers = []
    if selected_consumers:
        valid_consumers = list(
            Reclamation.objects.values_list("defect_period__name", flat=True).distinct()
        )
        consumers = [c for c in selected_consumers if c in valid_consumers]

    # Генерируем анализ
    manager = DefectDateReportManager(
        year=year_value, consumers=consumers, product=selected_product
    )
    result = manager.generate_report(chart_type=chart_type)

    if result["success"]:
        messages.success(request, f"✅ {result['message']}")

        # Формируем данные для session
        session_data = {
            "message": result["full_message"],
            "charts": result["charts"],  # Словарь с графиками
            "chart_type": result["chart_type"],
            "total_records": result["total_records"],
            "filter_text": result["filter_text"],
            "year": result["year"],
        }

        request.session["combined_chart_info"] = session_data

    elif result["message_type"] == "info":
        messages.warning(request, result["message"])
    else:
        messages.error(request, result["message"])

    return redirect("analytics:combined_chart")
