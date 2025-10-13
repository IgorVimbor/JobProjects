# Представление для формы добавления группового акта исследования

from django.contrib import messages
from django.http import HttpResponseRedirect
from django.db.models import Q
from django.utils import timezone
from django.shortcuts import render

from reclamations.models import Reclamation
from investigations.models import Investigation
from investigations.forms import AddInvestigationForm


def add_group_investigation_view(admin_instance, request):
    """Метод добавления группового акта исследования с копией акта для всех рекламаций"""
    # Во views.py используем параметр admin_instance - через него передаем ссылку на InvestigationAdmin
    # для вызова message_user.

    context_vars = {
        "opts": Investigation._meta,
        "app_label": Investigation._meta.app_label,
        "has_view_permission": True,
        "original": None,
    }

    if request.method == "POST":
        form = AddInvestigationForm(request.POST)

        if form.is_valid():
            reclamations = form.filtered_reclamations
            all_input_numbers = form.all_input_numbers
            uploaded_file = form.cleaned_data["act_scan"]  # Получаем загруженный файл

            # Проверяем отсутствующие номера ДО создания актов
            found_numbers = set()
            all_reclamations = Reclamation.objects.all()

            for num in all_input_numbers:
                if all_reclamations.filter(
                    Q(sender_outgoing_number=num)
                    | Q(consumer_act_number=num)
                    | Q(end_consumer_act_number=num)
                ).exists():
                    found_numbers.add(num)

            missing_numbers = [
                num for num in all_input_numbers if num not in found_numbers
            ]

            if reclamations.exists():
                # Создаем акты для найденных рекламаций
                for reclamation in reclamations:
                    try:
                        investigation_fields = [
                            f
                            for f in form.Meta.fields
                            if f
                            not in [
                                "sender_numbers",
                                "consumer_act_numbers",
                                "end_consumer_act_numbers",
                            ]
                        ]

                        investigation_data = {
                            field: form.cleaned_data[field]
                            for field in investigation_fields
                        }

                        investigation = Investigation(
                            reclamation=reclamation, **investigation_data
                        )
                        # Прикрепляем файл копии ко всем актам исследования
                        investigation.act_scan = uploaded_file
                        investigation.save()

                        reclamation.status = reclamation.Status.CLOSED
                        reclamation.save()

                    except Exception as e:
                        return render(
                            request,
                            "admin/add_group_investigation.html",
                            {
                                "title": "Добавление группового акта исследования",
                                "form": form,
                                "search_result": f"Ошибка при сохранении: {str(e)}",
                                "found_records": False,
                                **context_vars,
                            },
                        )

                # Формируем сообщения
                info_message = f"Введено номеров актов: {len(all_input_numbers)}"
                success_message = f"Создано актов исследования: {reclamations.count()}"

                if missing_numbers:
                    missing_text = ", ".join(missing_numbers)
                    error_part = (
                        f"Номер акта отсутствующий в базе данных: {missing_text}"
                    )

                    # Три отдельных сообщения с разными уровнями
                    admin_instance.message_user(
                        request, info_message, level=messages.INFO
                    )
                    admin_instance.message_user(
                        request, success_message, level=messages.SUCCESS
                    )
                    admin_instance.message_user(
                        request, error_part, level=messages.WARNING
                    )
                else:
                    # Два сообщения если все номера найдены
                    admin_instance.message_user(
                        request, info_message, level=messages.INFO
                    )
                    admin_instance.message_user(
                        request, success_message, level=messages.SUCCESS
                    )

                return HttpResponseRedirect(request.get_full_path())
            else:
                # Все номера отсутствуют
                if missing_numbers:
                    missing_text = ", ".join(missing_numbers)
                    error_message = (
                        f"Номер акта отсутствующий в базе данных: {missing_text}"
                    )
                else:
                    error_message = "Указанные номера актов в базе данных отсутствуют"

                return render(
                    request,
                    "admin/add_group_investigation.html",
                    {
                        "title": "Добавление группового акта исследования",
                        "form": form,
                        "search_result": error_message,
                        "found_records": False,
                        **context_vars,
                    },
                )
        else:
            return render(
                request,
                "admin/add_group_investigation.html",
                {
                    "title": "Добавление группового акта исследования",
                    "form": form,
                    **context_vars,
                },
            )
    else:
        form = AddInvestigationForm()

    return render(
        request,
        "admin/add_group_investigation.html",
        {
            "title": "Добавление группового акта исследования",
            "form": form,
            **context_vars,
        },
    )
