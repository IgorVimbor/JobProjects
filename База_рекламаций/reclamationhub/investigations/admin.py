from django.contrib import admin
from django import forms
from django.http import HttpResponseRedirect
from django.db.models import Q
from django.urls import path
from django.shortcuts import render

from reclamationhub.admin import admin_site
from reclamations.models import Reclamation
from .models import Investigation


# список полей с типом TextField для которых будем изменять размер
INVESTIGATION_TEXT_FIELDS = [
    "defect_causes",
    "defect_causes_explanation",
    "return_condition_explanation",
]


class AddInvestigationForm(forms.ModelForm):
    # Поля для поиска рекламаций
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

    class Meta:
        model = Investigation
        fields = [
            # Акт исследования
            "act_number",
            "act_date",
            "fault_bza",
            "fault_consumer",
            "compliant_with_specs",
            "fault_unknown",
            "defect_causes",
            "defect_causes_explanation",
            "defective_supplier",
            # ПКД
            "pkd_number",
            # Утилизация
            "disposal_act_number",
            "disposal_act_date",
            "volume_removal_reference",
            # Отправка результатов
            "recipient",
            "shipment_date",
            # Отгрузка
            "shipment_invoice_number",
            "shipment_invoice_date",
            "return_condition",
            "return_condition_explanation",
        ]

        text_fields = INVESTIGATION_TEXT_FIELDS

        widgets = {
            field: forms.Textarea(
                attrs={"rows": 4, "cols": 60, "style": "resize: none;"}
            )
            for field in text_fields
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.data:
            filter_q = Q()

            if self.data.get("sender_numbers"):
                sender_list = [
                    num.strip() for num in self.data["sender_numbers"].split(",")
                ]
                filter_q |= Q(sender_outgoing_number__in=sender_list)

            if self.data.get("consumer_act_numbers"):
                consumer_list = [
                    num.strip() for num in self.data["consumer_act_numbers"].split(",")
                ]
                filter_q |= Q(consumer_act_number__in=consumer_list)

            if self.data.get("end_consumer_act_numbers"):
                end_consumer_list = [
                    num.strip()
                    for num in self.data["end_consumer_act_numbers"].split(",")
                ]
                filter_q |= Q(end_consumer_act_number__in=end_consumer_list)

            self.filtered_reclamations = Reclamation.objects.filter(filter_q)

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

        # Проверка виновников дефекта
        fault_count = sum(
            [
                cleaned_data.get("fault_bza", False),
                cleaned_data.get("fault_consumer", False),
                cleaned_data.get("fault_unknown", False),
                cleaned_data.get("compliant_with_specs", False),
            ]
        )

        if fault_count > 1:
            raise forms.ValidationError(
                "Может быть указан только один виновник дефекта или соответствие ТУ"
            )
        if fault_count == 0:
            raise forms.ValidationError(
                "Необходимо указать виновника дефекта или соответствие ТУ"
            )

        return cleaned_data


class InvestigationAdminForm(forms.ModelForm):
    class Meta:
        model = Investigation
        fields = "__all__"

        text_fields = INVESTIGATION_TEXT_FIELDS

        # устанавливаем высоту полей "rows" и ширину "cols", отключаем возможность изменения размера поля мышкой
        widgets = {
            field: forms.Textarea(
                attrs={"rows": 4, "cols": 60, "style": "resize: none;"}
            )
            for field in text_fields
        }


@admin.register(Investigation, site=admin_site)
class InvestigationAdmin(admin.ModelAdmin):

    form = InvestigationAdminForm

    class Media:
        css = {"all": ("admin/css/custom_admin.css",)}
        js = ("admin/js/custom_admin.js",)

    change_list_template = "admin/investigation_changelist.html"

    # Добавляем URL для групповой формы
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "add_group_investigation/",
                self.add_group_investigation_view,
                name="add_group_investigation",
            ),
        ]
        return custom_urls + urls

    def add_group_investigation_view(self, request):
        if request.method == "POST":
            form = AddInvestigationForm(request.POST)
            if form.is_valid():
                reclamations = form.filtered_reclamations

                if reclamations.exists():
                    for reclamation in reclamations:
                        investigation = Investigation(
                            reclamation=reclamation,
                            **{
                                field: form.cleaned_data[field]
                                for field in form.Meta.fields
                            },
                        )
                        investigation.save()

                        reclamation.status = reclamation.Status.CLOSED
                        reclamation.save()

                    self.message_user(
                        request, f"Создано {reclamations.count()} актов исследования"
                    )
                    return HttpResponseRedirect("../")
                else:
                    return render(
                        request,
                        "admin/add_group_investigation.html",
                        {
                            "title": "Добавление группового акта исследования",
                            "form": form,
                            "search_result": "Указанные номера актов рекламаций в базе данных отсутствуют.",
                            "found_records": False,
                        },
                    )
        else:
            form = AddInvestigationForm()

        return render(
            request,
            "admin/add_group_investigation.html",
            {"title": "Добавление группового акта исследования", "form": form},
        )

    # Отображение кнопок сохранения сверху и снизу формы
    save_on_top = True

    # Отображаем все поля модели Investigation
    list_display = [
        "act_number",
        "act_date",
        "reclamation",
        "fault_bza",
        "guilty_department",
        "fault_consumer",
        "compliant_with_specs",
        "fault_unknown",
        "defect_causes",
        "defect_causes_explanation",
        "defective_supplier",
        "shipment_date",
        "recipient",
        "pkd_number",
        "disposal_act_number",
        "disposal_act_date",
        "volume_removal_reference",
        "shipment_invoice_number",
        "shipment_invoice_date",
        "return_condition",
        "return_condition_explanation",
    ]

    # Группировка полей
    fieldsets = [
        (
            "Акт исследования и виновник",
            {
                "fields": [
                    "reclamation",
                    "act_number",
                    "act_date",
                    "fault_bza",
                    "guilty_department",
                    "fault_consumer",
                    "compliant_with_specs",
                    "fault_unknown",
                    "defect_causes",
                    "defect_causes_explanation",
                    "defective_supplier",
                ],
            },
        ),
        (
            "Отправка результатов исследования",
            {
                "fields": [
                    "shipment_date",
                    "recipient",
                ],
                "classes": ["shipment-section"],  # добавляем класс для якоря
            },
        ),
        (
            "Номер ПКД",
            {
                "fields": ["pkd_number"],
            },
        ),
        (
            "Утилизация",
            {
                "fields": [
                    "disposal_act_number",
                    "disposal_act_date",
                    "volume_removal_reference",
                ],
            },
        ),
        (
            "Отгрузка (возврат) изделия потребителю",
            {
                "fields": [
                    "shipment_invoice_number",
                    "shipment_invoice_date",
                    "return_condition",
                    "return_condition_explanation",
                ],
            },
        ),
    ]

    # Поля для фильтрации
    list_filter = [
        "reclamation__defect_period",
        "reclamation__product__product_type",
    ]

    # Поля для поиска
    search_fields = [
        "act_number",
        "reclamation__product__nomenclature",
        "reclamation__product_number",
    ]

    # Сортировка по умолчанию
    ordering = ["reclamation"]

    # Делаем поле reclamation обязательным
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields["reclamation"].required = True
        return form

    def save_model(self, request, obj, form, change):
        """Проверка статуса рекламации"""
        super().save_model(request, obj, form, change)
        # Если есть номер и дата акта, закрываем рекламацию
        if obj.act_number and obj.act_date:
            if not obj.reclamation.is_closed():
                obj.reclamation.close_reclamation()
                self.message_user(request, f"Рекламация {obj.reclamation} закрыта")

    # Добавляем действие в панель "Действие / Выполнить"
    actions = ["edit_shipment"]

    def edit_shipment(self, request, queryset):
        """Действие для редактирования даты отправки акта"""
        # Если выбрано больше одной записи
        if queryset.count() > 1:
            self.message_user(
                request,
                "Пожалуйста, выберите только один акт исследования для редактирования",
                level="ERROR",
            )
            return

        # Получаем единственную выбранную запись
        investigation = queryset.first()

        # Перенаправляем на форму редактирования с фокусом на секции отправки
        return HttpResponseRedirect(
            f"../investigation/{investigation.pk}/change/#shipment-section"
        )

    edit_shipment.short_description = "Редактировать запись"
