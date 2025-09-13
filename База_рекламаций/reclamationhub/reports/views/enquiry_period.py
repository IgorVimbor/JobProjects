# reports/views/enquiry_period.py
# Представление для приложения "Справка за период"

# render - для HTML страниц. Результат: Браузер показывает веб-страницу
# redirect - для HTML страниц. Результат: обновляет страницу с новыми данными
# HttpResponse - для файлов и данных. Результат: Браузер скачивает файл

from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import FileResponse, Http404
from reports.modules.enquiry_period_module import ExcelWriter
from reports.models import EnquiryPeriod
from reclamations.models import Reclamation
import os


def enquiry_period_page(request):
    """Страница модуля справки за период"""

    if request.method == "POST":
        return generate_report(request)

    # Получаем информацию для отображения (GET запрос - показываем страницу)
    last_metadata = EnquiryPeriod.objects.order_by("-sequence_number").first()

    # Считаем количество новых записей
    last_processed_id = last_metadata.last_processed_id if last_metadata else 0
    new_records_count = Reclamation.objects.filter(id__gt=last_processed_id).count()

    # Проверяем, есть ли актуальная данные для справки
    download_info = request.session.get("download_info", None)
    # if download_info:
    #     del request.session["download_info"]

    context = {
        "page_title": "Справка за период",
        "description": "Справка по количеству поступивших рекламаций за период времени",
        "last_metadata": last_metadata,
        "new_records_count": new_records_count,
        "download_info": download_info,  # актуальная данные для справки
    }
    return render(request, "reports/enquiry_period.html", context)


def generate_report(request):
    """Обертка для представления результата генерации справки модулем enquiry_period_module"""
    # Вся логика в модуле enquiry_period_module
    writer = ExcelWriter()
    result = writer.generate_full_report()

    # Обрабатываем результат
    if result["success"]:
        messages.success(request, f"✅ {result['message']}")
        request.session["download_info"] = {
            "message": result["full_message"],
            "excel_path": result["excel_path"],
            "filename": result["filename"],
        }
    else:
        # Определяем тип сообщения
        if result["message_type"] == "info":
            messages.info(request, result["message"])
        elif result["message_type"] == "warning":
            messages.warning(request, result["message"])  # ← Добавляем warning
        else:
            messages.error(request, result["message"])

    # Редирект для обновления страницы с новыми данными
    return redirect("reports:enquiry_period")


def download_excel(request):
    """Скачивание Excel файла"""
    download_info = request.session.get("download_info")

    if not download_info:
        messages.error(request, "Файл для скачивания не найден")
        return redirect("reports:enquiry_period")

    excel_path = download_info.get("excel_path")
    filename = download_info.get("filename")

    if os.path.exists(excel_path):
        # Убираем информацию о файле из сессии после скачивания
        if download_info:
            del request.session["download_info"]

        return FileResponse(
            open(excel_path, "rb"), as_attachment=True, filename=filename
        )
    else:
        messages.error(request, "Файл отчета не найден на диске")
        return redirect("reports:enquiry_period")
