# reports/views/culprits_defect.py
# Представление для приложения "Дефекты по виновникам"

from datetime import date
from django.shortcuts import redirect, render
from django.contrib import messages

from reports.modules.culprits_defect_module import CulpritsDefectProcessor


# Названия месяцев
MONTH_NAMES = {
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
    # Отчетные месяц и год для отображения
    report_month = date.today().month - 1  # текущий месяц минус 1, т.е. предыдущий
    today_year = date.today().year
    # Если текущий месяц не январь, то год текущий. Иначе (текущий месяц январь), то
    # год предыдущий,т.к. делаем справку за декабрь.
    report_year = today_year if report_month != 1 else today_year - 1

    context = {
        "page_title": "Дефекты по виновникам",
        "description": "Справка по виновникам дефектов с разделением по подразделениям",
        "report_data": report_data,
        "current_date": today.strftime("%d.%m.%Y"),
        "report_month": MONTH_NAMES[report_month],
        "report_year": report_year,
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
