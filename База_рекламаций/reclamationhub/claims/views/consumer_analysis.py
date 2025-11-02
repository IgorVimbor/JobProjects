# claims/views/consumer_analysis.py

from datetime import date
from decimal import Decimal, InvalidOperation
from django.shortcuts import redirect, render
from django.contrib import messages

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from reports.config.paths import (
    get_claims_dashboard_chart_path,
    get_claims_dashboard_table_path,
    BASE_REPORTS_DIR,
)
from claims.modules.dashboard_processor import DashboardProcessor
from claims.modules.consumer_analysis_processor import ConsumerAnalysisProcessor
from claims.models import Claim


# def consumer_analysis_view(request):
#     """Заглушка для модуля"""
#     context = {
#         "page_title": "Претензии по потребителю",
#         "module_name": "Claims",
#         "description": "Информация по выставленным и признанным претензиям по потребителю",
#         "status": "В разработке...",
#     }
#     return render(request, "claims/consumer_analysis.html", context)


def consumer_analysis_view(request):
    """Страница анализа претензий по потребителю"""

    if request.method == "POST":
        return generate_consumer_analysis(request)

    # GET запрос - показываем форму
    analysis_data = request.session.get("consumer_analysis_data", None)
    if analysis_data:
        del request.session["consumer_analysis_data"]

    # Получаем доступные годы
    available_years = list(
        Claim.objects.values_list("claim_date__year", flat=True)
        .distinct()
        .order_by("-claim_date__year")
    )

    current_year = date.today().year
    if not available_years:
        available_years = [current_year]

    # Получаем список потребителей
    available_consumers = list(
        Claim.objects.exclude(consumer_name__isnull=True)
        .exclude(consumer_name="")
        .values_list("consumer_name", flat=True)
        .distinct()
        .order_by("consumer_name")
    )

    context = {
        "page_title": "Анализ по потребителю",
        "description": "Детальный анализ претензий по выбранному потребителю",
        "analysis_data": analysis_data,
        "available_years": available_years,
        "current_year": current_year,
        "available_consumers": available_consumers,
        "current_date": date.today().strftime("%d.%m.%Y"),
    }
    return render(request, "claims/consumer_analysis.html", context)


def generate_consumer_analysis(request):
    """Генерация анализа по потребителю"""

    # Получаем параметры
    year = request.POST.get("year")
    consumer = request.POST.get("consumer")
    exchange_rate = request.POST.get("exchange_rate")

    # Валидация года
    try:
        year = int(year) if year else date.today().year

        if year < 2000 or year > date.today().year:
            messages.error(request, "Некорректный год")
            return redirect("claims:consumer_analysis")

    except (ValueError, TypeError):
        messages.error(request, "Некорректный год")
        return redirect("claims:consumer_analysis")

    # Валидация потребителя
    if not consumer:
        messages.error(request, "Выберите потребителя")
        return redirect("claims:consumer_analysis")

    # Проверка существования потребителя в БД
    valid_consumers = list(
        Claim.objects.exclude(consumer_name__isnull=True)
        .exclude(consumer_name="")
        .values_list("consumer_name", flat=True)
        .distinct()
    )

    if consumer not in valid_consumers:
        messages.error(request, "Выбранный потребитель не найден")
        return redirect("claims:consumer_analysis")

    # Валидация курса
    try:
        if exchange_rate:
            exchange_rate_str = str(exchange_rate).replace(",", ".")
            exchange_rate_decimal = Decimal(exchange_rate_str)

            if exchange_rate_decimal <= 0:
                messages.error(request, "Курс должен быть положительным числом")
                return redirect("claims:consumer_analysis")
        else:
            exchange_rate_decimal = Decimal("0.03")

    except (ValueError, InvalidOperation):
        messages.error(request, "Некорректный курс обмена")
        return redirect("claims:consumer_analysis")

    # Генерируем анализ
    processor = ConsumerAnalysisProcessor(
        year=year, consumer=consumer, exchange_rate=exchange_rate_decimal
    )
    result = processor.generate_analysis()

    if result["success"]:
        # Проверяем есть ли данные
        if result["summary_data"]["total_claims"] == 0:
            messages.warning(
                request, f"⚠️ Нет данных по потребителю '{consumer}' за {year} год"
            )
            return redirect("claims:consumer_analysis")

        # messages.success(
        #     request, f"✅ Анализ по потребителю '{consumer}' за {year} год сформирован"
        # )

        # Сохраняем в session
        request.session["consumer_analysis_data"] = {
            "year": int(result["year"]),
            "consumer": result["consumer"],
            "exchange_rate": str(result["exchange_rate"]),
            "summary_data": {
                "total_claims": int(result["summary_data"]["total_claims"]),
                "total_amount_byn": str(result["summary_data"]["total_amount_byn"]),
                "total_costs_byn": str(result["summary_data"]["total_costs_byn"]),
                "acceptance_percent": float(
                    result["summary_data"]["acceptance_percent"]
                ),
            },
            "monthly_dynamics": {
                "labels": result["monthly_dynamics"]["labels"],
                "amounts": result["monthly_dynamics"]["amounts"],
                "costs": result["monthly_dynamics"]["costs"],
            },
        }
    else:
        messages.error(
            request, f"❌ {result.get('error', 'Ошибка при генерации анализа')}"
        )

    return redirect("claims:consumer_analysis")


def save_dashboard_files(request):
    """Сохранение графика и таблицы Dashboard в файлы"""

    if request.method != "POST":
        messages.error(request, "Неверный метод запроса")
        return redirect("claims:dashboard")

    # Получаем параметры
    year = request.POST.get("year")
    exchange_rate = request.POST.get("exchange_rate")

    try:
        year = int(year)
        exchange_rate_decimal = Decimal(str(exchange_rate).replace(",", "."))
    except (ValueError, TypeError, InvalidOperation):
        messages.error(request, "Некорректные параметры")
        return redirect("claims:dashboard")

    # Генерируем Dashboard заново для получения данных
    processor = DashboardProcessor(year=year, exchange_rate=exchange_rate_decimal)
    result = processor.generate_dashboard()

    if not result["success"]:
        messages.error(request, "Ошибка при генерации данных")
        return redirect("claims:dashboard")

    try:
        # 1. Сохраняем график
        chart_path = get_claims_dashboard_chart_path(year)

        monthly_data = result["monthly_dynamics"]

        if monthly_data["labels"]:
            plt.figure(figsize=(12, 6))
            plt.plot(
                monthly_data["labels"],
                monthly_data["amounts"],
                marker="o",
                label="Выставлено (BYN)",
                color="rgb(255, 193, 7)".replace("rgb(", "")
                .replace(")", "")
                .split(","),
                linewidth=2,
            )
            plt.plot(
                monthly_data["labels"],
                monthly_data["costs"],
                marker="o",
                label="Признано (BYN)",
                color="green",
                linewidth=2,
            )

            plt.title(
                f"Динамика претензий за {year} год (BYN)",
                fontsize=14,
                fontweight="bold",
            )
            plt.xlabel("Месяц")
            plt.ylabel("Сумма (BYN)")
            plt.legend()
            plt.grid(True, alpha=0.3)
            plt.tight_layout()

            plt.savefig(chart_path, dpi=300, bbox_inches="tight")
            plt.close()

        # 2. Сохраняем таблицу
        table_path = get_claims_dashboard_table_path(year)

        top_consumers = result["top_consumers"]

        with open(table_path, "w", encoding="utf-8") as f:
            f.write(f"TOP ПОТРЕБИТЕЛЕЙ ПО СУММАМ ПРЕТЕНЗИЙ ЗА {year} ГОД\n")
            f.write(f"Курс: 1 RUR = {result['exchange_rate']} BYN\n")
            f.write("=" * 80 + "\n\n")

            f.write(
                f"{'№':<5}{'Потребитель':<30}{'Претензий':<15}{'Выставлено':<15}{'Признано':<15}{'%':<10}\n"
            )
            f.write("-" * 80 + "\n")

            for idx, consumer in enumerate(top_consumers, 1):
                f.write(
                    f"{idx:<5}"
                    f"{consumer['consumer']:<30}"
                    f"{consumer['count']:<15}"
                    f"{consumer['amount']:<15}"
                    f"{consumer['costs']:<15}"
                    f"{consumer['acceptance_percent']:<10}\n"
                )

            f.write("\n" + "=" * 80 + "\n")
            f.write(f"Всего претензий: {result['summary_cards']['total_claims']}\n")
            f.write(f"Выставлено: {result['summary_cards']['total_amount_byn']} BYN\n")
            f.write(f"Признано: {result['summary_cards']['total_costs_byn']} BYN\n")

        messages.success(request, f"✅ Файлы сохранены в папку {BASE_REPORTS_DIR}")

    except Exception as e:
        messages.error(request, f"❌ Ошибка при сохранении файлов: {str(e)}")

    return redirect("claims:dashboard")
