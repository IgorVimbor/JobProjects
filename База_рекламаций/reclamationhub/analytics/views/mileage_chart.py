from datetime import datetime
from django.shortcuts import redirect, render
from django.contrib import messages

from analytics.modules.mileage_chart_modul import MileageChartProcessor
from reclamations.models import Reclamation


# def mileage_chart_page(request):
#     """Заглушка для модуля 'Диаграмма по пробегу (наработке)'"""
#     context = {
#         "page_title": "Диаграмма по пробегу",
#         "module_name": "Mileage Chart",
#         "description": "Диаграмма по пробегу (наработке) в эксплуатации по виду изделия и потребителю",
#         "status": "В разработке...",
#     }
#     return render(request, "analytics/mileage_chart.html", context)


def mileage_chart_page(request):
    """Страница модуля 'Диаграмма по пробегу (наработке)'"""

    if request.method == "POST":
        return generate_report(request)

    # GET запрос - показываем актуальную информацию
    download_info = request.session.get("mileage_chart_info", None)
    if download_info:
        del request.session["mileage_chart_info"]

    # Получаем доступные годы для селектора
    available_years = list(
        Reclamation.objects.values_list("year", flat=True).distinct().order_by("-year")
    )

    # Получаем потребителей с суффиксом "- эксплуатация"
    available_consumers_raw = (
        Reclamation.objects.select_related("defect_period")
        .filter(defect_period__name__icontains="- эксплуатация")
        .values_list("defect_period__name", flat=True)
        .distinct()
        .order_by("defect_period__name")
    )

    available_consumers = [
        {"value": consumer, "name": consumer}
        for consumer in available_consumers_raw
        if consumer
    ]

    # Получаем список изделий
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
        "page_title": "Диаграмма по пробегу",
        "description": "Диаграмма по пробегу (наработке) в эксплуатации по виду изделия и потребителю",
        "download_info": download_info,
        "available_years": available_years,
        "current_year": datetime.now().year,
        "available_consumers": available_consumers,
        "available_products": available_products,
    }
    return render(request, "analytics/mileage_chart.html", context)


def generate_report(request):
    """Генерация отчета"""
    # Получаем данные из POST
    year = request.POST.get("year")  # Год данных
    step = request.POST.get("step")  # Шаг разбиения пробега
    # Получаем выбранных потребителей и изделия из чекбоксов
    selected_consumers = request.POST.getlist("consumers")
    selected_products = request.POST.getlist("products")

    # Валидация полей для которых предусмотрен выбор из предложенных - это защита от модификации HTML и прямых POST запросов.
    # Возможные атаки:
    # DevTools: пользователь добавляет <option value="100000">100 000</option>
    # Прямой POST: отправка запроса с step=999999
    # Скрипты: автоматическая отправка с некорректными данными
    try:
        year = int(year) if year else datetime.now().year
        step = int(step) if step else 5000  # Дефолт 5000
    except (ValueError, TypeError):
        messages.error(request, "Некорректные данные")
        return redirect("analytics:mileage_chart")

    # Проверка года
    current_year = datetime.now().year
    if year > current_year:
        messages.error(request, f"Нельзя формировать отчет за будущий {year} год")
        return redirect("analytics:mileage_chart")

    # Валидация шага
    if step not in [500, 1000, 2000, 5000, 10000]:
        messages.error(request, "Некорректный шаг пробега")
        return redirect("analytics:mileage_chart")

    # Валидация потребителей - только с суффиксом "- эксплуатация"
    consumers = []
    if selected_consumers:
        valid_consumers = list(
            Reclamation.objects.filter(defect_period__name__icontains="- эксплуатация")
            .values_list("defect_period__name", flat=True)
            .distinct()
        )
        consumers = [c for c in selected_consumers if c in valid_consumers]

    # Проверка наличия изделия - обязательно должно быть выбрано изделие
    if not selected_products:
        messages.warning(request, "⚠️ Выберите изделие для анализа")
        return redirect("analytics:mileage_chart")

    # Валидация изделий
    valid_products = list(
        Reclamation.objects.values_list("product_name__name", flat=True).distinct()
    )
    products = [p for p in selected_products if p in valid_products]

    if not products:
        messages.error(request, "Выбраны некорректные изделия")
        return redirect("analytics:mileage_chart")

    # Генерируем анализ
    processor = MileageChartProcessor(
        year=year, consumers=consumers, products=products, step=step
    )
    result = processor.generate_report()

    if result["success"]:
        messages.success(request, f"✅ {result['message']}")
        request.session["mileage_chart_info"] = {
            # "message": f"Анализ пробега для {result['filter_text']} за {result['year']} год",
            "table_data": result["table_data"],
            "chart_base64": result["chart_base64"],
            "total_records": result["total_records"],
            "filter_text": result["filter_text"],
            "year": result["year"],
        }
    elif result["message_type"] == "info":
        messages.warning(request, result["message"])
    else:
        messages.error(request, result["message"])

    return redirect("analytics:mileage_chart")
