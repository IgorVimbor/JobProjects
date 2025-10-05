from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_http_methods
from django.db.models import Q

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
    search_number = request.GET.get("reclamation_act_number", "").strip()
    search_date = request.GET.get("reclamation_act_date", "").strip()
    engine_number = request.GET.get("engine_number", "").strip()

    try:
        # 1. Определяем тип поиска и ищем рекламацию
        if search_number and search_date and not engine_number:
            # Поиск по номеру и дате рекламационного акта
            search_type = "by_act_number"
            reclamation = Reclamation.objects.filter(
                Q(sender_outgoing_number=search_number)
                | Q(consumer_act_number=search_number)
                | Q(end_consumer_act_number=search_number)
            ).first()
        elif engine_number and not search_number and not search_date:
            # Поиск по номеру двигателя
            search_type = "by_engine_number"
            reclamation = Reclamation.objects.filter(
                engine_number=engine_number
            ).first()
        else:
            return JsonResponse({"found": False})

        # 2. Проверяем, найдена ли рекламация
        if not reclamation:  # Если условия не выполнены - просто ничего не делаем
            return JsonResponse({"found": False})

        # 3. Ищем связанное исследование (акт исследования)
        try:
            investigation = reclamation.investigation
        except Investigation.DoesNotExist:
            return JsonResponse({"found": False})

        # 4. Проверяем дублирование претензий
        existing_claims = Claim.objects.filter(reclamation=reclamation)

        # 5. Формируем базовый ответ по найденной информации
        response_data = {
            "found": True,
            "message_received_date": reclamation.message_received_date.strftime(
                "%d.%m.%Y"
            ),
            "receipt_invoice_number": reclamation.receipt_invoice_number or "",
            "investigation_act_number": investigation.act_number or "",
            "investigation_act_date": investigation.act_date.strftime("%d.%m.%Y"),
            "investigation_act_result": investigation.get_solution_display() or "",
        }

        # 6. Добавляем специфичные поля в зависимости от типа поиска
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

        # 7. Добавляем предупреждение о дублировании
        if existing_claims.exists():
            claims_info = []
            for claim in existing_claims:
                if claim.claim_number and claim.claim_date:
                    claims_info.append(
                        f"№{claim.claim_number} от {claim.claim_date.strftime('%d.%m.%Y')}"
                    )
                else:
                    claims_info.append("без номера")

            response_data["warning"] = (
                f"⚠️ По этой рекламации уже есть претензия: {', '.join(claims_info)}"
            )

        return JsonResponse(response_data)

    except Exception as e:
        return JsonResponse({"found": False})
