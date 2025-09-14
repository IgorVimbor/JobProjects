# reports/views/accept_defect.py
# Представление для приложения "Количество признанных/непризнанных"

# render - для HTML страниц. Результат: Браузер показывает веб-страницу
# redirect - для HTML страниц. Результат: обновляет страницу с новыми данными
# HttpResponse - для файлов и данных. Результат: Браузер скачивает файл

from django.http import FileResponse
from django.shortcuts import redirect, render
from django.contrib import messages
import os

from reports.modules.accept_defect_module import AcceptDefectProcessor


def accept_defect_page(request):
    """Страница модуля 'Количество признанных/непризнанных рекламаций'"""

    if request.method == "POST":
        return generate_report(request)

    # GET запрос - показываем актуальную информацию
    download_info = request.session.get("accept_defect_download_info", None)
    # Проверяем, есть ли актуальная данные
    if download_info:
        del request.session["accept_defect_download_info"]

    context = {
        "page_title": "Признанные/непризнанные рекламации",
        "description": "Отчет по количеству признанных/непризнанных рекламаций по потребителям и изделиям",
        "download_info": download_info,
    }
    return render(request, "reports/accept_defect.html", context)


def generate_report(request):
    """Генерация отчета"""
    processor = AcceptDefectProcessor()
    result = processor.generate_report()

    if result["success"]:
        messages.success(request, f"✅ {result['message']}")
        request.session["accept_defect_download_info"] = {
            "message": result["full_message"],  # Убираем txt_path и filename
            "report_data": result["report_data"],  # ← Добавляем данные для показа
        }
    else:
        if result["message_type"] == "info":
            messages.info(request, result["message"])
        else:
            messages.error(request, result["message"])

    return redirect("reports:accept_defect")


# Убираем функцию download_txt полностью!
# def download_txt(request):
#     """Скачивание TXT файла"""
#     download_info = request.session.get("accept_defect_download_info")

#     if not download_info:
#         messages.error(request, "Файл для скачивания не найден")
#         return redirect("reports:accept_defect")

#     txt_path = download_info.get("txt_path")
#     filename = download_info.get("filename")

#     if os.path.exists(txt_path):
#         if "accept_defect_download_info" in request.session:
#             del request.session["accept_defect_download_info"]

#         return FileResponse(open(txt_path, "rb"), as_attachment=True, filename=filename)
#     else:
#         messages.error(request, "Файл отчета не найден на диске")
#         return redirect("reports:accept_defect")
