# reports/views/culprits_defect.py
# Представление для приложения "Дефекты по виновникам"

from datetime import date
from django.shortcuts import redirect, render
from django.contrib import messages

from reports.modules.culprits_defect_module import CulpritsDefectProcessor


def culprits_defect_page(request):
    """Страница модуля 'Дефекты по виновникам'"""

    if request.method == "POST":
        return generate_analysis(request)

    # GET запрос - показываем актуальную информацию
    report_data = request.session.get("culprits_defect_report_data", None)
    if report_data:
        del request.session["culprits_defect_report_data"]

    # Текущая дата для отображения
    today = date.today()

    context = {
        "page_title": "Дефекты по виновникам",
        "description": "Анализ по виновникам дефектов с разделением по подразделениям",
        "report_data": report_data,
        "current_date": today.strftime("%d.%m.%Y"),
    }
    return render(request, "reports/culprits_defect.html", context)


def generate_analysis(request):
    """Генерация анализа по виновникам"""

    # Получаем номер акта исследования
    user_number = request.POST.get("user_number")

    # Валидация номера акта
    try:
        user_number = int(user_number) if user_number else None
        if user_number is None:
            messages.warning(request, "Необходимо указать номер акта исследования")
            return redirect("reports:culprits_defect")

        if user_number < 0:
            messages.warning(request, "Номер акта должен быть неотрицательным числом")
            return redirect("reports:culprits_defect")

    except (ValueError, TypeError):
        messages.warning(request, "Некорректный номер акта исследования")
        return redirect("reports:culprits_defect")

    # Запускаем анализ
    processor = CulpritsDefectProcessor(user_number=user_number)
    result = processor.generate_analysis()

    if result["success"]:
        messages.success(request, f"✅ {result['message']}")
        request.session["culprits_defect_report_data"] = {
            "bza_data": result["bza_data"],
            "not_bza_data": result["not_bza_data"],
            "bza_count": result["bza_count"],
            "not_bza_count": result["not_bza_count"],
            "max_act_number": result.get("max_act_number"),
            "start_act_number": user_number + 1,
        }
    else:
        if result["message_type"] == "info":
            messages.info(request, result["message"])
        else:
            messages.warning(request, result["message"])

    return redirect("reports:culprits_defect")
