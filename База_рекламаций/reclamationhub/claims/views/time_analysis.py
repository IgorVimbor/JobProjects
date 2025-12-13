# claims/views/time_analysis.py
"""Представление для страницы временного анализа рекламация → претензия"""

from datetime import date
from django.shortcuts import redirect, render
from django.contrib import messages

from claims.modules.time_analysis_processor import TimeAnalysisProcessor
from claims.models import Claim


def time_analysis_view(request):
    """Страница временного анализа"""

    # Получаем доступные годы из претензий
    available_years = list(
        Claim.objects.values_list("claim_date__year", flat=True)
        .distinct()
        .order_by("-claim_date__year")
    )

    current_year = date.today().year
    if not available_years:
        available_years = [current_year]

    # Получаем доступных потребителей
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
        "available_years": available_years,
        "current_year": current_year,
        "available_consumers": available_consumers,
        "current_date": date.today().strftime("%d.%m.%Y"),
    }

    if request.method == "POST":
        action = request.POST.get("action")

        # Валидация параметров
        year, consumers, validation_error = validate_time_analysis_parameters(
            request.POST.get("year"),
            request.POST.getlist("consumers"),
            available_consumers,
        )

        if validation_error:
            messages.warning(request, validation_error)
            return render(request, "claims/reclamation_to_claim.html", base_context)

        # Создаем процессор
        processor = TimeAnalysisProcessor(year=year, consumers=consumers)

        if action == "save_files":
            # ОБРАБОТКА СОХРАНЕНИЯ ФАЙЛОВ
            result = processor.save_to_files()

            if result["success"]:
                messages.success(
                    request, f"✅ График сохранен в папку {result['base_dir']}"
                )
            else:
                messages.warning(
                    request, f"❌ Ошибка при сохранении: {result['error']}"
                )

            # Генерируем данные заново и отображаем
            analysis_result = processor.generate_analysis()

            if analysis_result["success"]:
                context = {
                    **base_context,
                    "time_analysis_data": format_analysis_data(analysis_result),
                }
                return render(request, "claims/reclamation_to_claim.html", context)
            else:
                messages.warning(
                    request,
                    f"❌ Ошибка при генерации: {analysis_result.get('error')}",
                )
                return render(request, "claims/reclamation_to_claim.html", base_context)

        else:
            # ОБЫЧНАЯ ГЕНЕРАЦИЯ АНАЛИЗА
            result = processor.generate_analysis()

            if result["success"]:
                context = {
                    **base_context,
                    "time_analysis_data": format_analysis_data(result),
                }
                return render(request, "claims/reclamation_to_claim.html", context)
            else:
                messages.warning(
                    request, f"⚠️ {result.get('error', 'Нет данных для анализа')}"
                )
                return render(request, "claims/reclamation_to_claim.html", base_context)

    # GET запрос - показываем форму
    return render(request, "claims/reclamation_to_claim.html", base_context)


def validate_time_analysis_parameters(year_str, consumers_list, available_consumers):
    """
    Валидация параметров для временного анализа

    Возвращает: (year, consumers, error_message)
    """

    # Валидация года
    try:
        year = int(year_str) if year_str else date.today().year

        if year < 2000 or year > date.today().year:
            return None, None, "Некорректный год"

    except (ValueError, TypeError):
        return None, None, "Некорректный год"

    # Валидация потребителей
    consumers = []
    if consumers_list:
        # Проверяем, что все выбранные потребители существуют
        for consumer in consumers_list:
            if consumer not in available_consumers:
                return None, None, f"Потребитель '{consumer}' не найден"
        consumers = consumers_list
    # Если список пустой - анализируем всех потребителей

    return year, consumers, None


def format_analysis_data(result):
    """Форматирование данных анализа для передачи в шаблон"""
    return {
        "year": int(result["year"]),
        "consumers": result["consumers"],
        "consumer_display": result.get("consumer_display", ""),
        "all_consumers_mode": result.get("all_consumers_mode", False),
        "monthly_data": {
            "labels": result["monthly_data"]["labels"],
            "labels_formatted": result["monthly_data"]["labels_formatted"],
            "reclamations": result["monthly_data"]["reclamations"],
            "claims_counts": result["monthly_data"]["claims_counts"],
            "claims_costs": result["monthly_data"]["claims_costs"],
        },
    }
