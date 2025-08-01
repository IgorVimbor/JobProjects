from django.contrib import admin
from django.utils.html import format_html
from django import forms
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import path
from django.db.models import Q

from .models import Reclamation
from sourcebook.models import Product


# Форма для ввода номеров отправителя (ПСА), актов и номера накладной
class UpdateInvoiceNumberForm(forms.Form):
    sender_numbers = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 3}),
        label="Исходящие номера отправителя",
        help_text="(вводить через запятую)",
        required=False,
    )
    consumer_act_numbers = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 3}),
        label="Номера актов приобретателя",
        help_text="(вводить через запятую)",
        required=False,
    )
    end_consumer_act_numbers = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 3}),
        label="Номера актов конечного потребителя",
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
        text_fields = [
            "sender",
            "claimed_defect",
            "consumer_requirement",
            "measures_taken",
            "consumer_response",
            "reclamation_documents",
        ]

        # устанавливаем высоту полей "rows" и ширину "cols", отключаем возможность изменения размера поля мышкой
        widgets = {
            field: forms.Textarea(
                attrs={"rows": 4, "cols": 40, "style": "resize: none;"}
            )
            for field in text_fields
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


@admin.register(Reclamation)
class ReclamationAdmin(admin.ModelAdmin):
    class Media:
        css = {"all": ("admin/css/custom_admin.css",)}
        js = ("admin/js/custom_admin.js",)

    form = ReclamationAdminForm

    # Отображение кнопок сохранения сверху и снизу формы
    save_on_top = True

    # Основные поля для отображения в списке
    list_display = [
        "status_colored",  # статус рекламации (Новая, В работе, Закрыта)
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
                ]
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
        "sender_outgoing_number",  # по Исходящему № отправителя
        "product_name__name",  # по Наименованию изделия
        "product__nomenclature",  # по Обозначению изделия
        "product_number",  # по Номеру изделия
        "consumer_act_number",  # по Номеру акта приобретателя изделия
        "end_consumer_act_number",  # по Номеру акта конечного потребителя
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

    # Вспомогательные методы для отображения

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
        """Метод для отображения иконки исследования"""
        return "✓" if obj.has_investigation else "✗"

    has_investigation_icon.short_description = "Исследование"

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
                    # Если записи найдены, обновляем их
                    updated_count = filtered_queryset.update(
                        receipt_invoice_number=invoice_number,
                        receipt_invoice_date=invoice_date,
                    )
                    self.message_user(
                        request,
                        f"Обновлены данные накладной для {updated_count} записей",
                    )
                    return HttpResponseRedirect("../")
                else:
                    # Если записи не найдены, возвращаем форму с сообщением
                    return render(
                        request,
                        "admin/update_invoice_number.html",
                        {
                            "title": "Добавление данных накладной",
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
            {"title": "Добавление данных накладной", "form": form},
        )
