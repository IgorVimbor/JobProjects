from django import forms
from django.contrib.admin.widgets import AdminDateWidget
from django.utils import timezone

from .models import Claim
from reclamations.models import Reclamation


# Константы для виджетов форм
CLAIM_DATE_FIELDS = [
    "registration_date",
    "claim_date",
    "response_date",
]


class ClaimAdminForm(forms.ModelForm):
    """Основная форма для редактирования Claim в админке"""

    class Meta:
        model = Claim
        fields = [
            # Регистрация
            "registration_number",
            "registration_date",
            # Претензия
            "claim_number",
            "claim_date",
            "claim_amount_all",
            "reclamation_act_number",
            "reclamation_act_date",
            "claim_amount_act",
            # Результат рассмотрения
            "investigation_act_number",
            "investigation_act_date",
            "result",
            "comment",
            "costs_act",
            "costs_all",
            # Ответ БЗА
            "response_number",
            "response_date",
        ]

        widgets = {
            "result": forms.RadioSelect(),  # RadioSelect для результата
            **{  # AdminDateWidget для полей дат
                field: AdminDateWidget() for field in CLAIM_DATE_FIELDS
            },
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # # Фильтрация доступных рекламаций только для новых записей
        # if not self.instance.pk:
        #     self.fields["reclamation"].queryset = Reclamation.objects.filter(
        #         claim__isnull=True  # Только рекламации без претензий
        #     )

    def clean(self):
        cleaned_data = super().clean()

        # Валидация дат - не больше сегодняшней
        today = timezone.now().date()

        for field_name in CLAIM_DATE_FIELDS:
            field_value = cleaned_data.get(field_name)
            if field_value and field_value > today:
                self.add_error(field_name, "Дата не может быть больше сегодняшней")

        # Валидация сумм - не могут быть отрицательными
        claim_amount = ("claim_amount_all", "claim_amount_act")
        for value in claim_amount:
            value_amount = cleaned_data.get(value)
            if value_amount is not None and value_amount < 0:
                self.add_error(value, "Сумма претензии не может быть отрицательной")

        bza_costs = ("costs_all", "costs_act")
        for value in bza_costs:
            value_costs = cleaned_data.get(value)
            if value_costs is not None and value_costs < 0:
                self.add_error(value, "Признанная сумма не может быть отрицательной")

        # Проверка что признанная сумма не больше суммы претензии
        for claim_sum, bza_sum in zip(claim_amount, bza_costs):
            if claim_sum is not None and bza_sum is not None and bza_sum > claim_sum:
                self.add_error(
                    bza_sum, "Признанная сумма не может превышать сумму претензии"
                )

        return cleaned_data
