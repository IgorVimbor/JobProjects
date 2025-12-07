# claims\views\claim_prognosis.py

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

        # Получаем параметры методов
        forecast_method = request.POST.get("forecast_method", "statistical")
        statistical_mode = request.POST.get("statistical_mode", "balanced")
        ml_model = request.POST.get("ml_model", "linear")

        # Валидация параметров
        (
            year,
            consumers,
            forecast_months,
            exchange_rate_decimal,
            forecast_method,
            statistical_mode,
            ml_model,
            validation_error,
        ) = validate_prognosis_parameters(
            request.POST.get("year"),
            request.POST.getlist("consumers"),
            request.POST.get("forecast_months"),
            request.POST.get("exchange_rate"),
            forecast_method,
            statistical_mode,
            ml_model,
            available_reclamation_years,
            available_consumers,
        )

        if validation_error:
            messages.error(request, validation_error)
            return render(request, "claims/claim_prognosis.html", base_context)

        # Создаем процессор с параметрами
        processor = ClaimPrognosisProcessor(
            year=year,
            consumers=consumers,
            forecast_months=forecast_months,
            exchange_rate=exchange_rate_decimal,
            forecast_method=forecast_method,
            statistical_mode=statistical_mode,
            ml_model=ml_model,
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
    forecast_method,
    statistical_mode,
    ml_model,
    available_years,
    available_consumers,
):
    """Валидация параметров для прогнозирования"""

    # Валидация года
    try:
        year = int(year_str) if year_str else date.today().year

        if year < 2000 or year > date.today().year:
            return None, None, None, None, None, None, None, "Некорректный год"

        if year not in available_years:
            return (
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                f"⚠️ Рекламаций за {year} год нет в базе",
            )

    except (ValueError, TypeError):
        return None, None, None, None, None, None, None, "Некорректный год"

    # Валидация потребителей
    consumers = []
    if consumers_list:
        for consumer in consumers_list:
            if consumer not in available_consumers:
                return (
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    f"Потребитель '{consumer}' не найден",
                )
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
                None,
                None,
                None,
                "Период прогноза должен быть 3, 6 или 12 месяцев",
            )

    except (ValueError, TypeError):
        return None, None, None, None, None, None, None, "Некорректный период прогноза"

    # Валидация курса
    try:
        if exchange_rate_str:
            exchange_rate_str = str(exchange_rate_str).replace(",", ".")
            exchange_rate_decimal = Decimal(exchange_rate_str)

            if exchange_rate_decimal <= 0:
                return (
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    "Курс должен быть положительным числом",
                )
        else:
            exchange_rate_decimal = Decimal("0.03")

    except (ValueError, InvalidOperation):
        return None, None, None, None, None, None, None, "Некорректный курс обмена"

    # Валидация метода прогнозирования
    if forecast_method not in ["statistical", "ml"]:
        forecast_method = "statistical"

    # Валидация статистического режима
    if statistical_mode not in ["conservative", "balanced", "aggressive"]:
        statistical_mode = "balanced"

    # Валидация ML модели
    if ml_model not in ["linear", "ridge", "polynomial"]:
        ml_model = "linear"

    return (
        year,
        consumers,
        forecast_months,
        exchange_rate_decimal,
        forecast_method,
        statistical_mode,
        ml_model,
        None,
    )


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

    # Словари для перевода на русский
    FORECAST_METHODS = {
        "statistical": "Скользящее среднее + Тренд",
        "ml": "Машинное обучение",
    }

    STATISTICAL_MODES = {
        "conservative": "Консервативный",
        "balanced": "Сбалансированный",
        "aggressive": "Агрессивный",
    }

    ML_MODELS = {
        "linear": "Линейная регрессия",
        "ridge": "Регуляризованная регрессия",
        "polynomial": "Полиномиальный тренд",
    }

    # Формируем читабельное название метода
    forecast_method = result["forecast_method"]

    if forecast_method == "statistical":
        method_name = FORECAST_METHODS.get(forecast_method, forecast_method)
        mode_name = STATISTICAL_MODES.get(result.get("statistical_mode"), "")
        forecast_display = f"{method_name} ({mode_name})"
    else:  # ml
        method_name = FORECAST_METHODS.get(forecast_method, forecast_method)
        model_name = ML_MODELS.get(result.get("ml_model"), "")
        forecast_display = f"{method_name} ({model_name})"

    # Считаем суммы для карточек
    total_reclamations_forecast = sum(result["combined_data"]["reclamations_forecast"])
    total_claims_forecast = sum(result["combined_data"]["claims_forecast"])
    total_claims_costs_forecast = sum(result["combined_data"]["claims_costs_forecast"])

    return {
        "year": result["year"],
        "consumers": result["consumers"],
        "consumer_display": result["consumer_display"],
        "all_consumers_mode": result["all_consumers_mode"],
        "forecast_months": result["forecast_months"],
        "exchange_rate": result["exchange_rate"],
        # Информация о методе
        "forecast_method": result["forecast_method"],
        "statistical_mode": result.get("statistical_mode"),
        "ml_model": result.get("ml_model"),
        # Читабельное название метода прогнозирования
        "forecast_display": forecast_display,
        # Суммы для карточек
        "total_reclamations_forecast": total_reclamations_forecast,
        "total_claims_forecast": total_claims_forecast,
        "total_claims_costs_forecast": total_claims_costs_forecast,
        # Исторические данные
        "historical": result["historical"],
        # Параметры конверсии
        "conversion_params": result["conversion_params"],
        # Объединенные данные для графика и таблицы
        "combined_data": {
            # Данные для графика
            "labels": result["combined_data"]["labels"],
            "labels_formatted": result["combined_data"]["labels_formatted"],
            "reclamations_fact": result["combined_data"]["reclamations_fact"],
            "reclamations_forecast": result["combined_data"]["reclamations_forecast"],
            "claims_fact": result["combined_data"]["claims_fact"],
            "claims_forecast": result["combined_data"]["claims_forecast"],
            # "claims_costs_fact": result["combined_data"]["claims_costs_fact"],
            "claims_costs_fact": [
                float(v) for v in result["combined_data"]["claims_costs_fact"]
            ],
            # "claims_costs_forecast": result["combined_data"]["claims_costs_forecast"],
            "claims_costs_forecast": [
                float(v) for v in result["combined_data"]["claims_costs_forecast"]
            ],
            # Данные для таблицы
            "table_data": result["combined_data"]["table_data"],
        },
    }
