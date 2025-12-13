# investigations\views\add_group_investigation.py
"""Представление для формы добавления группового акта исследования."""

from django.contrib import messages
from django.http import HttpResponseRedirect
from django.db.models import Q
from django.utils import timezone
from django.shortcuts import render

from reclamations.models import Reclamation
from investigations.models import Investigation
from investigations.forms import AddInvestigationForm


def analyze_investigation_data(form):
    """Анализ данных для группового создания актов исследования"""

    if not form.is_valid():
        return {"has_records": False, "error_message": "Форма содержит ошибки"}

    # Получаем данные из формы (используем свойства формы)
    reclamations = form.filtered_reclamations
    all_input_numbers = form.all_input_numbers

    # Проверяем отсутствующие номера
    found_numbers = set()
    all_reclamations = Reclamation.objects.all()

    for num in all_input_numbers:
        if all_reclamations.filter(
            Q(sender_outgoing_number=num)
            | Q(consumer_act_number=num)
            | Q(end_consumer_act_number=num)
        ).exists():
            found_numbers.add(num)

    missing_numbers = [num for num in all_input_numbers if num not in found_numbers]

    # Формируем результат анализа
    analysis_result = {
        "reclamations_queryset": reclamations,
        "all_input_numbers": all_input_numbers,
        "found_numbers": found_numbers,
        "missing_numbers": missing_numbers,
        "total_input_count": len(all_input_numbers),
        "found_records_count": reclamations.count() if reclamations.exists() else 0,
        "missing_count": len(missing_numbers),
        "has_records": reclamations.exists(),
        "uploaded_file": form.cleaned_data.get("act_scan"),  # Информация о файле
    }

    return analysis_result


def format_investigation_messages(analysis_result):
    """Форматирование сообщений для группового создания актов исследования"""
    messages_data = []

    # 1. Информационное сообщение (всегда)
    info_message = f"Введено номеров актов: {analysis_result['total_input_count']}"
    messages_data.append({"level": "info", "message": info_message})

    if analysis_result["has_records"]:
        # 2. Сообщение об успехе (при найденных записях)
        success_message = f"Найдено рекламаций для создания актов: {analysis_result['found_records_count']}"
        messages_data.append({"level": "success", "message": success_message})

        # 3. Предупреждение об отсутствующих номерах (если есть missing_numbers)
        if analysis_result["missing_numbers"]:
            missing_text = ", ".join(analysis_result["missing_numbers"])
            warning_message = f"Номер акта отсутствующий в базе данных: {missing_text}"
            messages_data.append({"level": "warning", "message": warning_message})
    else:
        # Записи не найдены - ошибка
        if analysis_result["missing_numbers"]:
            missing_text = ", ".join(analysis_result["missing_numbers"])
            error_message = f"Номер акта отсутствующий в базе данных: {missing_text}"
        else:
            error_message = "Указанные номера актов в базе данных отсутствуют"

        messages_data.append({"level": "error", "message": error_message})

    return messages_data


def add_group_investigation_view(admin_instance, request):
    """Метод добавления группового акта исследования с копией акта для всех рекламаций"""

    context_vars = {
        "opts": Investigation._meta,
        "app_label": Investigation._meta.app_label,
        "has_view_permission": True,
        "original": None,
    }

    if request.method == "POST":
        # Определяем режим работы по нажатой кнопке
        is_preview_mode = request.POST.get("action") == "Предварительный просмотр"

        form = AddInvestigationForm(request.POST, request.FILES)

        if form.is_valid():
            # Анализируем данные (всегда)
            analysis_result = analyze_investigation_data(form)

            if is_preview_mode:
                # РЕЖИМ ПРЕДВАРИТЕЛЬНОГО ПРОСМОТРА - НЕ СОХРАНЯЕМ
                messages_data = format_investigation_messages(analysis_result)

                return render(
                    request,
                    "admin/add_group_investigation.html",
                    {
                        "title": "Добавление группового акта исследования",
                        "form": form,
                        "preview_mode": True,
                        "preview_messages": messages_data,
                        "found_records": analysis_result["has_records"],
                        "records_count": analysis_result["found_records_count"],
                        "uploaded_file_name": (
                            analysis_result["uploaded_file"].name
                            if analysis_result["uploaded_file"]
                            else None
                        ),
                        **context_vars,
                    },
                )
            else:
                # РЕЖИМ ПРИМЕНЕНИЯ ИЗМЕНЕНИЙ - СОХРАНЯЕМ
                if analysis_result["has_records"]:
                    # Если есть записи - создаем акты
                    reclamations = analysis_result["reclamations_queryset"]
                    uploaded_file = analysis_result["uploaded_file"]

                    # ---------- Создаем акты для найденных рекламаций -----------
                    created_count = 0  # счетчик созданных актов исследования
                    updated_count = 0  # счетчик обновленных актов исследования
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

                            # ✅ Проверяем существование Investigation
                            if hasattr(reclamation, "investigation"):
                                # Investigation уже существует
                                existing_investigation = reclamation.investigation

                                # Проверяем, это "автоматический" акт или реальный
                                if (
                                    existing_investigation.act_number
                                    == "без исследования"
                                ):
                                    # ОБНОВЛЯЕМ существующий автоматический акт
                                    for field, value in investigation_data.items():
                                        setattr(existing_investigation, field, value)
                                    # Прикрепляем файл копии ко всем актам исследования
                                    existing_investigation.act_scan = uploaded_file
                                    # Сохраняем изменения и увеличиваем счетчик обновленных актов исследования
                                    existing_investigation.save()
                                    updated_count += 1
                            else:
                                # СОЗДАЕМ новый Investigation
                                investigation = Investigation(
                                    reclamation=reclamation, **investigation_data
                                )
                                # Прикрепляем файл копии ко всем актам исследования
                                investigation.act_scan = uploaded_file
                                # Сохраняем изменения и увеличиваем счетчик обновленных актов исследования
                                investigation.save()
                                created_count += 1

                            # Обновляем статус рекламации
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

                    # Формируем и отправляем сообщения в Django Admin
                    messages_data = format_investigation_messages(analysis_result)

                    level_map = {
                        "info": messages.INFO,
                        "success": messages.SUCCESS,
                        "warning": messages.WARNING,
                        "error": messages.ERROR,
                    }

                    for msg_data in messages_data:
                        # Обновляем сообщение об успехе с фактическим количеством созданных и обновленных записей
                        if msg_data["level"] == "success":
                            success_parts = []
                            if created_count > 0:
                                success_parts.append(f"создано: {created_count}")
                            if updated_count > 0:
                                success_parts.append(f"обновлено: {updated_count}")

                            msg_data["message"] = (
                                f"Актов исследования {', '.join(success_parts)}"
                            )

                        admin_instance.message_user(
                            request,
                            msg_data["message"],
                            level=level_map[msg_data["level"]],
                        )

                    return HttpResponseRedirect(request.get_full_path())
                else:
                    # Записи не найдены - показываем ошибку
                    messages_data = format_investigation_messages(analysis_result)
                    error_message = messages_data[-1][
                        "message"
                    ]  # Последнее сообщение - ошибка

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
            # Форма невалидна
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
        # GET запрос - показываем пустую форму
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
