from django import forms
from django.contrib.admin.widgets import AdminDateWidget
from django.utils import timezone
import re

from sourcebook.models import Product
from .models import Reclamation


# ------------------------------ Константы для виджетов форм ----------------------------

# Список полей с типом CharField с возможностью переноса строк
RECLAMATION_TEXT_FIELDS = [
    "consumer_requirement",
    "measures_taken",
    "consumer_response",
    "pkd_number",
    "reclamation_documents",
]
# Список полей с типом DateField
RECLAMATION_DATE_FIELDS = [
    "message_received_date",
    "message_sent_date",
    "consumer_act_date",
    "end_consumer_act_date",
    "defect_detection_date",
    "outgoing_document_date",
    "consumer_response_date",
    "product_received_date",
    "receipt_invoice_date",
]


# ---------------------------- Формы приложения Reclamation -----------------------------


class UpdateInvoiceNumberForm(forms.Form):
    """Форма группового добавления накладной прихода рекламационных изделий.
    В поля формы вводятся номер отправителя (ПСА) и/или акта рекламации и номер накладной прихода
    """

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
    received_date = forms.DateField(
        label="Дата поступления изделий",
        widget=forms.DateInput(attrs={"type": "date"}),
        # widget=AdminDateWidget(),
        required=True,
    )
    product_sender = forms.CharField(
        max_length=200,
        label="Организация-отправитель изделия",
        required=True,
    )
    invoice_number = forms.CharField(label="Номер накладной", required=True)
    invoice_date = forms.DateField(
        label="Дата накладной",
        widget=forms.DateInput(attrs={"type": "date"}),
        # widget=AdminDateWidget(),
        required=True,
    )

    def clean(self):
        cleaned_data = super().clean()

        # Проверяем, что заполнено хотя бы одно поле с номерами актов
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

        # Проверяем, что дата накладной не больше сегодняшней
        invoice_date = cleaned_data.get("invoice_date")
        if invoice_date and invoice_date > timezone.now().date():
            raise forms.ValidationError(
                {"invoice_date": "Дата не может быть больше сегодняшней"}
            )

        return cleaned_data


class ReclamationAdminForm(forms.ModelForm):
    class Meta:
        model = Reclamation
        fields = "__all__"

        widgets = {
            "away_type": forms.RadioSelect(),  # Виджет RadioSelect для away_type
            **{  # Настройка текстовых полей - высота полей, перенос строк и запрет изменения размера
                field: forms.TextInput(
                    attrs={
                        "style": "width: 600px; text-overflow: ellipsis; resize: none;"
                    }
                )
                for field in RECLAMATION_TEXT_FIELDS
            },
            # **{  # Виджет DateInput для полей дат
            #     field: forms.DateInput(attrs={"type": "date"}) for field in date_fields
            # },
            **{  # Виджет AdminDateWidget для полей дат
                field: AdminDateWidget() for field in RECLAMATION_DATE_FIELDS
            },
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Убираем иконки действий для поля defect_period
        # (карандаш - редактировать, плюс - добавить, крестик - удалить, глаз - просмотр)
        self.fields["defect_period"].widget.can_add_related = False
        self.fields["defect_period"].widget.can_change_related = False
        self.fields["defect_period"].widget.can_delete_related = False
        self.fields["defect_period"].widget.can_view_related = False

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
        """Метод проверки данных, вводимых пользователем в форму"""
        cleaned_data = super().clean()

        # Проверяем соответствие продукта выбранному типу
        product = cleaned_data.get("product")
        product_name = cleaned_data.get("product_name")

        if product and product_name:
            if product.product_type_id != product_name.id:
                self.add_error(
                    "product", "Выбранное изделие не соответствует выбранному типу"
                )

        # Проверяем корректность номера изделия
        product_number = cleaned_data.get("product_number")
        if product_number:
            pattern = r"^\d+$"
            if not re.match(pattern, product_number):
                self.add_error(
                    "product_number",
                    "Введите только цифры или оставьте поле пустым при отсутствии данных",
                )

        # Проверяем корректность ввода даты изготовления (мм.гг)
        manufacture_date = cleaned_data.get("manufacture_date")
        if manufacture_date:
            pattern = r"^((0[1-9]|1[0-2])\.\d{2})$"
            if not re.match(pattern, manufacture_date):
                self.add_error(
                    "manufacture_date",
                    "Введите корректную дату в формате ММ.ГГ или оставьте поле пустым при отсутствии данных",
                )

        # Валидация пробега/наработки
        away_type = cleaned_data.get("away_type")
        mileage_operating_time = cleaned_data.get("mileage_operating_time")

        if away_type and mileage_operating_time:
            # Проверяем только для км и м/ч
            if away_type in [Reclamation.AwayType.KILOMETRE, Reclamation.AwayType.MOTO]:
                # Убираем пробелы по краям
                mileage_value = mileage_operating_time.strip()

                # Убираем единицы измерения если пользователь их ввел
                mileage_value = (
                    mileage_value.replace("км", "").replace("м/ч", "").strip()
                )

                if not mileage_value or mileage_value.lower() == "н/д":
                    self.add_error(
                        "mileage_operating_time",
                        "Для выбранной единицы измерения необходимо ввести числовое значение",
                    )
                else:
                    try:
                        # Заменяем запятую на точку для корректного преобразования
                        mileage_value = mileage_value.replace(",", ".")

                        # Преобразуем в число
                        numeric_value = float(mileage_value)

                        # Проверяем что число положительное
                        if numeric_value < 0:
                            self.add_error(
                                "mileage_operating_time",
                                "Значение пробега/наработки не может быть отрицательным",
                            )
                        else:
                            # ← ДЛЯ ОБЕИХ ЕДИНИЦ ИЗМЕРЕНИЯ приводим к целому числу
                            cleaned_data["mileage_operating_time"] = str(
                                int(numeric_value)
                            )

                    except ValueError:
                        self.add_error(
                            "mileage_operating_time",
                            "Введите корректное целое числовое значение (например: 1250)",
                        )

        return cleaned_data
