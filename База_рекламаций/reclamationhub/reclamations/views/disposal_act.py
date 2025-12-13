# reclamations\views\disposal_act.py
"""Представление для формы группового добавления акта утилизации."""

from django.contrib import admin  # Импорт для admin.helpers
from django.http import HttpResponseRedirect
from django.shortcuts import render

from reclamations.models import Reclamation


def add_disposal_act_view(admin_instance, request, queryset):
    """Метод группового добавления акта утилизации"""

    # Если форма отправлена (POST-запрос)
    if "apply" in request.POST:
        disposal_act_number = request.POST.get("disposal_act_number")
        disposal_act_date = request.POST.get("disposal_act_date")

        if not disposal_act_number or not disposal_act_date:
            admin_instance.message_user(
                request,
                "Укажите номер и дату акта утилизации",
                level="ERROR",
            )
            return HttpResponseRedirect(".")

        success_count = 0
        error_count = 0
        no_investigation_count = 0

        for reclamation in queryset:
            if not hasattr(reclamation, "investigation"):
                no_investigation_count += 1
                continue

            try:
                investigation = reclamation.investigation
                investigation.disposal_act_number = disposal_act_number
                investigation.disposal_act_date = disposal_act_date
                investigation.save()
                success_count += 1
            except Exception as e:
                error_count += 1
                admin_instance.message_user(
                    request,
                    f"Ошибка при обновлении акта утилизации для рекламации {reclamation.id}: {str(e)}",
                    level="ERROR",
                )

        if success_count:
            admin_instance.message_user(
                request,
                f"Акт утилизации успешно добавлен для {success_count} рекламации(-ий)",
            )
        if no_investigation_count:
            admin_instance.message_user(
                request,
                f"Пропущено {no_investigation_count} рекламаций без актов исследования",
                level="WARNING",
            )

        return HttpResponseRedirect(".")

    # Если это первый запрос (GET-запрос), показываем форму
    context = {
        "title": "Добавление акта утилизации",
        "reclamations": queryset,
        "count": queryset.count(),
        "opts": Reclamation._meta,
        "action": "add_disposal_act",
        "action_checkbox_name": admin.helpers.ACTION_CHECKBOX_NAME,
    }
    return render(request, "admin/add_disposal_act.html", context)
