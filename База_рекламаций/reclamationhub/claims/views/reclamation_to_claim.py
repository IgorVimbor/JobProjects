# claims/views/reclamation_to_claim.py
"""Представления для анализа конверсии рекламация → претензия"""

from datetime import date
from decimal import Decimal, InvalidOperation
from django.shortcuts import redirect, render
from django.contrib import messages

from claims.modules.reclamation_to_claim_processor import ReclamationToClaimProcessor
from claims.models import Claim
from reclamations.models import Reclamation


# def reclamation_to_claim_view(request):
#     """Заглушка для модуля"""
#     context = {
#         "page_title": "Графики и таблицы по претензиям",
#         "module_name": "Claims",
#         "description": "Графики и таблицы по выставленным и признанным претензиям",
#         "status": "В разработке...",
#     }
#     return render(request, "claims/reclamation_to_claim.html", context)


def reclamation_to_claim_view(request):
    """Страница анализа конверсии рекламация → претензия"""

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

    base_context = {
        "page_title": "Рекламация → Претензия",
        "description": "Анализ конверсии рекламаций в признанные претензии",
        "available_years": available_reclamation_years,
        "current_year": current_year,
        "available_consumers": available_consumers,
        "current_date": date.today().strftime("%d.%m.%Y"),
    }

    if request.method == "POST":
        action = request.POST.get("action")

        # Общая валидация параметров
        year, consumers, exchange_rate_decimal, validation_error = (
            validate_reclamation_parameters(
                request.POST.get("year"),
                request.POST.getlist("consumers"),
                request.POST.get("exchange_rate"),
                available_reclamation_years,
                available_consumers,
            )
        )

        if validation_error:
            messages.error(request, validation_error)
            return render(request, "claims/reclamation_to_claim.html", base_context)

        # Создаем процессор
        processor = ReclamationToClaimProcessor(
            year=year, consumers=consumers, exchange_rate=exchange_rate_decimal
        )

        if action == "save_files":
            # ОБРАБОТКА СОХРАНЕНИЯ ФАЙЛОВ
            result = processor.save_to_files()

            if result["success"]:
                messages.success(
                    request, f"✅ Файлы сохранены в папку {result['base_dir']}"
                )
            else:
                messages.error(request, f"❌ Ошибка при сохранении: {result['error']}")

            # Генерируем данные заново и отображаем их
            analysis_result = processor.generate_analysis()

            if analysis_result["success"]:
                # Проверяем наличие данных
                if (
                    analysis_result["group_a"]["summary_cards"]["total_reclamations"]
                    == 0
                ):
                    messages.warning(
                        request,
                        f"⚠️ Нет рекламаций за {year} год в базе",
                    )
                    return render(
                        request, "claims/reclamation_to_claim.html", base_context
                    )

                context = {
                    **base_context,
                    "conversion_data": format_analysis_data(analysis_result),
                }
                return render(request, "claims/reclamation_to_claim.html", context)
            else:
                messages.error(
                    request,
                    f"❌ Ошибка при генерации анализа: {analysis_result.get('error')}",
                )
                return render(request, "claims/reclamation_to_claim.html", base_context)

        else:
            # ОБЫЧНАЯ ГЕНЕРАЦИЯ АНАЛИЗА
            result = processor.generate_analysis()

            if result["success"]:
                # Проверяем наличие данных
                if result["group_a"]["summary_cards"]["total_reclamations"] == 0:
                    messages.warning(
                        request,
                        f"⚠️ Нет рекламаций за {year} год в базе",
                    )
                    return render(
                        request, "claims/reclamation_to_claim.html", base_context
                    )

                context = {
                    **base_context,
                    "conversion_data": format_analysis_data(result),
                }
                return render(request, "claims/reclamation_to_claim.html", context)
            else:
                messages.error(
                    request, f"❌ {result.get('error', 'Ошибка при генерации анализа')}"
                )
                return render(request, "claims/reclamation_to_claim.html", base_context)

    # GET запрос - показываем форму
    return render(request, "claims/reclamation_to_claim.html", base_context)


def validate_reclamation_parameters(
    year_str, consumers_list, exchange_rate_str, available_years, available_consumers
):
    """Валидация параметров для анализа рекламация → претензия"""

    # Валидация года
    try:
        year = int(year_str) if year_str else date.today().year

        if year < 2000 or year > date.today().year:
            return None, None, None, "Некорректный год"

        # Проверяем наличие года в базе рекламаций
        if year not in available_years:
            return None, None, None, f"⚠️ Рекламаций за {year} год нет в базе"

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
        # Группа A
        "group_a": {
            "summary_cards": {
                "total_reclamations": int(
                    result["group_a"]["summary_cards"]["total_reclamations"]
                ),
                "escalated_reclamations": int(
                    result["group_a"]["summary_cards"]["escalated_reclamations"]
                ),
                "escalation_rate": float(
                    result["group_a"]["summary_cards"]["escalation_rate"]
                ),
                "average_days": int(result["group_a"]["summary_cards"]["average_days"]),
            },
            "monthly_conversion": {
                "labels": result["group_a"]["monthly_conversion"]["labels"],
                "conversion_rates": result["group_a"]["monthly_conversion"][
                    "conversion_rates"
                ],
            },
            "time_distribution": {
                "labels": result["group_a"]["time_distribution"]["labels"],
                "counts": result["group_a"]["time_distribution"]["counts"],
            },
            "top_consumers": [
                {
                    "consumer": consumer["consumer"],
                    "total_reclamations": int(consumer["total_reclamations"]),
                    "escalated": int(consumer["escalated"]),
                    "conversion_rate": float(consumer["conversion_rate"]),
                    "average_days": int(consumer["average_days"]),
                }
                for consumer in result["group_a"]["top_consumers"]
            ],
        },
        # Группа B
        "group_b": {
            "summary_cards": {
                "claims_without_link": int(
                    result["group_b"]["summary_cards"]["claims_without_link"]
                ),
                "claims_without_date": int(
                    result["group_b"]["summary_cards"]["claims_without_date"]
                ),
                "total_amount_byn": str(
                    result["group_b"]["summary_cards"]["total_amount_byn"]
                ),
            },
            "time_distribution": {
                "labels": result["group_b"]["time_distribution"]["labels"],
                "counts": result["group_b"]["time_distribution"]["counts"],
            },
        },
    }
