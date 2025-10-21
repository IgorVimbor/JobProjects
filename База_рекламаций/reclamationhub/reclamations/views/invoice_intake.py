# Представление для формы группового добавления накладной прихода изделий

from django.contrib import messages
from django.http import HttpResponseRedirect
from django.db.models import Q
from django.shortcuts import render

from reclamations.models import Reclamation
from reclamations.forms import UpdateInvoiceNumberForm


def analyze_invoice_data(form):
    """Анализ данных для группового добавления накладной прихода"""

    if not form.is_valid():
        return {"has_records": False, "error_message": "Форма содержит ошибки"}

    # Собираем все введенные номера
    all_input_numbers = []
    filter_q = Q()

    if form.cleaned_data["sender_numbers"]:
        sender_list = [
            num.strip() for num in form.cleaned_data["sender_numbers"].split(",")
        ]
        all_input_numbers.extend(sender_list)
        filter_q |= Q(sender_outgoing_number__in=sender_list)

    if form.cleaned_data["consumer_act_numbers"]:
        consumer_list = [
            num.strip() for num in form.cleaned_data["consumer_act_numbers"].split(",")
        ]
        all_input_numbers.extend(consumer_list)
        filter_q |= Q(consumer_act_number__in=consumer_list)

    if form.cleaned_data["end_consumer_act_numbers"]:
        end_consumer_list = [
            num.strip()
            for num in form.cleaned_data["end_consumer_act_numbers"].split(",")
        ]
        all_input_numbers.extend(end_consumer_list)
        filter_q |= Q(end_consumer_act_number__in=end_consumer_list)

    # Фильтруем рекламации
    filtered_queryset = Reclamation.objects.filter(filter_q)

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
        "reclamations_queryset": filtered_queryset,
        "all_input_numbers": all_input_numbers,
        "found_numbers": found_numbers,
        "missing_numbers": missing_numbers,
        "total_input_count": len(all_input_numbers),
        "found_records_count": (
            filtered_queryset.count() if filtered_queryset.exists() else 0
        ),
        "missing_count": len(missing_numbers),
        "has_records": filtered_queryset.exists(),
        # Данные накладной
        "received_date": form.cleaned_data.get("received_date"),
        "product_sender": form.cleaned_data.get("product_sender"),
        "invoice_number": form.cleaned_data.get("invoice_number"),
        "invoice_date": form.cleaned_data.get("invoice_date"),
    }

    return analysis_result


def format_invoice_messages(analysis_result):
    """Форматирование сообщений для группового добавления накладной прихода"""
    messages_data = []

    # 1. Информационное сообщение (всегда)
    info_message = f"Введено номеров актов: {analysis_result['total_input_count']}"
    messages_data.append({"level": "info", "message": info_message})

    if analysis_result["has_records"]:
        # 2. Сообщение об успехе (при найденных записях)
        success_message = f"Найдено рекламаций для обновления: {analysis_result['found_records_count']}"
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


def add_invoice_into_view(admin_instance, request):
    """Метод группового добавления накладной прихода рекламационных изделий"""

    context_vars = {
        "opts": Reclamation._meta,
        "app_label": Reclamation._meta.app_label,
        "has_view_permission": True,
        "original": None,
    }

    if request.method == "POST":
        # Определяем режим работы по нажатой кнопке
        is_preview_mode = request.POST.get("action") == "Предварительный просмотр"

        form = UpdateInvoiceNumberForm(request.POST)

        if form.is_valid():
            # Анализируем данные (всегда)
            analysis_result = analyze_invoice_data(form)

            if is_preview_mode:
                # РЕЖИМ ПРЕДВАРИТЕЛЬНОГО ПРОСМОТРА - НЕ СОХРАНЯЕМ
                messages_data = format_invoice_messages(analysis_result)

                return render(
                    request,
                    "admin/add_group_invoice_into.html",
                    {
                        "title": "Добавление накладной прихода изделий",
                        "form": form,
                        "preview_mode": True,
                        "preview_messages": messages_data,
                        "found_records": analysis_result["has_records"],
                        "records_count": analysis_result["found_records_count"],
                        **context_vars,
                    },
                )
            else:
                # РЕЖИМ ПРИМЕНЕНИЯ ИЗМЕНЕНИЙ - СОХРАНЯЕМ
                if analysis_result["has_records"]:
                    # Если есть записи - обновляем их
                    filtered_queryset = analysis_result["reclamations_queryset"]
                    received_date = analysis_result["received_date"]
                    product_sender = analysis_result["product_sender"]
                    invoice_number = analysis_result["invoice_number"]
                    invoice_date = analysis_result["invoice_date"]

                    # Обновляем накладную и статус для записей со статусом NEW
                    updated_count = filtered_queryset.filter(
                        status=Reclamation.Status.NEW
                    ).update(
                        product_received_date=received_date,
                        product_sender=product_sender,
                        receipt_invoice_number=invoice_number,
                        receipt_invoice_date=invoice_date,
                        status=Reclamation.Status.IN_PROGRESS,
                    )

                    # Обновляем только накладную для остальных записей
                    other_updated = filtered_queryset.exclude(
                        status=Reclamation.Status.NEW
                    ).update(
                        product_received_date=received_date,
                        product_sender=product_sender,
                        receipt_invoice_number=invoice_number,
                        receipt_invoice_date=invoice_date,
                    )

                    total_updated = updated_count + other_updated
                    status_message = (
                        f"Изменен статус для записей: {updated_count}"
                        if updated_count
                        else ""
                    )

                    # Формируем и отправляем сообщения в Django Admin
                    messages_data = format_invoice_messages(analysis_result)

                    level_map = {
                        "info": messages.INFO,
                        "success": messages.SUCCESS,
                        "warning": messages.WARNING,
                        "error": messages.ERROR,
                    }

                    for msg_data in messages_data:
                        # Обновляем сообщение об успехе с фактическим количеством обновленных записей
                        if msg_data["level"] == "success":
                            msg_data["message"] = (
                                f"Обновлены данные накладной для записей: {total_updated} {status_message}"
                            )

                        admin_instance.message_user(
                            request,
                            msg_data["message"],
                            level=level_map[msg_data["level"]],
                        )

                    return HttpResponseRedirect(request.get_full_path())
                else:
                    # Записи не найдены - показываем ошибку
                    messages_data = format_invoice_messages(analysis_result)
                    error_message = messages_data[-1][
                        "message"
                    ]  # Последнее сообщение - ошибка

                    return render(
                        request,
                        "admin/add_group_invoice_into.html",
                        {
                            "title": "Добавление накладной прихода изделий",
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
                "admin/add_group_invoice_into.html",
                {
                    "title": "Добавление накладной прихода изделий",
                    "form": form,
                    **context_vars,
                },
            )
    else:
        # GET запрос - показываем пустую форму
        form = UpdateInvoiceNumberForm()

    return render(
        request,
        "admin/add_group_invoice_into.html",
        {
            "title": "Добавление накладной прихода изделий",
            "form": form,
            **context_vars,
        },
    )
