# claims\views\claim_prognosis.py

# from django.shortcuts import render


# def claim_prognosis_view(request):
#     """Заглушка для модуля"""
#     context = {
#         "page_title": "Прогноз по претензиям",
#         "module_name": "Claims",
#         "description": "Прогноз по выставленным претензиям",
#         "status": "В разработке...",
#     }
#     return render(request, "claims/claim_prognosis.html", context)

"""Представление для прогнозирования претензий"""

from datetime import date
from decimal import Decimal, InvalidOperation

from django.shortcuts import render
from django.contrib import messages

from claims.modules.claim_prognosis_processor import ClaimPrognosisProcessor
from claims.models import Claim
from reclamations.models import Reclamation


def claim_prognosis_view(request):
    """Страница прогнозирования претензий"""

    # Получаем доступные годы из рекламаций
    available_reclamation_years = list(
        Reclamation.objects.values_list("year", flat=True).distinct().order_by("-year")
    )

    current_year = date.today().year
    if not available_reclamation_years:
        available_reclamation_years = [current_year]

    # Получаем доступных потребителей из претензий
    available_consumers = list(
        Claim.objects.exclude(consumer_name__isnull=True)
        .exclude(consumer_name="")
        .values_list("consumer_name", flat=True)
        .distinct()
        .order_by("consumer_name")
    )

    # Варианты прогноза
    forecast_options = [3, 6, 12]

    base_context = {
        "page_title": "Прогноз претензий",
        "description": "Прогнозирование претензий на основе анализа рекламаций и конверсии",
        "available_years": available_reclamation_years,
        "current_year": current_year,
        "available_consumers": available_consumers,
        "forecast_options": forecast_options,
        "current_date": date.today().strftime("%d.%m.%Y"),
    }

    if request.method == "POST":
        action = request.POST.get("action")

        # Валидация параметров
        year, consumers, forecast_months, exchange_rate_decimal, validation_error = (
            validate_prognosis_parameters(
                request.POST.get("year"),
                request.POST.getlist("consumers"),
                request.POST.get("forecast_months"),
                request.POST.get("exchange_rate"),
                available_reclamation_years,
                available_consumers,
            )
        )

        if validation_error:
            messages.error(request, validation_error)
            return render(request, "claims/claim_prognosis.html", base_context)

        # Создаем процессор
        processor = ClaimPrognosisProcessor(
            year=year,
            consumers=consumers,
            forecast_months=forecast_months,
            exchange_rate=exchange_rate_decimal,
        )

        # Генерируем анализ
        analysis_result = processor.generate_analysis()

        # Обрабатываем результат
        context, error_message, warning_message = handle_prognosis_result(
            analysis_result, base_context
        )

        # Обрабатываем сообщения
        if error_message:
            messages.error(request, error_message)
            return render(request, "claims/claim_prognosis.html", base_context)

        if warning_message:
            messages.warning(request, warning_message)
            return render(request, "claims/claim_prognosis.html", base_context)

        # Если нужно сохранить файлы
        if action == "save_files":
            result = processor.save_to_files()

            if result["success"]:
                messages.success(
                    request, f"✅ Файлы сохранены в папку {result['base_dir']}"
                )
            else:
                messages.error(request, f"❌ Ошибка при сохранении: {result['error']}")

        return render(request, "claims/claim_prognosis.html", context)

    # GET запрос - показываем форму
    return render(request, "claims/claim_prognosis.html", base_context)


def validate_prognosis_parameters(
    year_str,
    consumers_list,
    forecast_months_str,
    exchange_rate_str,
    available_years,
    available_consumers,
):
    """Валидация параметров для прогнозирования"""

    # Валидация года
    try:
        year = int(year_str) if year_str else date.today().year

        if year < 2000 or year > date.today().year:
            return None, None, None, None, "Некорректный год"

        if year not in available_years:
            return None, None, None, None, f"⚠️ Рекламаций за {year} год нет в базе"

    except (ValueError, TypeError):
        return None, None, None, None, "Некорректный год"

    # Валидация потребителей
    consumers = []
    if consumers_list:
        for consumer in consumers_list:
            if consumer not in available_consumers:
                return None, None, None, None, f"Потребитель '{consumer}' не найден"
        consumers = consumers_list

    # Валидация периода прогноза
    try:
        forecast_months = int(forecast_months_str) if forecast_months_str else 6

        if forecast_months not in [3, 6, 12]:
            return (
                None,
                None,
                None,
                None,
                "Период прогноза должен быть 3, 6 или 12 месяцев",
            )

    except (ValueError, TypeError):
        return None, None, None, None, "Некорректный период прогноза"

    # Валидация курса
    try:
        if exchange_rate_str:
            exchange_rate_str = str(exchange_rate_str).replace(",", ".")
            exchange_rate_decimal = Decimal(exchange_rate_str)

            if exchange_rate_decimal <= 0:
                return None, None, None, None, "Курс должен быть положительным числом"
        else:
            exchange_rate_decimal = Decimal("0.03")

    except (ValueError, InvalidOperation):
        return None, None, None, None, "Некорректный курс обмена"

    return year, consumers, forecast_months, exchange_rate_decimal, None


def handle_prognosis_result(analysis_result, base_context):
    """Обработка результата прогнозирования"""

    if not analysis_result["success"]:
        error_message = (
            f"❌ {analysis_result.get('error', 'Ошибка при генерации прогноза')}"
        )
        return None, error_message, None

    # Проверяем наличие данных
    if not analysis_result["historical"]["labels"]:
        warning_message = (
            f"⚠️ Нет данных для прогнозирования за {analysis_result['year']} год"
        )
        return None, None, warning_message

    context = {
        **base_context,
        "prognosis_data": format_prognosis_data(analysis_result),
    }

    return context, None, None


def format_prognosis_data(result):
    """Форматирование данных прогноза для передачи в шаблон"""

    # Считаем суммы для карточек
    total_reclamations_forecast = sum(result["combined_data"]["reclamations_forecast"])
    total_claims_forecast = sum(result["combined_data"]["claims_forecast"])

    return {
        "year": int(result["year"]),
        "consumers": result["consumers"],
        "consumer_display": result.get("consumer_display", ""),
        "all_consumers_mode": result.get("all_consumers_mode", False),
        "forecast_months": int(result["forecast_months"]),
        "exchange_rate": str(result["exchange_rate"]),
        # Суммы для карточек
        "total_reclamations_forecast": int(total_reclamations_forecast),
        "total_claims_forecast": int(total_claims_forecast),
        # Исторические данные
        "historical": {
            "labels": result["historical"]["labels"],
            "labels_formatted": result["historical"]["labels_formatted"],
            "reclamations": result["historical"]["reclamations"],
            "claims": result["historical"]["claims"],
            "claims_costs": result["historical"]["claims_costs"],
        },
        # Параметры конверсии
        "conversion_params": {
            "conversion_rate": float(result["conversion_params"]["conversion_rate"]),
            "escalation_days": int(result["conversion_params"]["escalation_days"]),
            "total_reclamations": int(
                result["conversion_params"]["total_reclamations"]
            ),
            "escalated_reclamations": int(
                result["conversion_params"]["escalated_reclamations"]
            ),
        },
        # Объединенные данные для графика
        "combined_data": {
            "labels": result["combined_data"]["labels"],
            "labels_formatted": result["combined_data"]["labels_formatted"],
            "reclamations_fact": result["combined_data"]["reclamations_fact"],
            "reclamations_forecast": result["combined_data"]["reclamations_forecast"],
            "claims_fact": result["combined_data"]["claims_fact"],
            "claims_forecast": result["combined_data"]["claims_forecast"],
        },
    }
