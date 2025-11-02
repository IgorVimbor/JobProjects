# claims/views/analytics.py
"""Представления для аналитики претензий"""

from datetime import date
from decimal import Decimal, InvalidOperation
from django.shortcuts import redirect, render
from django.contrib import messages

from claims.modules.dashboard_processor import DashboardProcessor
from claims.models import Claim


def dashboard_view(request):
    """Страница Dashboard претензий"""

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "save_files":
            # ОБРАБОТКА СОХРАНЕНИЯ ФАЙЛОВ
            year = request.POST.get("year")
            exchange_rate = request.POST.get("exchange_rate")

            try:
                year = int(year)
                exchange_rate_decimal = Decimal(str(exchange_rate).replace(",", "."))
            except (ValueError, TypeError, InvalidOperation):
                messages.error(request, "Некорректные параметры")
                return redirect("claims:dashboard")

            # Создаем процессор и сохраняем файлы
            processor = DashboardProcessor(
                year=year, exchange_rate=exchange_rate_decimal
            )
            result = processor.save_to_files()

            if result["success"]:
                messages.success(
                    request, f"✅ Файлы сохранены в папку {result['base_dir']}"
                )
            else:
                messages.error(request, f"❌ Ошибка при сохранении: {result['error']}")

            return redirect("claims:dashboard")

        else:
            # ОБЫЧНАЯ ГЕНЕРАЦИЯ DASHBOARD
            return generate_dashboard(request)

    # GET запрос - показываем форму
    dashboard_data = request.session.get("claims_dashboard_data", None)
    if dashboard_data:
        del request.session["claims_dashboard_data"]

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
        "page_title": "Dashboard претензий",
        "description": "Общая сводка по претензиям с финансовыми показателями",
        "dashboard_data": dashboard_data,
        "available_years": available_years,
        "current_year": current_year,
        "current_date": date.today().strftime("%d.%m.%Y"),
    }
    return render(request, "claims/dashboard.html", context)


def generate_dashboard(request):
    """Генерация Dashboard"""

    # Получаем параметры из формы
    year = request.POST.get("year")
    exchange_rate = request.POST.get("exchange_rate")

    # Валидация года
    try:
        year = int(year) if year else date.today().year

        # Проверка корректности года
        if year < 2000 or year > date.today().year:
            messages.error(request, "Некорректный год")
            return redirect("claims:dashboard")

    except (ValueError, TypeError):
        messages.error(request, "Некорректный год")
        return redirect("claims:dashboard")

    # Валидация курса
    try:
        if exchange_rate:
            # Заменяем запятую на точку (если пользователь ввёл с запятой)
            exchange_rate_str = str(exchange_rate).replace(",", ".")
            exchange_rate_decimal = Decimal(exchange_rate_str)

            # Проверка корректности курса
            if exchange_rate_decimal <= 0:
                messages.error(request, "Курс должен быть положительным числом")
                return redirect("claims:dashboard")

            if exchange_rate_decimal > 1:
                messages.warning(
                    request,
                    "⚠️ Проверьте курс! Обычно курс RUR→BYN меньше 1 (например, 0.03)",
                )
        else:
            exchange_rate_decimal = Decimal("0.03")  # Дефолтное значение

    except (ValueError, InvalidOperation):
        messages.error(request, "Некорректный курс обмена")
        return redirect("claims:dashboard")

    # Генерируем Dashboard
    processor = DashboardProcessor(year=year, exchange_rate=exchange_rate_decimal)
    result = processor.generate_dashboard()

    if result["success"]:
        # messages.success(request, f"✅ Dashboard за {year} год сформирован")

        # Сохраняем результаты в session
        # ⚠️ ВАЖНО: конвертируем данные для JSON сериализации
        request.session["claims_dashboard_data"] = {
            "year": int(result["year"]),
            "exchange_rate": str(result["exchange_rate"]),
            "summary_cards": {
                "total_claims": int(result["summary_cards"]["total_claims"]),
                "total_acts": int(result["summary_cards"]["total_acts"]),
                "total_amount_byn": str(result["summary_cards"]["total_amount_byn"]),
                "total_costs_byn": str(result["summary_cards"]["total_costs_byn"]),
                "acceptance_percent": float(
                    result["summary_cards"]["acceptance_percent"]
                ),
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
    else:
        messages.error(
            request, f"❌ {result.get('error', 'Ошибка при генерации Dashboard')}"
        )

    return redirect("claims:dashboard")
