from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from utils.excel.excel_exporter import UniversalExcelExporter


# Список полей для быстрого экспорта
QUICK_EXPORT_FIELDS = [
    "reclamation.id",
    "reclamation.defect_period",
    "reclamation.product_name",
    "reclamation.product",
    "reclamation.products_count",
    "reclamation.manufacture_date",
    "reclamation.claimed_defect",
    "reclamation.mileage_operating_time",
    "investigation.act_number",
    "investigation.defect_causes",
    "investigation.defect_causes_explanation",
]


def get_quick_export_field_names():
    """Метод для получения человекочитаемых названий полей быстрого экспорта"""
    exporter = UniversalExcelExporter()
    field_names = []
    for field_key in QUICK_EXPORT_FIELDS:
        if field_key in exporter.field_config:
            field_names.append(exporter.field_config[field_key]["header"])
    return field_names


@login_required
def excel_exporter_page(request):
    """Страница универсального экспорта данных в Excel"""

    if request.method == "POST":
        return handle_export(request)

    # GET запрос - показываем форму выбора полей
    available_fields = UniversalExcelExporter.get_available_fields()

    # Группируем поля по моделям для удобного отображения
    grouped_fields = {}
    for field in available_fields:
        group = field["group"]
        if group not in grouped_fields:
            grouped_fields[group] = []
        grouped_fields[group].append(field)

    # Получаем названия полей быстрого экспорта
    quick_export_names = get_quick_export_field_names()

    context = {
        "page_title": "Универсальный экспорт данных",
        "description": "Выберите поля для экспорта в Excel файл",
        "grouped_fields": grouped_fields,
        "total_fields": len(available_fields),
        "quick_export_fields": quick_export_names,
        "quick_fields_count": len(quick_export_names),
    }

    return render(request, "utils/excel_exporter.html", context)


def handle_export(request):
    """Обработка экспорта данных"""
    try:
        # Получаем выбранные поля
        selected_fields = request.POST.getlist("selected_fields")

        if not selected_fields:
            messages.warning(request, "⚠️ Выберите хотя бы одно поле для экспорта")
            return redirect("utils:excel_exporter")

        # Валидация полей
        available_fields = [
            field["key"] for field in UniversalExcelExporter.get_available_fields()
        ]
        invalid_fields = [
            field for field in selected_fields if field not in available_fields
        ]

        if invalid_fields:
            messages.warning(
                request, f'❌ Обнаружены некорректные поля: {", ".join(invalid_fields)}'
            )
            return redirect("utils:excel_exporter")

        # Создаем экспортер и генерируем файл
        exporter = UniversalExcelExporter(selected_fields=selected_fields)

        # Вызываем экспорт и проверяем результат
        if exporter.export_to_excel():
            messages.success(request, "✅ Экспорт завершен успешно!")
        else:
            messages.warning(request, "❌ Ошибка при сохранении файла")

        return redirect("utils:excel_exporter")

    except ValueError as e:
        messages.warning(request, f"❌ Ошибка валидации: {str(e)}")
        return redirect("utils:excel_exporter")

    except Exception as e:
        messages.warning(
            request,
            f"❌ Ошибка при экспорте! Возможно у вас открыт файл ЖУРНАЛА РЕКЛАМАЦИЙ. Закройте файл и повторите экспорт.",
        )
        return redirect("utils:excel_exporter")


@login_required
def get_fields_preview(request):
    """AJAX endpoint для предварительного просмотра выбранных полей"""
    if request.method == "POST":
        selected_fields = request.POST.getlist("selected_fields")

        if not selected_fields:
            return JsonResponse({"success": False, "message": "Поля не выбраны"})

        # Получаем информацию о выбранных полях
        exporter = UniversalExcelExporter(selected_fields=selected_fields)
        field_info = []

        for field_key in selected_fields:
            if field_key in exporter.field_config:
                config = exporter.field_config[field_key]
                field_info.append(
                    {
                        "key": field_key,
                        "header": config["header"],
                        "model": config["model"],
                    }
                )

        return JsonResponse(
            {"success": True, "selected_count": len(field_info), "fields": field_info}
        )

    return JsonResponse({"success": False, "message": "Метод не поддерживается"})


# Альтернативный view для быстрого экспорта с предустановленным набором полей
@login_required
def quick_export_reclamations(request):
    """Быстрый экспорт основных полей рекламаций"""
    try:
        # Используем общую константу
        exporter = UniversalExcelExporter(selected_fields=QUICK_EXPORT_FIELDS)

        # Проверяем результат экспорта
        if exporter.export_to_excel():
            messages.success(request, "✅ Быстрый экспорт выполнен успешно!")
        else:
            messages.error(request, "❌ Ошибка при быстром экспорте")

        return redirect("utils:excel_exporter")

    except Exception as e:
        messages.error(
            request,
            f"❌ Ошибка при быстром экспорте! Возможно у вас открыт файл ЖУРНАЛА РЕКЛАМАЦИЙ. Закройте файл и повторите экспорт.",
        )
        return redirect("utils:excel_exporter")
