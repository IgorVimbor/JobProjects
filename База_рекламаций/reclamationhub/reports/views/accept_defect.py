# reports/views/accept_defect.py
# Представление для приложения "Количество признанных/непризнанных"

# render - для HTML страниц. Результат: Браузер показывает веб-страницу
# redirect - для HTML страниц. Результат: обновляет страницу с новыми данными
# HttpResponse - для файлов и данных. Результат: Браузер скачивает файл

from datetime import datetime
from django.http import FileResponse
from django.shortcuts import redirect, render
from django.contrib import messages
import os

from reports.modules.accept_defect_module import AcceptDefectProcessor
from reclamations.models import Reclamation


def accept_defect_page(request):
    """Страница модуля 'Количество признанных/непризнанных рекламаций'"""

    if request.method == "POST":
        return generate_report(request)

    # GET запрос - показываем актуальную информацию
    download_info = request.session.get("accept_defect_download_info", None)
    # Проверяем, есть ли актуальная данные
    if download_info:
        del request.session["accept_defect_download_info"]

    # Получаем доступные годы для селектора
    available_years = list(
        Reclamation.objects.values_list("year", flat=True).distinct().order_by("-year")
    )

    # Список месяцев по кварталам
    months_by_quarters = [
        {
            "title": "I квартал",
            "months": [
                {"value": 1, "name": "Январь"},
                {"value": 2, "name": "Февраль"},
                {"value": 3, "name": "Март"},
            ],
        },
        {
            "title": "II квартал",
            "months": [
                {"value": 4, "name": "Апрель"},
                {"value": 5, "name": "Май"},
                {"value": 6, "name": "Июнь"},
            ],
        },
        {
            "title": "III квартал",
            "months": [
                {"value": 7, "name": "Июль"},
                {"value": 8, "name": "Август"},
                {"value": 9, "name": "Сентябрь"},
            ],
        },
        {
            "title": "IV квартал",
            "months": [
                {"value": 10, "name": "Октябрь"},
                {"value": 11, "name": "Ноябрь"},
                {"value": 12, "name": "Декабрь"},
            ],
        },
    ]

    context = {
        "page_title": "% Признанных рекламаций",
        "description": "Отчет по количеству признанных/непризнанных рекламаций по потребителям и изделиям",
        "download_info": download_info,
        "available_years": available_years,
        "current_year": datetime.now().year,
        "months_by_quarters": months_by_quarters,
    }
    return render(request, "reports/accept_defect.html", context)


def generate_report(request):
    """Генерация отчета"""
    # Получаем год из POST данных
    year = request.POST.get("year")

    # Получаем выбранные месяцы из чекбоксов
    selected_months = request.POST.getlist("months")  # Список строк ['1', '2', '3']

    try:
        year = int(year) if year else datetime.now().year
    except (ValueError, TypeError):
        messages.error(request, "Некорректный год")
        return redirect("reports:accept_defect")

    # Умная валидация месяцев
    months = []
    if selected_months:
        try:
            months = [int(month) for month in selected_months if month.isdigit()]
            # Проверка данных - фильтруем только валидные месяцы (1-12)
            months = [month for month in months if 1 <= month <= 12]
            # Проверка делается для защиты от действий злоумышленников: модификация HTML, прямые POST запросы, JavaScript атаки

            # ДОБАВЛЯЕМ ПРОВЕРКУ НА ЛОГИЧНОСТЬ МЕСЯЦЕВ
            current_date = datetime.now()
            current_year = current_date.year
            current_month = current_date.month

            # Первый if - защита от действий злоумышленников с запросами с будущим годом.
            # Например: модификации HTML (добавить <option value="2030">2030</option>), прямые POST запросы
            if year > current_year:
                # Будущий год - нет данных
                messages.error(
                    request, f"Нельзя формировать отчет за будущий {year} год"
                )
                return redirect("reports:accept_defect")
            # Защиту по году можно убрать, тогда ниже не elif, а if
            elif year == current_year:
                # Текущий год - месяцы не должны быть больше текущего
                future_months = [month for month in months if month > current_month]
                if future_months:
                    month_names = {
                        1: "январь",
                        2: "февраль",
                        3: "март",
                        4: "апрель",
                        5: "май",
                        6: "июнь",
                        7: "июль",
                        8: "август",
                        9: "сентябрь",
                        10: "октябрь",
                        11: "ноябрь",
                        12: "декабрь",
                    }
                    future_names = [
                        month_names[month] for month in sorted(future_months)
                    ]

                    if len(future_names) == 1:
                        msg = f"❌ Месяц {future_names[0]} {year} года еще не наступил"
                    else:
                        msg = f"❌ Месяцы {', '.join(future_names)} {year} года еще не наступили"

                    messages.error(request, msg)
                    return redirect("reports:accept_defect")
            # Для прошлых лет (year < current_year) - любые месяцы валидны

        except (ValueError, TypeError):
            messages.error(request, "Некорректные месяцы")
            return redirect("reports:accept_defect")

    # Если не выбрано ни одного месяца - обрабатываем весь год
    processor = AcceptDefectProcessor(year=year, months=months)
    result = processor.generate_report()

    if result["success"]:
        messages.success(request, f"✅ {result['message']}")
        request.session["accept_defect_download_info"] = {
            "message": result["full_message"],
            "report_data": result["report_data"],
            "period_text": result.get(
                "period_text", f"{year} год"
            ),  # Для отображения периода
        }
    else:
        if result["message_type"] == "info":
            messages.info(request, result["message"])
        else:
            messages.error(request, result["message"])

    return redirect("reports:accept_defect")


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
