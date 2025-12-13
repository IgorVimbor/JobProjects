# utils\views.py
"""Представление для страницы экспортера в Excel данных из базы данных"""

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from reclamations.models import Reclamation
from utils.modules.excel_exporter import UniversalExcelExporter
from reports.config.paths import BASE_REPORTS_DIR


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
    "investigation.solution",
    "investigation.defect_causes",
    "investigation.defect_causes_explanation",
]


def get_quick_export_field_names():
    """Метод для получения человекочитаемых названий полей быстрого экспорта"""
    exporter = UniversalExcelExporter()
    field_names = []
    for field_key in QUICK_EXPORT_FIELDS:
        if field_key in exporter.field_config:
            field_names.append(exporter.field_config[field_key][0])  # [0] - заголовок
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

    # Получаем доступные годы
    available_years = ["all"] + list(
        Reclamation.objects.values_list("year", flat=True).distinct().order_by("-year")
    )

    # Получаем названия полей быстрого экспорта
    quick_export_names = get_quick_export_field_names()

    context = {
        "page_title": "Универсальный экспорт данных",
        "description": "✅ Для экспорта в Excel файл выберите столбцы или воспользуйтесь быстрым экспортом с предустановленным набором столбцов",
        "grouped_fields": grouped_fields,
        "total_fields": len(available_fields),
        "quick_export_fields": quick_export_names,
        "quick_fields_count": len(quick_export_names),
        "available_years": available_years,
        "current_year": "all",  # По умолчанию все годы
    }

    return render(request, "utils/excel_exporter.html", context)


def handle_export(request):
    """Обработка экспорта данных"""
    try:
        # Получаем выбранные поля
        selected_fields = request.POST.getlist("selected_fields")
        year = request.POST.get("year")  # Получаем выбранный год

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

        # Валидация года
        available_years = ["all"] + list(
            Reclamation.objects.values_list("year", flat=True).distinct()
        )
        if year not in [str(y) for y in available_years]:
            messages.warning(request, "❌ Некорректный год")
            return redirect("utils:excel_exporter")

        # Преобразуем year для передачи в экспортер
        export_year = None if year == "all" else int(year)

        # Создаем экспортер с годом и генерируем файл
        exporter = UniversalExcelExporter(
            selected_fields=selected_fields, year=export_year
        )

        # Вызываем экспорт и проверяем результат
        if exporter.export_to_excel():
            year_text = "все годы" if year == "all" else f"{year} год"
            messages.success(request, f"✅ Экспорт за {year_text} завершен успешно!")
            messages.success(
                request,
                f"✅ Файл ЖУРНАЛ УЧЕТА_{year_text}.xlsx находится в папке {BASE_REPORTS_DIR}",
            )
        else:
            messages.warning(request, "❌ Ошибка при сохранении файла")

        return redirect("utils:excel_exporter")

    except ValueError as e:
        messages.warning(request, f"❌ Ошибка валидации: {str(e)}")
        return redirect("utils:excel_exporter")

    except Exception as e:
        # # ВРЕМЕННО: выводим реальную ошибку для отладки
        # print(f"Реальная ошибка экспорта: {e}")
        # import traceback
        # traceback.print_exc()
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
                # Распаковываем кортеж
                header, field_type = exporter.field_config[field_key]
                model = field_key.split(".")[0]  # Извлекаем модель из ключа

                field_info.append(
                    {
                        "key": field_key,
                        "header": header,  # Используем распакованный заголовок
                        "model": model,  # Используем извлеченную модель
                    }
                )

        return JsonResponse(
            {"success": True, "selected_count": len(field_info), "fields": field_info}
        )

    return JsonResponse({"success": False, "message": "Метод не поддерживается"})


# view для быстрого экспорта с предустановленным набором полей
@login_required
def quick_export_reclamations(request):
    """Быстрый экспорт данных из предустановленных полей"""
    try:
        # Получаем год из GET параметров или используем текущий
        year = request.GET.get("year", "all")
        export_year = None if year == "all" else int(year)

        # Создаем экспортер с годом используя общую константу
        exporter = UniversalExcelExporter(
            selected_fields=QUICK_EXPORT_FIELDS, year=export_year
        )

        # Проверяем результат экспорта
        if exporter.export_to_excel():
            year_text = "все годы" if year == "all" else f"{year} год"
            messages.success(
                request, f"✅ Быстрый экспорт за {year_text} выполнен успешно!"
            )
            messages.success(
                request,
                f"✅ Файл ЖУРНАЛ УЧЕТА_{year_text}.xlsx находится в папке {BASE_REPORTS_DIR}",
            )
        else:
            messages.warning(request, "❌ Ошибка при быстром экспорте")

        return redirect("utils:excel_exporter")

    except Exception as e:
        # # ВРЕМЕННО: выводим реальную ошибку для отладки
        # print(f"Реальная ошибка экспорта: {e}")
        # import traceback
        # traceback.print_exc()
        messages.warning(
            request,
            f"❌ Ошибка при быстром экспорте! Возможно у вас открыт файл ЖУРНАЛА РЕКЛАМАЦИЙ. Закройте файл и повторите экспорт.",
        )
        return redirect("utils:excel_exporter")
