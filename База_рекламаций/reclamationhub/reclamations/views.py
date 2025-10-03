from django.contrib import messages
from django.http import JsonResponse, HttpResponseRedirect
from django.db.models import Q
from django.shortcuts import render

from sourcebook.models import Product
from .models import Reclamation
from .forms import UpdateInvoiceNumberForm


def get_products(request):
    """Возвращает список продуктов для выбранного типа"""
    product_type_id = request.GET.get("product_type_id")

    if product_type_id:
        products = (
            Product.objects.filter(product_type_id=product_type_id)
            .values("id", "nomenclature")
            .order_by("nomenclature")
        )

        product_list = list(products)
        return JsonResponse(product_list, safe=False)

    return JsonResponse([])


def add_invoice_into_view(admin_instance, request):
    """Метод группового добавления накладной прихода рекламационных изделий"""
    context_vars = {
        "opts": Reclamation._meta,
        "app_label": Reclamation._meta.app_label,
        "has_view_permission": True,
        "original": None,
    }

    if request.method == "POST":
        form = UpdateInvoiceNumberForm(request.POST)
        if form.is_valid():
            received_date = form.cleaned_data["received_date"]
            product_sender = form.cleaned_data["product_sender"]
            invoice_number = form.cleaned_data["invoice_number"]
            invoice_date = form.cleaned_data["invoice_date"]

            # Собираем все введенные номера
            all_input_numbers = []
            filter_q = Q()

            if form.cleaned_data["sender_numbers"]:
                sender_list = [
                    num.strip()
                    for num in form.cleaned_data["sender_numbers"].split(",")
                ]
                all_input_numbers.extend(sender_list)
                filter_q |= Q(sender_outgoing_number__in=sender_list)

            if form.cleaned_data["consumer_act_numbers"]:
                consumer_list = [
                    num.strip()
                    for num in form.cleaned_data["consumer_act_numbers"].split(",")
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

            missing_numbers = [
                num for num in all_input_numbers if num not in found_numbers
            ]

            # Проверяем, найдены ли записи
            if filtered_queryset.exists():
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

                # Формируем сообщения
                info_message = f"Введено номеров актов: {len(all_input_numbers)}"
                success_message = f"Обновлены данные накладной для записей: {total_updated} {status_message}"

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
                    error_message = "Указанные номера актов в базе данных отсутствуют."

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
    from django.contrib import admin  # Импорт для admin.helpers

    context = {
        "title": "Добавление акта утилизации",
        "reclamations": queryset,
        "count": queryset.count(),
        "opts": Reclamation._meta,
        "action": "add_disposal_act",
        "action_checkbox_name": admin.helpers.ACTION_CHECKBOX_NAME,
    }
    return render(request, "admin/add_disposal_act.html", context)
