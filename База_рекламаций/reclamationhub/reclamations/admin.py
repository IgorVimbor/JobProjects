from django.contrib import admin
from django.utils.html import format_html
from django import forms
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import path
from django.db.models import Q

from reclamationhub.admin import admin_site
from .models import Reclamation
from sourcebook.models import Product


# Форма для ввода номеров отправителя (ПСА), актов и номера накладной
class UpdateInvoiceNumberForm(forms.Form):
    sender_numbers = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 3}),
        label="Исходящий номер отправителя (ПСА)",
        help_text="(вводить через запятую)",
        required=False,
    )
    consumer_act_numbers = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 3}),
        label="Номер акта приобретателя",
        help_text="(вводить через запятую)",
        required=False,
    )
    end_consumer_act_numbers = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 3}),
        label="Номер акта конечного потребителя",
        help_text="(вводить через запятую)",
        required=False,
    )
    invoice_number = forms.CharField(label="Номер накладной", required=True)
    invoice_date = forms.DateField(
        label="Дата накладной",
        widget=forms.DateInput(attrs={"type": "date"}),
        required=True,
    )

    def clean(self):
        cleaned_data = super().clean()
        if not any(
            [
                cleaned_data.get("sender_numbers"),
                cleaned_data.get("consumer_act_numbers"),
                cleaned_data.get("end_consumer_act_numbers"),
            ]
        ):
            raise forms.ValidationError(
                "Необходимо заполнить хотя бы одно поле с номерами для поиска"
            )
        return cleaned_data


class ReclamationAdminForm(forms.ModelForm):
    class Meta:
        model = Reclamation
        fields = "__all__"
        # список полей из модели с типом TextField для которых будем изменять размер
        text_fields = ["measures_taken", "consumer_response"]

        # устанавливаем высоту полей "rows" и ширину "cols", отключаем возможность изменения размера поля мышкой
        widgets = {
            "away_type": forms.RadioSelect(),  # Добавляем RadioSelect для away_type
            **{
                field: forms.Textarea(
                    attrs={"rows": 4, "cols": 60, "style": "resize: none;"}
                )
                for field in text_fields
            },
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Определяем тип изделия
        if self.data and "product_name" in self.data:
            # Если форма отправлена, берем тип из данных формы
            product_type_id = self.data.get("product_name")
        elif self.instance.pk and self.instance.product_name:
            # Если редактируем существующую запись
            product_type_id = self.instance.product_name.id
        else:
            # По умолчанию - водяные насосы
            product_type_id = 1

        # Фильтруем queryset в соответствии с типом изделия
        filtered_queryset = Product.objects.filter(
            product_type_id=product_type_id
        ).order_by("nomenclature")

        self.fields["product"] = forms.ModelChoiceField(
            queryset=filtered_queryset,
            label="Обозначение изделия",
            required=True,
            empty_label="---------",
        )

    def clean(self):
        cleaned_data = super().clean()

        # Проверяем соответствие продукта выбранному типу
        product = cleaned_data.get("product")
        product_name = cleaned_data.get("product_name")

        if product and product_name:
            if product.product_type_id != product_name.id:
                self.add_error(
                    "product", "Выбранное изделие не соответствует выбранному типу"
                )

        return cleaned_data


@admin.register(Reclamation, site=admin_site)
class ReclamationAdmin(admin.ModelAdmin):
    class Media:
        css = {"all": ("admin/css/custom_admin.css",)}
        js = ("admin/js/custom_admin.js", "admin/js/copy_act_fields.js")

    form = ReclamationAdminForm

    # Отображение кнопок сохранения сверху и снизу формы
    save_on_top = True

    # Основные поля для отображения в списке
    list_display = [
        "id",
        "status_colored",  # статус рекламации (Новая, В работе, Закрыта)
        "incoming_number",  # входящий № по ОТК
        "defect_period",  # период выявления дефекта
        "sender_outgoing_number",  # исходящий № отправителя
        "product_name",  # наименование изделия
        "product",  # обозначение изделия
        "product_number",  # заводской номер изделия
        "claimed_defect",  # дефект
        "consumer_act_number",  # номер акта приобретателя изделия
        "consumer_act_date",  # дата акта приобретателя изделия
        "end_consumer_act_number",  # номер акта конечного потребителя
        "end_consumer_act_date",  # дата акта конечного потребителя
        "engine_number",  # номер двигателя
        "mileage_operating_time",  # пробег/наработка
        "products_count",  # количество изделий
        "measures_taken",  # принятые меры
        "outgoing_document_number",  # номер исходящего документа
        "receipt_invoice_number",  # номер накладной поступления изделия
        "receipt_invoice_date",  # дата накладной поступления изделия
        "has_investigation_icon",  # иконка "Исследование"
    ]

    # Группировка полей в форме редактирования
    fieldsets = [
        (
            "Информация о сообщении",
            {
                "fields": [
                    "incoming_number",
                    "sender",
                    "sender_outgoing_number",
                    "message_sent_date",
                    "status",
                ]
            },
        ),
        (
            "Информация об изделии",
            {
                "fields": [
                    "product_name",
                    "product",
                    "product_number",
                    "manufacture_date",
                    "defect_period",
                ]
            },
        ),
        (
            "Рекламационный акт приобретателя",
            {
                "fields": [
                    "purchaser",
                    "consumer_act_number",
                    "consumer_act_date",
                ]
            },
        ),
        (
            "Рекламационный акт конечного потребителя",
            {
                "fields": [
                    "country_rejected",
                    "end_consumer",
                    "end_consumer_act_number",
                    "end_consumer_act_date",
                ]
            },
        ),
        (
            "Информация о двигателе и ТС",
            {
                "fields": [
                    "engine_brand",
                    "engine_number",
                    "transport_name",
                    "transport_number",
                ]
            },
        ),
        (
            "Информация о дефекте",
            {
                "fields": [
                    "defect_detection_date",
                    "away_type",
                    "mileage_operating_time",
                    "claimed_defect",
                    "consumer_requirement",
                    "products_count",
                ]
            },
        ),
        (
            "Принятые меры",
            {
                "fields": [
                    "measures_taken",
                    "outgoing_document_number",
                    "outgoing_document_date",
                    "letter_sending_method",
                ],
                "classes": ["measures-section"],  # добавляем класс для якоря
            },
        ),
        (
            "Ответ потребителя",
            {
                "fields": [
                    "consumer_response",
                    "consumer_response_number",
                    "consumer_response_date",
                ]
            },
        ),
        (
            "Поступление изделия",
            {
                "fields": [
                    "product_received_date",
                    "product_sender",
                    "receipt_invoice_number",
                    "receipt_invoice_date",
                    "reclamation_documents",
                ]
            },
        ),
    ]

    # Фильтры
    list_filter = [
        "defect_period",
        "product__product_type",
    ]

    # Поиск
    search_fields = [
        "incoming_number",  # входящий № по ОТК
        "sender_outgoing_number",  # исходящий № отправителя
        "product_name__name",  # наименование изделия
        "product__nomenclature",  # обозначение изделия
        "product_number",  # номер изделия
        "consumer_act_number",  # номер акта приобретателя изделия
        "end_consumer_act_number",  # номер акта конечного потребителя
        "engine_number",  # номер двигателя
    ]

    # Метод get_queryset с select_related используется для оптимизации запросов к базе данных.
    # Без select_related будет N+1 запросов (1 запрос для списка рекламаций + N запросов для связанных данных)
    # С select_related будет только 1 запрос
    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("product_name", "product", "defect_period")
        )

    # ----------------------------- Вспомогательные методы для отображения -----------------------------------

    # def claimed_defect_display(self, obj):
    #     """Метод для сокращения длинного текста дефекта"""
    #     if len(obj.claimed_defect) > 50:
    #         return f"{obj.claimed_defect[:50]}..."
    #     return obj.claimed_defect

    # claimed_defect_display.short_description = "Дефект"

    # И заменим в list_display (список вверху)
    # list_display = [
    #     # ...
    #     "claimed_defect_display",  # вместо "claimed_defect"
    #     # ...
    # ]

    # Добавляем действие в панель "Действие / Выполнить"
    actions = ["add_measures"]

    def add_measures(self, request, queryset):
        """Действие для редактирования рекламации"""
        # Если выбрано больше одной записи
        if queryset.count() > 1:
            self.message_user(
                request,
                "Пожалуйста, выберите только одну рекламацию для редактирования",
                level="ERROR",
            )
            return

        # Получаем единственную выбранную запись
        reclamation = queryset.first()

        # Перенаправляем на форму редактирования с фокусом на секции "Принятые меры"
        return HttpResponseRedirect(
            f"../reclamation/{reclamation.pk}/change/#measures-section"
        )

    add_measures.short_description = "Редактировать запись"

    def status_colored(self, obj):
        """Метод для цветового отображения статуса рекламации"""
        colors = {"NEW": "blue", "IN_PROGRESS": "orange", "CLOSED": "green"}
        return format_html(
            '<span style="color: {};">{}</span>',
            colors[obj.status],
            obj.get_status_display(),
        )

    status_colored.short_description = "Статус"

    def has_investigation_icon(self, obj):
        """Метод для отображения номера акта исследования"""
        if obj.has_investigation:
            return obj.investigation.act_number
        return ""

    has_investigation_icon.short_description = "Исследование"

    # def save_model(self, request, obj, form, change):
    #     """Обновление статуса рекламации при добавлении номера накладной прихода изделия"""
    #     # Если это изменение существующей записи, добавлен номер накладной и статус "Новая"
    #     if change and "receipt_invoice_number" in form.changed_data and obj.is_new():
    #         obj.update_status_on_receipt()
    #         self.message_user(request, 'Статус рекламации изменен на "В работе"')
    #     super().save_model(request, obj, form, change)

    def save_model(self, request, obj, form, change):
        """Обновление статуса рекламации и добавление суффикса к пробегу"""
        # Добавляем суффикс к пробегу/наработке в зависимости от типа
        if (
            obj.away_type == Reclamation.AwayType.KILOMETRE
            and not obj.mileage_operating_time.endswith(" км")
        ):
            obj.mileage_operating_time = f"{obj.mileage_operating_time} км"
        elif (
            obj.away_type == Reclamation.AwayType.MOTO
            and not obj.mileage_operating_time.endswith(" м/ч")
        ):
            obj.mileage_operating_time = f"{obj.mileage_operating_time} м/ч"

        # Обновление статуса рекламации при добавлении накладной или удалении накладной
        if change and "receipt_invoice_number" in form.changed_data:
            old_obj = Reclamation.objects.get(pk=obj.pk)

            # Если было значение, а стало пустым и статус "В работе"
            if (
                old_obj.receipt_invoice_number
                and not obj.receipt_invoice_number
                and obj.status == Reclamation.Status.IN_PROGRESS
            ):
                obj.status = Reclamation.Status.NEW
                self.message_user(request, "Статус рекламации изменен на 'Новая'")
            # Если поле заполнено и статус "Новая"
            elif obj.receipt_invoice_number and obj.is_new():
                obj.status = Reclamation.Status.IN_PROGRESS
                self.message_user(request, "Статус рекламации изменен на 'В работе'")

        super().save_model(request, obj, form, change)

    # Автозаполнение для связанных полей
    autocomplete_fields = ["product_name", "product"]

    # Быстрый поиск по ID
    raw_id_fields = ["product_name", "product"]

    # Сортировка по умолчанию
    ordering = ["-message_received_date"]

    # Добавляем шаблон формы, где можно будет ввести номера актов и номер накладной
    change_list_template = "admin/reclamation_changelist.html"

    # Добавляем URL для формы
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("add_invoice/", self.add_invoice_view, name="add_invoice"),
        ]
        return custom_urls + urls

    # Обработчик формы для добавления накладной
    def add_invoice_view(self, request):
        if request.method == "POST":
            form = UpdateInvoiceNumberForm(request.POST)
            if form.is_valid():
                invoice_number = form.cleaned_data["invoice_number"]
                invoice_date = form.cleaned_data["invoice_date"]

                filter_q = Q()

                if form.cleaned_data["sender_numbers"]:
                    sender_list = [
                        num.strip()
                        for num in form.cleaned_data["sender_numbers"].split(",")
                    ]
                    filter_q |= Q(sender_outgoing_number__in=sender_list)
                    # filter_q |= - это операция побитового ИЛИ с присваиванием в Python,
                    # которая в контексте Django Q-объектов используется для объединения
                    # условий фильтрации через логическое ИЛИ (OR)

                if form.cleaned_data["consumer_act_numbers"]:
                    consumer_list = [
                        num.strip()
                        for num in form.cleaned_data["consumer_act_numbers"].split(",")
                    ]
                    filter_q |= Q(consumer_act_number__in=consumer_list)

                if form.cleaned_data["end_consumer_act_numbers"]:
                    end_consumer_list = [
                        num.strip()
                        for num in form.cleaned_data["end_consumer_act_numbers"].split(
                            ","
                        )
                    ]
                    filter_q |= Q(end_consumer_act_number__in=end_consumer_list)

                filtered_queryset = self.model.objects.filter(filter_q)

                # Проверяем, найдены ли записи
                if filtered_queryset.exists():
                    # Обновляем накладную и статус для записей со статусом NEW
                    updated_count = filtered_queryset.filter(
                        status=self.model.Status.NEW
                    ).update(
                        receipt_invoice_number=invoice_number,
                        receipt_invoice_date=invoice_date,
                        status=self.model.Status.IN_PROGRESS,
                    )

                    # Обновляем только накладную для остальных записей
                    other_updated = filtered_queryset.exclude(
                        status=self.model.Status.NEW
                    ).update(
                        receipt_invoice_number=invoice_number,
                        receipt_invoice_date=invoice_date,
                    )

                    total_updated = updated_count + other_updated
                    status_message = (
                        f" (изменен статус для {updated_count} записей)"
                        if updated_count
                        else ""
                    )

                    self.message_user(
                        request,
                        f"Обновлены данные накладной для {total_updated} записей{status_message}",
                    )
                    return HttpResponseRedirect("../")
                else:
                    # Если записи не найдены, возвращаем форму с сообщением
                    return render(
                        request,
                        "admin/update_invoice_number.html",
                        {
                            "title": "Добавление данных накладной прихода изделий",
                            "form": form,
                            "search_result": "Указанные номера актов рекламаций в базе данных отсутствуют.",
                            "found_records": False,
                        },
                    )
        else:
            form = UpdateInvoiceNumberForm()

        return render(
            request,
            "admin/update_invoice_number.html",
            {
                "title": "Добавление данных накладной прихода изделий",
                "form": form,
            },
        )
