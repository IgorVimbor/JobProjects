# reclamations\views\reclamation_form.py
"""
AJAX endpoint для проверки дубликатов рекламаций.
Проверяет каждое поле отдельно и возвращает предупреждение если найден дубликат.
"""

from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_http_methods

from reclamations.models import Reclamation


@staff_member_required
@require_http_methods(["POST"])
def check_duplicate_reclamations_ajax(request):
    """
    AJAX проверка дубликатов рекламаций по одному полю.

    Принимает:
        field_name: название поля для проверки
        field_value: значение поля
        current_reclamation_id: ID текущей рекламации (для исключения при редактировании)

    Возвращает:
        JSON с результатом проверки и предупреждением если найден дубликат
    """

    # Получаем данные из POST запроса
    field_name = request.POST.get("field_name", "").strip()
    field_value = request.POST.get("field_value", "").strip()
    current_id = request.POST.get("current_reclamation_id")

    # Если поле или значение пустые - дубликатов нет
    if not field_name or not field_value:
        return JsonResponse({"duplicate_found": False})

    try:
        # Проверяем дубликат по конкретному полю
        duplicate_info = _check_single_field_duplicate(
            field_name, field_value, current_id
        )

        if duplicate_info:
            return JsonResponse(
                {"duplicate_found": True, "warning": duplicate_info["warning"]}
            )

        return JsonResponse({"duplicate_found": False})

    except Exception as e:
        # В случае ошибки возвращаем безопасный ответ
        return JsonResponse(
            {"duplicate_found": False, "error": "Ошибка проверки дубликатов"}
        )


def _check_single_field_duplicate(field_name, field_value, exclude_id=None):
    """
    Проверка дубликата по одному конкретному полю.

    Args:
        field_name (str): Название поля для проверки
        field_value (str): Значение поля
        exclude_id (str|None): ID рекламации для исключения из поиска

    Returns:
        dict|None: Информация о найденном дубликате или None
    """

    # Список разрешенных полей для проверки (защита от инъекций)
    allowed_fields = [
        "sender_outgoing_number",  # Номер ПСА отправителя
        "product_number",  # Номер изделия
        "consumer_act_number",  # Номер акта приобретателя
        "end_consumer_act_number",  # Номер акта конечного потребителя
        "engine_number",  # Номер двигателя
    ]

    # Проверяем что поле разрешено для поиска
    if field_name not in allowed_fields:
        return None

    # Создаем динамический фильтр для конкретного поля
    # Например: {'product_number': '123'} превратится в filter(product_number='123')
    filter_kwargs = {field_name: field_value}

    # Выполняем оптимизированный запрос к БД
    queryset = Reclamation.objects.filter(**filter_kwargs).only(
        "id",
        "year",
        "yearly_number",  # Загружаем только нужные поля для производительности
    )

    # Исключаем текущую рекламацию при редактировании
    if exclude_id:
        queryset = queryset.exclude(id=exclude_id)

    # Получаем первый найденный дубликат
    duplicate = queryset.first()

    if duplicate:
        # Словарь для человекочитаемых названий полей
        field_labels = {
            "sender_outgoing_number": "номером ПСА",
            "product_number": "номером изделия",
            "consumer_act_number": "номером акта приобретателя",
            "end_consumer_act_number": "номером акта конечного потребителя",
            "engine_number": "номером двигателя",
        }

        # Формируем номер рекламации в формате YYYY-NNNN
        reclamation_number = f"{duplicate.year}-{duplicate.yearly_number:04d}"

        return {
            "warning": f"⚠️ С {field_labels[field_name]} '{field_value}' уже есть рекламация: {reclamation_number}"
        }

    return None
