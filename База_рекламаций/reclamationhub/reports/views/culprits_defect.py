# reports/views/culprits_defect.py
# Представление для приложения "Дефекты по виновникам"

from datetime import date
from django.shortcuts import redirect, render
from django.contrib import messages

from reports.modules.culprits_defect_module import CulpritsDefectProcessor


def culprits_defect_page(request):
    """Страница модуля 'Дефекты по виновникам'"""

    def clear_session_data():
        """Вспомогательная функция для очистки данных"""
        if "culprits_defect_report_data" in request.session:
            del request.session["culprits_defect_report_data"]

    if request.method == "POST":
        return generate_analysis(request)

    # Проверяем параметр clear
    if request.GET.get("clear") == "1":
        clear_session_data()  # очищаем сессию (старые данные)
        # Перенаправляем без параметра clear
        return redirect("reports:culprits_defect")

    # Проверяем, откуда пришел пользователь
    referer = request.META.get("HTTP_REFERER", "")
    current_url = request.build_absolute_uri()

    # Если пользователь пришел НЕ с этой же страницы - очищаем данные
    if referer and not referer.startswith(current_url.split("?")[0]):
        # Пришел с другой страницы - очищаем старые данные
        clear_session_data()

    # GET запрос - показываем данные БЕЗ удаления
    report_data = request.session.get("culprits_defect_report_data", None)

    # Текущая дата для отображения
    today = date.today()
    # Определяем отчетные месяц и год для отображения из класса CulpritsDefectProcessor
    obj = CulpritsDefectProcessor()
    report_month = obj.month_name  # Отчетный месяц (предыдущий)
    report_year = obj.analysis_year  # Отчетный год

    context = {
        "page_title": "Дефекты по виновникам",
        "description": "Справка по виновникам дефектов с разделением по подразделениям",
        "report_data": report_data,
        "current_date": today.strftime("%d.%m.%Y"),
        "report_month": report_month,
        "report_year": report_year,
    }
    return render(request, "reports/culprits_defect.html", context)


def generate_analysis(request):
    """Генерация анализа по виновникам"""

    action = request.POST.get("action")

    # СОХРАНЕНИЕ В ФАЙЛ (из готовых данных в сессии)
    if action == "save_files":
        # Получаем готовые данные из сессии
        report_data = request.session.get("culprits_defect_report_data", {})

        if not report_data:
            messages.warning(
                request, "Нет данных для сохранения. Сначала сгенерируйте анализ."
            )
            return redirect("reports:culprits_defect")

        # Создаем процессор для сохранения
        processor = CulpritsDefectProcessor()

        # Сохраняем готовые данные в Excel
        save_result = processor.save_to_excel_from_data(
            bza_data=report_data["bza_data"],
            not_bza_data=report_data["not_bza_data"],
            start_act_number=report_data["start_act_number"],
        )

        if save_result["success"]:
            messages.success(request, save_result["full_message"])
        else:
            if save_result["message_type"] == "warning":
                messages.warning(request, save_result["message"])
            else:
                messages.error(request, save_result["message"])

        return redirect("reports:culprits_defect")

    # ------------- ОБЫЧНАЯ ГЕНЕРАЦИЯ АНАЛИЗА ---------------

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
