from django.contrib import messages
from django.http import HttpResponseRedirect
from django.db.models import Q
from django.utils import timezone
from django.shortcuts import render

from reclamations.models import Reclamation
from .models import Investigation
from .forms import AddInvestigationForm, UpdateInvoiceOutForm


def add_group_investigation_view(admin_instance, request):
    """Метод добавления группового акта исследования с копией акта для всех рекламаций"""
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


def analyze_invoice_numbers(form_data):
    """Анализ введенных номеров и формирование информационных сообщений"""
    all_input_numbers = []
    filter_q = Q()

    # Обработка номеров актов исследования
    if form_data["act_numbers"]:
        act_list = [
            num.strip() for num in form_data["act_numbers"].split(",") if num.strip()
        ]
        current_year = timezone.now().year
        full_act_numbers = [f"{current_year} № {num}" for num in act_list]
        all_input_numbers.extend(act_list)
        filter_q |= Q(act_number__in=full_act_numbers)

    # Обработка номеров ПСА
    if form_data["sender_numbers"]:
        sender_list = [
            num.strip() for num in form_data["sender_numbers"].split(",") if num.strip()
        ]
        all_input_numbers.extend(sender_list)
        filter_q |= Q(reclamation__sender_outgoing_number__in=sender_list)

    # Обработка номеров актов рекламаций
    if form_data["reclamation_act_numbers"]:
        consumer_act_list = [
            num.strip()
            for num in form_data["reclamation_act_numbers"].split(",")
            if num.strip()
        ]
        all_input_numbers.extend(consumer_act_list)
        filter_q |= Q(reclamation__consumer_act_number__in=consumer_act_list)
        filter_q |= Q(reclamation__end_consumer_act_number__in=consumer_act_list)

    # Обработка номера накладной прихода
    if form_data["receipt_invoice_number"]:
        invoice_number = form_data["receipt_invoice_number"].strip()
        all_input_numbers.append(invoice_number)
        filter_q |= Q(reclamation__receipt_invoice_number=invoice_number)

    filtered_queryset = Investigation.objects.filter(filter_q)

    # Проверяем отсутствующие номера (ваша существующая логика)
    found_numbers = set()
    all_investigations = Investigation.objects.all()
    all_reclamations = Reclamation.objects.all()

    for num in all_input_numbers:
        current_year = timezone.now().year
        full_act_number = f"{current_year} № {num}"
        if all_investigations.filter(act_number=full_act_number).exists():
            found_numbers.add(num)
        elif all_reclamations.filter(sender_outgoing_number=num).exists():
            found_numbers.add(num)
        elif all_reclamations.filter(consumer_act_number=num).exists():
            found_numbers.add(num)
        elif all_reclamations.filter(end_consumer_act_number=num).exists():
            found_numbers.add(num)
        elif all_reclamations.filter(receipt_invoice_number=num).exists():
            found_numbers.add(num)

    missing_numbers = [num for num in all_input_numbers if num not in found_numbers]

    return {
        "filtered_queryset": filtered_queryset,
        "all_input_numbers": all_input_numbers,
        "found_numbers": found_numbers,
        "missing_numbers": missing_numbers,
        "total_input_count": len(all_input_numbers),
        "found_records_count": filtered_queryset.count(),
        "has_records": filtered_queryset.exists(),
    }


def format_analysis_messages(analysis_result):
    """Форматирование сообщений как в вашем исходном коде"""
    messages_data = []

    # 1. Информационное сообщение
    info_message = f"Введено номеров: {analysis_result['total_input_count']}"
    messages_data.append({"level": "info", "message": info_message})

    if analysis_result["has_records"]:
        # 2. Сообщение об успехе
        success_message = (
            f"Найдено записей для обновления: {analysis_result['found_records_count']}"
        )
        messages_data.append({"level": "success", "message": success_message})

        # 3. Предупреждение об отсутствующих номерах (если есть)
        if analysis_result["missing_numbers"]:
            missing_text = ", ".join(analysis_result["missing_numbers"])
            warning_message = f"Номера отсутствующие в базе данных: {missing_text}"
            messages_data.append({"level": "warning", "message": warning_message})
    else:
        # Записи не найдены
        if analysis_result["missing_numbers"]:
            missing_text = ", ".join(analysis_result["missing_numbers"])
            error_message = f"Номера отсутствующие в базе данных: {missing_text}"
        else:
            error_message = "Указанные номера в базе данных отсутствуют."

        messages_data.append({"level": "error", "message": error_message})

    return messages_data


def add_invoice_out_view(admin_instance, request):
    """Метод группового добавления накладной отгрузки изделий"""

    context_vars = {
        "opts": Investigation._meta,
        "app_label": Investigation._meta.app_label,
        "has_view_permission": True,
        "original": None,
    }

    if request.method == "POST":
        # Определяем режим работы по нажатой кнопке
        is_preview_mode = request.POST.get("action") == "Предварительный просмотр"

        form = UpdateInvoiceOutForm(request.POST)
        if form.is_valid():
            # Анализируем данные (всегда)
            analysis_result = analyze_invoice_numbers(form.cleaned_data)

            if is_preview_mode:
                # РЕЖИМ ПРЕДВАРИТЕЛЬНОГО ПРОСМОТРА - НЕ СОХРАНЯЕМ
                messages_data = format_analysis_messages(analysis_result)

                return render(
                    request,
                    "admin/add_group_invoice_out.html",
                    {
                        "title": "Добавление накладной отгрузки изделий",
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
                    # Применяем изменения
                    shipment_invoice_number = form.cleaned_data[
                        "shipment_invoice_number"
                    ]
                    shipment_invoice_date = form.cleaned_data["shipment_invoice_date"]

                    updated_count = analysis_result["filtered_queryset"].update(
                        shipment_invoice_number=shipment_invoice_number,
                        shipment_invoice_date=shipment_invoice_date,
                    )

                    # Формируем и отправляем сообщения в Django Admin
                    messages_data = format_analysis_messages(analysis_result)

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
                                f"Обновлены данные накладной отгрузки для записей: {updated_count}"
                            )

                        admin_instance.message_user(
                            request,
                            msg_data["message"],
                            level=level_map[msg_data["level"]],
                        )

                    return HttpResponseRedirect(request.get_full_path())
                else:
                    # Записи не найдены - показываем ошибку
                    messages_data = format_analysis_messages(analysis_result)
                    error_message = messages_data[-1][
                        "message"
                    ]  # Последнее сообщение - ошибка

                    return render(
                        request,
                        "admin/add_group_invoice_out.html",
                        {
                            "title": "Добавление накладной отгрузки изделий",
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
                "admin/add_group_invoice_out.html",
                {
                    "title": "Добавление накладной отгрузки изделий",
                    "form": form,
                    **context_vars,
                },
            )
    else:
        # GET запрос - показываем пустую форму
        form = UpdateInvoiceOutForm()

    return render(
        request,
        "admin/add_group_invoice_out.html",
        {
            "title": "Добавление накладной отгрузки изделий",
            "form": form,
            **context_vars,
        },
    )
