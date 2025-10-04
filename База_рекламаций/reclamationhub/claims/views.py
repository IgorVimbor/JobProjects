from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_http_methods
from django.db import models

from reclamations.models import Reclamation
from investigations.models import Investigation


@staff_member_required
@require_http_methods(["GET"])
def search_related_data(request):
    search_number = request.GET.get("reclamation_act_number", "").strip()
    search_date = request.GET.get("reclamation_act_date", "").strip()
    engine_number = request.GET.get("engine_number", "").strip()

    reclamation = None
    search_type = ""

    try:
        # Определяем тип поиска и ищем рекламацию
        if search_number and search_date and not engine_number:
            # Поиск по номеру и дате рекламационного акта
            search_type = "by_act_number"
            reclamation = Reclamation.objects.filter(
                models.Q(sender_outgoing_number=search_number)
                | models.Q(consumer_act_number=search_number)
                | models.Q(end_consumer_act_number=search_number)
            ).first()

        elif engine_number and not search_number and not search_date:
            # Поиск по номеру двигателя
            search_type = "by_engine_number"
            reclamation = Reclamation.objects.filter(
                engine_number=engine_number
            ).first()

        # Если условия не выполнены - просто ничего не делаем
        if not reclamation:
            return JsonResponse({"found": False})

        # Получаем связанное исследование через OneToOne
        try:
            investigation = reclamation.investigation
        except Investigation.DoesNotExist:
            return JsonResponse({"found": False})

        # Формируем ответ в зависимости от типа поиска
        response_data = {
            "found": True,
            "message_received_date": reclamation.message_received_date.strftime(
                "%d.%m.%Y"
            ),
            "investigation_act_number": investigation.act_number or "",
            "investigation_act_date": investigation.act_date.strftime("%d.%m.%Y"),
            "investigation_act_result": investigation.get_solution_display() or "",
            "message": "Данные найдены и заполнены автоматически",
        }

        # Добавляем специфичные поля в зависимости от типа поиска
        if search_type == "by_act_number":
            # Искали по номеру акта - добавляем номер двигателя
            response_data["engine_number"] = reclamation.engine_number or ""

        elif search_type == "by_engine_number":
            # Искали по двигателю - добавляем номер и дату акта
            # Определяем приоритет: сначала потребитель, потом конечный потребитель, потом отправитель
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
            else:
                response_data["reclamation_act_number"] = ""
                response_data["reclamation_act_date"] = ""

        return JsonResponse(response_data)

    except Exception as e:
        return JsonResponse({"found": False, "message": f"Ошибка поиска: {str(e)}"})
