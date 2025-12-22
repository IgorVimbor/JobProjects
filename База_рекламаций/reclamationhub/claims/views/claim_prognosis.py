# claims/views/claim_prognosis.py
"""Представление для страницы прогнозирования претензий"""

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
        # Доступные методы для формы
        "forecast_methods": get_forecast_methods(),
    }

    if request.method == "POST":
        action = request.POST.get("action")

        # Получаем параметры методов
        forecast_method = request.POST.get("forecast_method", "statistical")
        statistical_mode = request.POST.get("statistical_mode", "balanced")
        ml_model = request.POST.get("ml_model", "linear")
        seasonal_type = request.POST.get("seasonal_type", "mul")

        # Валидация параметров
        validation_result = validate_prognosis_parameters(
            year_str=request.POST.get("year"),
            consumers_list=request.POST.getlist("consumers"),
            forecast_months_str=request.POST.get("forecast_months"),
            exchange_rate_str=request.POST.get("exchange_rate"),
            forecast_method=forecast_method,
            statistical_mode=statistical_mode,
            ml_model=ml_model,
            seasonal_type=seasonal_type,
            available_years=available_reclamation_years,
            available_consumers=available_consumers,
        )

        if validation_result["error"]:
            messages.error(request, validation_result["error"])
            return render(request, "claims/claim_prognosis.html", base_context)

        # Создаем процессор с параметрами
        processor = ClaimPrognosisProcessor(
            year=validation_result["year"],
            consumers=validation_result["consumers"],
            forecast_months=validation_result["forecast_months"],
            exchange_rate=validation_result["exchange_rate"],
            forecast_method=validation_result["forecast_method"],
            statistical_mode=validation_result["statistical_mode"],
            ml_model=validation_result["ml_model"],
            seasonal_type=validation_result["seasonal_type"],
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


def get_forecast_methods():
    """
    Возвращает доступные методы прогнозирования для формы.

    Returns:
        list[dict]: список методов с параметрами
    """
    return [
        {
            "value": "statistical",
            "label": "Статистический",
            "description": "Скользящее среднее + линейный тренд",
            "has_submethods": True,
            "submethods": [
                {"value": "conservative", "label": "Консервативный"},
                {"value": "balanced", "label": "Сбалансированный", "default": True},
                {"value": "aggressive", "label": "Агрессивный"},
            ],
        },
        {
            "value": "ml",
            "label": "Машинное обучение",
            "description": "Регрессионные модели",
            "has_submethods": True,
            "submethods": [
                {"value": "linear", "label": "Линейная регрессия", "default": True},
                {"value": "ridge", "label": "Ridge регрессия"},
                {"value": "polynomial", "label": "Полиномиальная"},
            ],
        },
        {
            "value": "seasonal",
            "label": "Сезонный",
            "description": "Учитывает сезонные колебания (пики и спады)",
            "has_submethods": True,
            "submethods": [
                {"value": "mul", "label": "Мультипликативный", "default": True},
                {"value": "add", "label": "Аддитивный"},
            ],
        },
        {
            "value": "linked",
            "label": "Связанный",
            "description": "Прогноз претензий на основе рекламаций с учётом временного лага",
            "has_submethods": False,
            "features": [
                "Автоопределение временного лага",
                "Корреляционный анализ",
                "Доверительные интервалы",
            ],
        },
    ]


def validate_prognosis_parameters(
    year_str,
    consumers_list,
    forecast_months_str,
    exchange_rate_str,
    forecast_method,
    statistical_mode,
    ml_model,
    seasonal_type,
    available_years,
    available_consumers,
):
    """
    Валидация параметров для прогнозирования.

    Returns:
        dict: словарь с валидированными параметрами или ошибкой
    """
    result = {
        "year": None,
        "consumers": None,
        "forecast_months": None,
        "exchange_rate": None,
        "forecast_method": None,
        "statistical_mode": None,
        "ml_model": None,
        "seasonal_type": None,
        "error": None,
    }

    # Валидация года
    try:
        year = int(year_str) if year_str else date.today().year

        if year < 2000 or year > date.today().year:
            result["error"] = "Некорректный год"
            return result

        if year not in available_years:
            result["error"] = f"⚠️ Рекламаций за {year} год нет в базе"
            return result

        result["year"] = year

    except (ValueError, TypeError):
        result["error"] = "Некорректный год"
        return result

    # Валидация потребителей
    consumers = []
    if consumers_list:
        for consumer in consumers_list:
            if consumer not in available_consumers:
                result["error"] = f"Потребитель '{consumer}' не найден"
                return result
        consumers = consumers_list
    result["consumers"] = consumers

    # Валидация периода прогноза
    try:
        forecast_months = int(forecast_months_str) if forecast_months_str else 6

        if forecast_months not in [3, 6, 12]:
            result["error"] = "Период прогноза должен быть 3, 6 или 12 месяцев"
            return result

        result["forecast_months"] = forecast_months

    except (ValueError, TypeError):
        result["error"] = "Некорректный период прогноза"
        return result

    # Валидация курса
    try:
        if exchange_rate_str:
            exchange_rate_str = str(exchange_rate_str).replace(",", ".")
            exchange_rate_decimal = Decimal(exchange_rate_str)

            if exchange_rate_decimal <= 0:
                result["error"] = "Курс должен быть положительным числом"
                return result
        else:
            exchange_rate_decimal = Decimal("0.03")

        result["exchange_rate"] = exchange_rate_decimal

    except (ValueError, InvalidOperation):
        result["error"] = "Некорректный курс обмена"
        return result

    # Валидация метода прогнозирования
    valid_methods = ["statistical", "ml", "seasonal", "linked"]
    if forecast_method not in valid_methods:
        forecast_method = "statistical"
    result["forecast_method"] = forecast_method

    # Валидация статистического режима
    valid_modes = ["conservative", "balanced", "aggressive"]
    if statistical_mode not in valid_modes:
        statistical_mode = "balanced"
    result["statistical_mode"] = statistical_mode

    # Валидация ML модели
    valid_models = ["linear", "ridge", "polynomial"]
    if ml_model not in valid_models:
        ml_model = "linear"
    result["ml_model"] = ml_model

    # Валидация типа сезонности
    valid_seasonal_types = ["mul", "add"]
    if seasonal_type not in valid_seasonal_types:
        seasonal_type = "mul"
    result["seasonal_type"] = seasonal_type

    return result


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
        "seasonal": "Сезонный прогноз",
        "linked": "Связанный прогноз",
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

    SEASONAL_TYPES = {
        "mul": "Мультипликативный",
        "add": "Аддитивный",
    }

    # Формируем читабельное название метода
    forecast_method = result["forecast_method"]
    method_name = FORECAST_METHODS.get(forecast_method, forecast_method)

    if forecast_method == "statistical":
        mode_name = STATISTICAL_MODES.get(result.get("statistical_mode"), "")
        forecast_display = f"{method_name} ({mode_name})"
    elif forecast_method == "ml":
        model_name = ML_MODELS.get(result.get("ml_model"), "")
        forecast_display = f"{method_name} ({model_name})"
    elif forecast_method == "seasonal":
        seasonal_type = SEASONAL_TYPES.get(
            result.get("seasonal_type", "mul"), "Мультипликативный"
        )
        forecast_display = f"{method_name} ({seasonal_type})"
    elif forecast_method == "linked":
        lag = result.get("correlation_analysis", {}).get("optimal_lag", "?")
        forecast_display = f"{method_name} (лаг {lag} мес.)"
    else:
        forecast_display = method_name

    # Считаем суммы для карточек
    combined_data = result["combined_data"]
    total_reclamations_forecast = sum(combined_data["reclamations_forecast"])
    total_claims_forecast = sum(combined_data["claims_forecast"])
    total_claims_costs_forecast = sum(combined_data["claims_costs_forecast"])

    # Базовые данные
    formatted_data = {
        "year": result["year"],
        "consumers": result["consumers"],
        "consumer_display": result["consumer_display"],
        "all_consumers_mode": result["all_consumers_mode"],
        "forecast_months": result["forecast_months"],
        "exchange_rate": result["exchange_rate"],
        # Информация о методе
        "forecast_method": forecast_method,
        "statistical_mode": result.get("statistical_mode"),
        "ml_model": result.get("ml_model"),
        "seasonal_type": result.get("seasonal_type", "mul"),
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
            "labels": combined_data["labels"],
            "labels_formatted": combined_data["labels_formatted"],
            "reclamations_fact": combined_data["reclamations_fact"],
            "reclamations_forecast": combined_data["reclamations_forecast"],
            "claims_fact": combined_data["claims_fact"],
            "claims_forecast": combined_data["claims_forecast"],
            "claims_costs_fact": [float(v) for v in combined_data["claims_costs_fact"]],
            "claims_costs_forecast": [
                float(v) for v in combined_data["claims_costs_forecast"]
            ],
            "table_data": combined_data["table_data"],
        },
    }

    # === Добавляем данные для linked метода ===
    if forecast_method == "linked":
        # Доверительные интервалы
        if "claims_costs_ci_lower" in combined_data:
            ci_lower_list = [float(v) for v in combined_data["claims_costs_ci_lower"]]
            ci_upper_list = [float(v) for v in combined_data["claims_costs_ci_upper"]]

            formatted_data["combined_data"]["claims_costs_ci_lower"] = ci_lower_list
            formatted_data["combined_data"]["claims_costs_ci_upper"] = ci_upper_list

            # Суммы CI для карточки
            formatted_data["total_claims_costs_ci_lower"] = sum(ci_lower_list)
            formatted_data["total_claims_costs_ci_upper"] = sum(ci_upper_list)

        # Корреляционный анализ
        if "correlation_analysis" in result:
            formatted_data["correlation_analysis"] = result["correlation_analysis"]

        # Информация о модели
        if "linked_model" in result:
            formatted_data["linked_model"] = result["linked_model"]

    # === Сезонные индексы для seasonal/linked ===
    if forecast_method in ("seasonal", "linked"):
        if "seasonality_pattern" in result:
            month_names = {
                0: "Янв",
                1: "Фев",
                2: "Мар",
                3: "Апр",
                4: "Май",
                5: "Июн",
                6: "Июл",
                7: "Авг",
                8: "Сен",
                9: "Окт",
                10: "Ноя",
                11: "Дек",
            }
            seasonality = result["seasonality_pattern"]
            formatted_data["seasonality_pattern"] = {
                month_names.get(k, k): round(v, 2) for k, v in seasonality.items()
            }

    return formatted_data
