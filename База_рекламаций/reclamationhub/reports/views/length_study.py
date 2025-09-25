# reports/views/length_study.py
# Представление для приложения "Длительность исследований"

# render - для HTML страниц. Результат: Браузер показывает веб-страницу
# redirect - для HTML страниц. Результат: обновляет страницу с новыми данными
# HttpResponse - для файлов и данных. Результат: Браузер скачивает файл

from datetime import datetime
from django.shortcuts import render, redirect
from django.contrib import messages
from reports.modules.length_study_module import LengthStudyProcessor
from reclamations.models import Reclamation  # ДОБАВИЛИ импорт


def length_study_page(request):
    """Страница модуля анализа длительности исследований"""

    if request.method == "POST":
        return generate_report(request)

    # GET запрос - показываем страницу
    download_info = request.session.get("length_study_info", None)
    if download_info:
        del request.session["length_study_info"]

    # Получаем доступные годы
    available_years = list(
        Reclamation.objects.values_list("year", flat=True).distinct().order_by("-year")
    )

    # Список потребителей
    available_consumers = [
        {"value": "ММЗ", "name": "ММЗ"},
        {"value": "Гомсельмаш", "name": "Гомсельмаш"},
        {"value": "МАЗ", "name": "МАЗ"},
        {"value": "ЯМЗ", "name": "ЯМЗ"},
        {"value": "ПАЗ", "name": "ПАЗ"},
        {"value": "Ростсельмаш", "name": "Ростсельмаш"},
        {"value": "КАМАЗ", "name": "КАМАЗ"},
        {"value": "УРАЛ", "name": "УРАЛ"},
        {"value": "ПТЗ", "name": "ПТЗ"},
    ]

    context = {
        "page_title": "Длительность исследования",
        "description": "Анализ длительности исследований с расчетом среднего и медианного значений и построением гистограмм",
        "download_info": download_info,
        "available_years": available_years,  # Доступные годы
        "current_year": datetime.now().year,  # Текущий год
        "available_consumers": available_consumers,  # Список потребителей
    }
    return render(request, "reports/length_study.html", context)


def generate_report(request):
    """Генерация отчета"""
    # Получаем год из POST данных
    year = request.POST.get("year")

    # Получаем потребителей
    selected_consumers = request.POST.getlist("consumers")

    try:
        year = int(year) if year else datetime.now().year
    except (ValueError, TypeError):
        messages.error(request, "Некорректный год")
        return redirect("reports:length_study")

    # Простая валидация потребителей
    consumers = []
    if selected_consumers:
        valid_consumers = [
            "ММЗ",
            "Гомсельмаш",
            "МАЗ",
            "ЯМЗ",
            "ПАЗ",
            "Ростсельмаш",
            "КАМАЗ",
            "УРАЛ",
            "ПТЗ",
        ]
        consumers = [c for c in selected_consumers if c in valid_consumers]

    # Создаем экземпляр класса LengthStudyProcessor с выбранным годом и пользователями
    processor = LengthStudyProcessor(year=year, consumers=consumers)
    result = processor.generate_report()

    if result["success"]:
        messages.success(request, f"✅ {result['message']}")
        request.session["length_study_info"] = {
            "message": result["full_message"],
            "table_data": result["table_data"],
            "plot_base64": result["plot_base64"],
        }
    else:
        if result["message_type"] == "info":
            messages.info(request, result["message"])
        else:
            messages.error(request, result["message"])

    return redirect("reports:length_study")
