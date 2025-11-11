# analytics/views/combined_chart.py
"""Представления для модуля анализа по датам изготовления изделия и уведомления о дефектах"""

from datetime import datetime
from django.shortcuts import redirect, render
from django.contrib import messages

from analytics.modules.combined_chart_modul import DefectDateReportManager
from reclamations.models import Reclamation


def combined_chart_page(request):
    """Страница модуля 'Диаграммы по дате уведомления, дате изготовления и совмещенная'"""

    # Получаем доступные годы и другие данные
    available_years = ["all"] + list(
        Reclamation.objects.values_list("year", flat=True).distinct().order_by("-year")
    )

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

    base_context = {
        "page_title": "Диаграммы по датам",
        "description": "Диаграммы распределения по обозначению изделия, дате уведомления о дефекте, изготовления изделия или совмещенная диаграмма",
        "available_years": available_years,
        "current_year": datetime.now().year,
        "available_consumers": available_consumers,
        "available_products": available_products,
    }

    if request.method == "POST":
        action = request.POST.get("action")

        # Общая валидация параметров
        (
            year_value,
            chart_type,
            selected_consumers,
            selected_product,
            validation_error,
        ) = validate_combined_chart_parameters(request.POST, available_products)

        if validation_error:
            messages.warning(request, validation_error)
            return render(request, "analytics/combined_chart.html", base_context)

        # ДОБАВЛЯЕМ параметры запроса в base_context:
        base_context.update(
            {
                "request_year": year_value,
                "request_chart_type": chart_type,
                "request_consumers": selected_consumers,
                "request_product": selected_product,
            }
        )

        # Создаем процессор и ОДИН РАЗ генерируем анализ
        manager = DefectDateReportManager(
            year=year_value, consumers=selected_consumers, product=selected_product
        )

        analysis_result = manager.generate_report(chart_type=chart_type)

        # Обрабатываем результат (base_context содержит параметры запроса)
        context, error_message, warning_message = handle_combined_chart_result(
            analysis_result, base_context
        )

        # Обрабатываем сообщения
        if error_message:
            messages.warning(request, error_message)
            return render(request, "analytics/combined_chart.html", base_context)

        if warning_message:
            messages.warning(request, warning_message)
            return render(request, "analytics/combined_chart.html", base_context)

        # Если нужно сохранить файлы
        if action == "save_files":
            # Используем УЖЕ сгенерированные данные для сохранения
            result = manager.save_to_files(analysis_result)

            if result["success"]:
                messages.success(
                    request, f"✅ Файлы сохранены в папку {result['base_dir']}"
                )
            else:
                messages.warning(
                    request, f"❌ Ошибка при сохранении: {result['error']}"
                )
        else:
            # Показываем сообщение об успешной генерации
            messages.success(request, f"✅ {analysis_result['message']}")

        return render(request, "analytics/combined_chart.html", context)

    # GET запрос - показываем форму
    return render(request, "analytics/combined_chart.html", base_context)


def validate_combined_chart_parameters(post_data, available_products):
    """Валидация параметров для анализа диаграмм по датам"""

    year = post_data.get("year")
    chart_type = post_data.get("chart_type", "all")
    selected_consumers = post_data.getlist("consumers")
    selected_product = post_data.get("product")

    # Валидация года
    try:
        if year == "all":
            year_value = "all"
        else:
            year_value = int(year) if year else datetime.now().year
    except (ValueError, TypeError):
        return None, None, None, None, "Некорректный год"

    # Проверка года (если не "all")
    if year_value != "all":
        current_year = datetime.now().year
        if year_value > current_year:
            return (
                None,
                None,
                None,
                None,
                f"Нельзя формировать отчет за будущий {year_value} год",
            )

    # Валидация типа графика
    valid_chart_types = ["product", "manufacture", "message", "combined", "all"]
    if chart_type not in valid_chart_types:
        return None, None, None, None, "Некорректный тип графика"

    # Проверка наличия изделия
    if not selected_product:
        return None, None, None, None, "⚠️ Выберите изделие для анализа"

    # Валидация изделия
    valid_products = [product["value"] for product in available_products]
    if selected_product not in valid_products:
        return None, None, None, None, "Выбрано некорректное изделие"

    # Валидация потребителей
    consumers = []
    if selected_consumers:
        valid_consumers = list(
            Reclamation.objects.values_list("defect_period__name", flat=True).distinct()
        )
        consumers = [c for c in selected_consumers if c in valid_consumers]

    return year_value, chart_type, consumers, selected_product, None


def handle_combined_chart_result(analysis_result, base_context):
    """Обработка результата анализа диаграмм (вынесена общая логика)

    Возвращает:
        (context, error_message, warning_message)
    """

    if not analysis_result["success"]:
        if analysis_result.get("message_type") == "info":
            warning_message = analysis_result["message"]
            return None, None, warning_message
        else:
            error_message = analysis_result["message"]
            return None, error_message, None

    # Формируем контекст с данными для отображения
    download_info = {
        # "message": analysis_result["full_message"],
        "charts": analysis_result["charts"],
        "chart_type": analysis_result["chart_type"],
        "total_records": analysis_result["total_records"],
        "filter_text": analysis_result["filter_text"],
        "year": analysis_result["year"],
    }

    context = {
        **base_context,
        "download_info": download_info,
    }

    return context, None, None
