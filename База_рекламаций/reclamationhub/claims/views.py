# AJAX endpoint для получения данных по рекламации в зависимости от результатов поиска.
# Используется в форме добавления/изменения претензии для подстановки данных:
# т.е. при успешном поиске данные по рекламации динамически загружаются в поля формы претензии.

from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from datetime import datetime

from reclamations.models import Reclamation
from investigations.models import Investigation
from .models import Claim


# В нашем случае: AJAX поиск только для сотрудников + только GET запросы.
@staff_member_required  # Проверяет, что пользователь - сотрудник (staff)
@require_http_methods(["GET"])  # Разрешает только GET запросы
# @require_GET - только GET
# @require_POST - только POST
# @require_http_methods(["GET", "POST"]) - GET и POST
def search_related_data(request):
    """Возвращает данные по рекламации по результатам поиска для подстановки в форму претензии"""
    search_number = request.GET.get("reclamation_act_number", "").strip()
    search_date = request.GET.get("reclamation_act_date", "").strip()
    engine_number = request.GET.get("engine_number", "").strip()

    try:
        # 1. Определяем тип поиска - по номеру рекламации или номеру двигателя
        if search_number and search_date and not engine_number:
            search_type = "by_act_number"
            search_value = search_number
        elif engine_number and not search_number and not search_date:
            search_type = "by_engine_number"
            search_value = engine_number
        else:
            return JsonResponse({"found": False})

        # 2. Проверяем существующие претензии (до поиска рекламации!)
        existing_claim_warning = _check_existing_claims_ajax(search_type, search_value)

        # 3. Ищем рекламацию
        if search_type == "by_act_number":
            # Преобразуем дату из DD.MM.YYYY в YYYY-MM-DD
            try:
                search_date_obj = datetime.strptime(search_date, "%d.%m.%Y").date()
            except ValueError:
                return JsonResponse({"found": False, "error": "Неверный формат даты"})

            # Поиск по номеру акта рекламации и соответствующей дате
            reclamation = Reclamation.objects.filter(
                Q(
                    sender_outgoing_number=search_number,
                    message_sent_date=search_date_obj,
                )
                | Q(
                    consumer_act_number=search_number, consumer_act_date=search_date_obj
                )
                | Q(
                    end_consumer_act_number=search_number,
                    end_consumer_act_date=search_date_obj,
                )
            ).first()
        else:  # by_engine_number
            # Поиск по номеру двигателя
            reclamation = Reclamation.objects.filter(
                engine_number=engine_number
            ).first()

        # 4. Если рекламация НЕ найдена, но есть претензия - показываем предупреждение
        if not reclamation:
            if existing_claim_warning:
                return JsonResponse({"found": False, "warning": existing_claim_warning})
            else:
                return JsonResponse({"found": False})

        # 5. Рекламация найдена - ищем связанное исследование (акт исследования)
        try:
            investigation = reclamation.investigation
        except Investigation.DoesNotExist:
            # Рекламация есть, но исследования нет
            if existing_claim_warning:
                return JsonResponse({"found": False, "warning": existing_claim_warning})
            else:
                return JsonResponse({"found": False})

        # 6. Формируем успешный ответ
        response_data = {
            "found": True,
            "message_received_date": reclamation.message_received_date.strftime(
                "%d.%m.%Y"
            ),
            "receipt_invoice_number": reclamation.receipt_invoice_number or "",
            "investigation_act_number": investigation.act_number or "",
            "investigation_act_date": investigation.act_date.strftime("%d.%m.%Y"),
            "investigation_act_result": investigation.get_solution_display() or "",
            "consumer_name": (
                Claim.extract_consumer_prefix(reclamation.defect_period.name)
                if reclamation.defect_period
                else ""
            ),
        }

        # 7. Добавляем специфичные поля в зависимости от типа поиска
        if search_type == "by_act_number":
            # Искали по номеру акта - добавляем номер двигателя
            response_data["engine_number"] = reclamation.engine_number or ""
        elif search_type == "by_engine_number":
            # Искали по двигателю - добавляем номер и дату акта
            # Определяем приоритет: сначала потребитель, потом конечный потребитель, потом отправитель сообщения
            if reclamation.consumer_act_number:
                response_data["reclamation_act_number"] = (
                    reclamation.consumer_act_number
                )
                response_data["reclamation_act_date"] = (
                    reclamation.consumer_act_date.strftime("%d.%m.%Y")
                    if reclamation.consumer_act_date
                    else ""
                )
            elif reclamation.end_consumer_act_number:
                response_data["reclamation_act_number"] = (
                    reclamation.end_consumer_act_number
                )
                response_data["reclamation_act_date"] = (
                    reclamation.end_consumer_act_date.strftime("%d.%m.%Y")
                    if reclamation.end_consumer_act_date
                    else ""
                )
            elif reclamation.sender_outgoing_number:
                response_data["reclamation_act_number"] = (
                    reclamation.sender_outgoing_number
                )
                response_data["reclamation_act_date"] = (
                    reclamation.message_sent_date.strftime("%d.%m.%Y")
                    if reclamation.message_sent_date
                    else ""
                )

        # 8. Добавляем предупреждение о претензии (если есть)
        if existing_claim_warning:
            response_data["warning"] = existing_claim_warning

        return JsonResponse(response_data)

    except Exception as e:
        return JsonResponse({"found": False})


def _check_existing_claims_ajax(search_type, search_value):
    """Проверка существующих претензий для AJAX поиска"""

    if search_type == "by_act_number":
        # 1. Проверяем связанные претензии
        linked_claims = Claim.objects.filter(
            Q(reclamations__sender_outgoing_number=search_value)
            | Q(reclamations__consumer_act_number=search_value)
            | Q(reclamations__end_consumer_act_number=search_value)
        ).distinct()

        # 2. Проверяем несвязанные претензии по полю reclamation_act_number
        unlinked_claims = Claim.objects.filter(
            reclamation_act_number=search_value
        ).exclude(
            id__in=linked_claims.values_list("id", flat=True)  # Исключаем уже найденные
        )

        # Возвращаем первую найденную претензию
        existing_claim = linked_claims.first() or unlinked_claims.first()

    elif search_type == "by_engine_number":
        # Проверяем по номеру двигателя (тут может быть и в reclamations и в поле engine_number)
        existing_claim = (
            Claim.objects.filter(
                Q(engine_number=search_value)
                | Q(reclamations__engine_number=search_value)
            )
            .distinct()
            .first()
        )
    else:
        return None

    if existing_claim:
        return f"⚠️ По этой рекламации уже есть претензия: {existing_claim}"

    return None
