# reports/views/length_study.py
# Представление для приложения "Длительность исследований"

# render - для HTML страниц. Результат: Браузер показывает веб-страницу
# redirect - для HTML страниц. Результат: обновляет страницу с новыми данными
# HttpResponse - для файлов и данных. Результат: Браузер скачивает файл

from django.shortcuts import render, redirect
from django.contrib import messages
from reports.modules.length_study_module import LengthStudyProcessor


def length_study_page(request):
    """Страница модуля анализа длительности исследований"""

    if request.method == "POST":
        return generate_report(request)

    # GET запрос - показываем страницу
    download_info = request.session.get("length_study_info", None)
    if download_info:
        del request.session["length_study_info"]

    context = {
        "page_title": "Длительность исследования",
        "description": "Анализ длительности исследований с расчетом среднего и медианного значений и построением гистограмм",
        "download_info": download_info,
    }
    return render(request, "reports/length_study.html", context)


def generate_report(request):
    """Генерация отчета"""
    processor = LengthStudyProcessor()
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
