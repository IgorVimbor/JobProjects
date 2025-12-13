# claims/views/consumer_analysis.py
"""Представление для страницы анализа претензий по потребителю"""

from datetime import date
from decimal import Decimal, InvalidOperation
from django.shortcuts import redirect, render
from django.contrib import messages

from claims.modules.consumer_analysis_processor import ConsumerAnalysisProcessor
from claims.models import Claim


def consumer_analysis_view(request):
    """Страница анализа претензий по потребителю"""

    # Получаем доступные годы и потребителей
    available_years = list(
        Claim.objects.values_list("claim_date__year", flat=True)
        .distinct()
        .order_by("-claim_date__year")
    )

    current_year = date.today().year
    if not available_years:
        available_years = [current_year]

    available_consumers = list(
        Claim.objects.exclude(consumer_name__isnull=True)
        .exclude(consumer_name="")
        .values_list("consumer_name", flat=True)
        .distinct()
        .order_by("consumer_name")
    )

    base_context = {
        "page_title": "Анализ по потребителю",
        "description": "Детальный анализ претензий по выбранному потребителю",
        "available_years": available_years,
        "current_year": current_year,
        "available_consumers": available_consumers,
        "current_date": date.today().strftime("%d.%m.%Y"),
    }

    if request.method == "POST":
        action = request.POST.get("action")

        # Общая валидация параметров
        year, consumers, exchange_rate_decimal, validation_error = (
            validate_consumer_parameters(
                request.POST.get("year"),
                request.POST.getlist("consumers"),
                request.POST.get("exchange_rate"),
                available_consumers,
            )
        )

        if validation_error:
            messages.error(request, validation_error)
            return render(request, "claims/consumer_analysis.html", base_context)

        # Создаем процессор и ОДИН РАЗ генерируем анализ
        processor = ConsumerAnalysisProcessor(
            year=year, consumers=consumers, exchange_rate=exchange_rate_decimal
        )

        analysis_result = processor.generate_analysis()

        # Обрабатываем результат анализа
        context, error_message, warning_message = handle_analysis_result(
            analysis_result, base_context, year
        )

        # Обрабатываем сообщения
        if error_message:
            messages.error(request, error_message)
            return render(request, "claims/consumer_analysis.html", base_context)

        if warning_message:
            messages.warning(request, warning_message)
            return render(request, "claims/consumer_analysis.html", base_context)

        # Если нужно сохранить файлы
        if action == "save_files":
            result = processor.save_to_files(analysis_result)

            if result["success"]:
                messages.success(
                    request, f"✅ Файлы сохранены в папку {result['base_dir']}"
                )
            else:
                messages.error(request, f"❌ Ошибка при сохранении: {result['error']}")

        return render(request, "claims/consumer_analysis.html", context)

    # GET запрос - показываем форму
    return render(request, "claims/consumer_analysis.html", base_context)


def handle_analysis_result(analysis_result, base_context, year):
    """Обработка результата анализа (вынесена общая логика)

    Возвращает:
        (context, error_message, warning_message)
    """

    if not analysis_result["success"]:
        error_message = (
            f"❌ {analysis_result.get('error', 'Ошибка при генерации анализа')}"
        )
        return None, error_message, None

    if analysis_result["summary_data"]["total_claims"] == 0:
        consumer_text = analysis_result.get(
            "consumer_display", "выбранным потребителям"
        )
        warning_message = f"⚠️ Нет данных по {consumer_text} за {year} год"
        return None, None, warning_message

    context = {
        **base_context,
        "analysis_data": format_analysis_data(analysis_result),
    }

    return context, None, None


def validate_consumer_parameters(
    year_str, consumers_list, exchange_rate_str, available_consumers
):
    """Валидация параметров для анализа потребителя"""

    # Валидация года
    try:
        year = int(year_str) if year_str else date.today().year

        if year < 2000 or year > date.today().year:
            return None, None, None, "Некорректный год"

    except (ValueError, TypeError):
        return None, None, None, "Некорректный год"

    # Валидация потребителей
    consumers = []
    if consumers_list:
        # Проверяем, что все выбранные потребители существуют
        for consumer in consumers_list:
            if consumer not in available_consumers:
                return None, None, None, f"Потребитель '{consumer}' не найден"
        consumers = consumers_list
    # Если список пустой - анализируем всех потребителей

    # Валидация курса
    try:
        if exchange_rate_str:
            exchange_rate_str = str(exchange_rate_str).replace(",", ".")
            exchange_rate_decimal = Decimal(exchange_rate_str)

            if exchange_rate_decimal <= 0:
                return None, None, None, "Курс должен быть положительным числом"
        else:
            exchange_rate_decimal = Decimal("0.03")

    except (ValueError, InvalidOperation):
        return None, None, None, "Некорректный курс обмена"

    return year, consumers, exchange_rate_decimal, None


def format_analysis_data(result):
    """Форматирование данных анализа для передачи в шаблон"""
    return {
        "year": int(result["year"]),
        "consumers": result["consumers"],
        "consumer_display": result.get("consumer_display", ""),
        "all_consumers_mode": result.get("all_consumers_mode", False),
        "exchange_rate": str(result["exchange_rate"]),
        "summary_data": {
            "total_claims": int(result["summary_data"]["total_claims"]),
            "total_acts": int(result["summary_data"]["total_acts"]),
            "total_amount_byn": str(result["summary_data"]["total_amount_byn"]),
            "total_costs_byn": str(result["summary_data"]["total_costs_byn"]),
            "acceptance_percent": float(result["summary_data"]["acceptance_percent"]),
        },
        "monthly_dynamics": {
            "labels": result["monthly_dynamics"]["labels"],
            "amounts": result["monthly_dynamics"]["amounts"],
            "costs": result["monthly_dynamics"]["costs"],
        },
        "monthly_table": result.get("monthly_table", {}),
    }
