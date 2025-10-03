# Файл с формами приложения актов исследований Investigation

from django import forms
from django.contrib.admin.widgets import AdminDateWidget
from django.db.models import Q
from django.utils import timezone

from reclamations.models import Reclamation
from .models import Investigation


# --------------------------- Константы для виджетов форм ------------------------------

# Список полей с типом CharField с возможностью переноса строк
INVESTIGATION_TEXT_FIELDS = [
    "defect_causes",
    "defect_causes_explanation",
    "return_condition_explanation",
]
# Список полей с типом DateField
INVESTIGATION_DATE_FIELDS = [
    "act_date",
    "shipment_date",
    "disposal_act_date",
    "shipment_invoice_date",
]

# ------------------------- Формы приложения Investigation -----------------------------


class AddInvestigationForm(forms.ModelForm):
    """Форма группового добавления акта исследования"""

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
            # Сначала поля поиска
            "sender_numbers",
            "consumer_act_numbers",
            "end_consumer_act_numbers",
            # Акт исследования
            "act_number",
            "act_date",
            "act_scan",
            # Решение по рекламации
            "solution",
            # Виновник
            "fault_type",
            "guilty_department",
            # Пояснения к дефекту
            "defect_causes",
            "defect_causes_explanation",
            "defective_supplier",
            # Отправка результатов
            "shipment_date",
            "recipient",
            # Утилизация
            "disposal_act_number",
            "disposal_act_date",
            # Отгрузка
            "shipment_invoice_number",
            "shipment_invoice_date",
            "return_condition",
            "return_condition_explanation",
        ]

        widgets = {
            "act_date": forms.DateInput(attrs={"type": "date"}),
            "shipment_date": forms.DateInput(attrs={"type": "date"}),
            "disposal_act_date": forms.DateInput(attrs={"type": "date"}),
            "shipment_invoice_date": forms.DateInput(attrs={"type": "date"}),
            "fault_type": forms.RadioSelect(),  # Виджет RadioSelect для fault_type
            "act_scan": forms.FileInput(
                attrs={  # Виджет для файла копии акта
                    "accept": ".pdf",
                    "class": "form-control",
                }
            ),
            **{  # Настройка текстовых полей - высота полей, перенос строк и запрет изменения размера
                field: forms.TextInput(
                    attrs={
                        "style": "width: 600px; text-overflow: ellipsis; resize: none;"
                    }
                )
                for field in INVESTIGATION_TEXT_FIELDS
            },
            **{  # Виджет DateInput для полей дат
                field: forms.DateInput(attrs={"type": "date"})
                for field in INVESTIGATION_DATE_FIELDS
            },
            # **{  # Виджет AdminDateWidget для полей дат
            #     field: AdminDateWidget() for field in INVESTIGATION_DATE_FIELDS
            # },
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.data:
            filter_q = Q()
            self.all_input_numbers = []  # Сохранение всех введенных номеров

            if self.data.get("sender_numbers"):
                sender_list = [
                    num.strip() for num in self.data["sender_numbers"].split(",")
                ]
                self.all_input_numbers.extend(sender_list)
                filter_q |= Q(sender_outgoing_number__in=sender_list)

            if self.data.get("consumer_act_numbers"):
                consumer_list = [
                    num.strip() for num in self.data["consumer_act_numbers"].split(",")
                ]
                self.all_input_numbers.extend(consumer_list)
                filter_q |= Q(consumer_act_number__in=consumer_list)

            if self.data.get("end_consumer_act_numbers"):
                end_consumer_list = [
                    num.strip()
                    for num in self.data["end_consumer_act_numbers"].split(",")
                ]
                self.all_input_numbers.extend(end_consumer_list)
                filter_q |= Q(end_consumer_act_number__in=end_consumer_list)

            self.filtered_reclamations = Reclamation.objects.filter(filter_q)

    def clean(self):
        cleaned_data = super().clean()

        # Проверка полей поиска - специфичная только для этой формы
        if not any(
            [
                cleaned_data.get("sender_numbers"),
                cleaned_data.get("consumer_act_numbers"),
                cleaned_data.get("end_consumer_act_numbers"),
            ]
        ):
            raise forms.ValidationError(
                "Необходимо заполнить хотя бы одно поле с номерами актов"
            )

        # Проверка обязательности копии акта исследования
        if not cleaned_data.get("act_scan"):
            raise forms.ValidationError(
                {"act_scan": "Необходимо прикрепить копию акта исследования"}
            )

        # Проверяем, что даты не больше сегодняшней
        today = timezone.now().date()
        date_fields = [
            cleaned_data.get("act_date"),
            cleaned_data.get("shipment_date"),
            cleaned_data.get("disposal_act_date"),
            cleaned_data.get("shipment_invoice_date"),
        ]  # список полей с типом DateField

        errors = {}
        for field_name in date_fields:
            if field_name and field_name > today:
                errors[field_name] = "Дата не может быть больше сегодняшней"

        if errors:
            raise forms.ValidationError(errors)

        return cleaned_data


class UpdateInvoiceOutForm(forms.Form):
    """Форма группового добавления накладной отгрузки изделий"""

    act_numbers = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 3}),
        label="Номера актов исследования",
        help_text="(вводить через запятую, только номера без года, например: 123, 124, 125)",
        required=False,
    )
    sender_numbers = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 3}),
        label="Исходящий номер отправителя (ПСА)",
        help_text="(вводить через запятую)",
        required=False,
    )
    shipment_invoice_number = forms.CharField(
        label="Номер накладной отгрузки", required=True
    )
    shipment_invoice_date = forms.DateField(
        label="Дата накладной отгрузки",
        widget=forms.DateInput(attrs={"type": "date"}),
        required=True,
    )

    def clean(self):
        cleaned_data = super().clean()

        # Проверяем, что заполнено хотя бы одно поле с номерами
        if not any(
            [
                cleaned_data.get("act_numbers"),
                cleaned_data.get("sender_numbers"),
            ]
        ):
            raise forms.ValidationError(
                "Необходимо заполнить хотя бы одно поле с номерами актов или ПСА"
            )

        # Проверяем, что дата накладной не больше сегодняшней
        invoice_date = cleaned_data.get("shipment_invoice_date")
        if invoice_date and invoice_date > timezone.now().date():
            raise forms.ValidationError(
                {"shipment_invoice_date": "Дата не может быть больше сегодняшней"}
            )

        return cleaned_data


class InvestigationAdminForm(forms.ModelForm):
    """Основная форма для редактирования Investigation в админке"""

    class Meta:
        model = Investigation
        fields = "__all__"

        widgets = {
            "fault_type": forms.RadioSelect(),  # Виджет RadioSelect для fault_type
            **{  # Настройка текстовых полей - высота полей, перенос строк и запрет изменения размера
                field: forms.TextInput(
                    attrs={
                        "style": "width: 600px; text-overflow: ellipsis; resize: none;"
                    }
                )
                for field in INVESTIGATION_TEXT_FIELDS
            },
            # **{  # Виджет DateInput для полей дат
            #     field: forms.DateInput(attrs={"type": "date"}) for field in INVESTIGATION_DATE_FIELDS
            # },
            **{  # Виджет AdminDateWidget для полей дат
                field: AdminDateWidget() for field in INVESTIGATION_DATE_FIELDS
            },
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Фильтрация доступных рекламаций только для новых записей
        if not self.instance.pk:
            self.fields["reclamation"].queryset = Reclamation.objects.filter(
                investigation__isnull=True
            )

        # Настройка отображения поля для сохранения файла
        if self.instance.act_scan:
            self.fields["act_scan"].widget.initial_text = "Файл"
            self.fields["act_scan"].widget.input_text = "Заменить"
            self.fields["act_scan"].widget.clear_checkbox_label = "Удалить"
