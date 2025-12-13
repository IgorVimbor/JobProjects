# claims/views/dashboard.py
"""Представления для страницы Dashboard претензий."""

from datetime import date
from decimal import Decimal, InvalidOperation
from django.shortcuts import redirect, render
from django.contrib import messages

from claims.modules.dashboard_processor import DashboardProcessor
from claims.models import Claim


def dashboard_view(request):
    """Страница Dashboard претензий"""

    # Получаем доступные годы
    available_years = list(
        Claim.objects.values_list("claim_date__year", flat=True)
        .distinct()
        .order_by("-claim_date__year")
    )

    current_year = date.today().year
    if not available_years:
        available_years = [current_year]

    base_context = {
        "page_title": "Общая сводка",
        "description": "Сводная информация по претензиям с финансовыми показателями",
        "available_years": available_years,
        "current_year": current_year,
        "current_date": date.today().strftime("%d.%m.%Y"),
    }

    if request.method == "POST":
        action = request.POST.get("action")

        # Общая валидация параметров
        year, exchange_rate_decimal, validation_error = validate_parameters(
            request.POST.get("year"), request.POST.get("exchange_rate")
        )

        if validation_error:
            messages.warning(request, validation_error)
            return render(request, "claims/dashboard.html", base_context)

        # Создаем процессор и ОДИН РАЗ генерируем данные
        processor = DashboardProcessor(year=year, exchange_rate=exchange_rate_decimal)

        dashboard_result = processor.generate_dashboard()

        # Обрабатываем результат
        context, error_message, warning_message = handle_dashboard_result(
            dashboard_result, base_context
        )

        # Обрабатываем сообщения
        if error_message:
            messages.warning(request, error_message)
            return render(request, "claims/dashboard.html", base_context)

        if warning_message:
            messages.warning(request, warning_message)
            return render(request, "claims/dashboard.html", base_context)

        # Если нужно сохранить файлы
        if action == "save_files":
            # Используем УЖЕ сгенерированные данные для сохранения
            result = processor.save_to_files(dashboard_result)

            if result["success"]:
                messages.success(
                    request, f"✅ Файлы сохранены в папку {result['base_dir']}"
                )
            else:
                messages.warning(
                    request, f"❌ Ошибка при сохранении: {result['error']}"
                )

        return render(request, "claims/dashboard.html", context)

    # GET запрос - показываем форму
    return render(request, "claims/dashboard.html", base_context)


def handle_dashboard_result(dashboard_result, base_context):
    """Обработка результата генерации dashboard (вынесена общая логика)

    Возвращает:
        (context, error_message, warning_message)
    """

    if not dashboard_result["success"]:
        error_message = (
            f"❌ {dashboard_result.get('error', 'Ошибка при генерации Dashboard')}"
        )
        return None, error_message, None

    # Проверка на наличие данных
    if dashboard_result["summary_cards"]["total_claims"] == 0:
        warning_message = f"⚠️ Нет данных за выбранный период"
        return None, None, warning_message

    context = {
        **base_context,
        "dashboard_data": format_dashboard_data(dashboard_result),
    }

    return context, None, None


def validate_parameters(year_str, exchange_rate_str):
    """Валидация параметров года и курса обмена"""

    # Валидация года
    try:
        year = int(year_str) if year_str else date.today().year

        if year < 2000 or year > date.today().year:
            return None, None, "Некорректный год"

    except (ValueError, TypeError):
        return None, None, "Некорректный год"

    # Валидация курса
    try:
        if exchange_rate_str:
            exchange_rate_str = str(exchange_rate_str).replace(",", ".")
            exchange_rate_decimal = Decimal(exchange_rate_str)

            if exchange_rate_decimal <= 0:
                return None, None, "Курс должен быть положительным числом"

            if exchange_rate_decimal > 1:
                return (
                    None,
                    None,
                    "⚠️ Проверьте курс! Обычно курс RUR→BYN меньше 1 (например, 0.03)",
                )
        else:
            exchange_rate_decimal = Decimal("0.03")  # Дефолтное значение

    except (ValueError, InvalidOperation):
        return None, None, "Некорректный курс обмена"

    return year, exchange_rate_decimal, None


def format_dashboard_data(result):
    """Форматирование данных dashboard для передачи в шаблон"""
    return {
        "year": int(result["year"]),
        "exchange_rate": str(result["exchange_rate"]),
        "summary_cards": {
            "total_claims": int(result["summary_cards"]["total_claims"]),
            "total_acts": int(result["summary_cards"]["total_acts"]),
            "total_amount_byn": str(result["summary_cards"]["total_amount_byn"]),
            "total_costs_byn": str(result["summary_cards"]["total_costs_byn"]),
            "acceptance_percent": float(result["summary_cards"]["acceptance_percent"]),
        },
        "monthly_dynamics": {
            "labels": result["monthly_dynamics"]["labels"],
            "amounts": result["monthly_dynamics"]["amounts"],
            "costs": result["monthly_dynamics"]["costs"],
        },
        "top_consumers": [
            {
                "consumer": consumer["consumer"],
                "amount": str(consumer["amount"]),
                "costs": str(consumer["costs"]),
                "acceptance_percent": float(consumer["acceptance_percent"]),
                "count": int(consumer["count"]),
            }
            for consumer in result["top_consumers"]
        ],
    }
