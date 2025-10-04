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
        fields = "__all__"
        exclude = ["reclamation"]  # полностью исключаем из формы

        widgets = {
            "result": forms.RadioSelect(),  # RadioSelect для результата
            **{  # AdminDateWidget для полей дат
                field: AdminDateWidget() for field in CLAIM_DATE_FIELDS
            },
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Определяем текущую валюту
        if self.instance.pk and self.instance.type_money:
            currency = self.instance.type_money
        else:
            currency = "RUR"  # по умолчанию

        # Добавляем подписи с валютой
        self.fields["claim_amount_all"].help_text = f"Валюта: {currency}"
        self.fields["claim_amount_act"].help_text = f"Валюта: {currency}"
        self.fields["costs_act"].help_text = f"Валюта: {currency}"
        self.fields["costs_all"].help_text = f"Валюта: {currency}"

    def clean(self):
        cleaned_data = super().clean()

        # Валидация дат - не больше сегодняшней
        today = timezone.now().date()

        for field_name in CLAIM_DATE_FIELDS:
            field_value = cleaned_data.get(field_name)
            if field_value and field_value > today:
                self.add_error(field_name, "Дата не может быть больше сегодняшней")

        # Валидация сумм - не могут быть отрицательными и признанная не больше выставленной
        claim_amount = ("claim_amount_all", "claim_amount_act")
        bza_costs = ("costs_all", "costs_act")

        for claim_sum, bza_sum in zip(claim_amount, bza_costs):
            value_claim = cleaned_data.get(claim_sum)
            value_costs = cleaned_data.get(bza_sum)

            if value_claim is not None and value_claim < 0:
                self.add_error(claim_sum, "Сумма претензии не может быть отрицательной")

            if value_costs is not None and value_costs < 0:
                self.add_error(bza_sum, "Признанная сумма не может быть отрицательной")

            if (
                value_claim is not None
                and value_costs is not None
                and value_costs > value_claim
            ):
                self.add_error(
                    bza_sum, "Признанная сумма не может превышать сумму претензии"
                )

        # Валидация рекламационного акта и двигателя для установления связи с рекламацией
        # Если это редактирование существующей претензии - проверка не нужна
        if self.instance.pk and self.instance.reclamation:
            return cleaned_data

        reclamation_act_number = cleaned_data.get("reclamation_act_number")
        engine_number = cleaned_data.get("engine_number")

        # Ищем рекламацию
        found_reclamation = self._find_reclamation(
            reclamation_act_number, engine_number
        )

        if not reclamation_act_number and not engine_number:
            raise forms.ValidationError(
                "Необходимо указать либо номер и дату рекламационного акта, "
                "либо номер двигателя для поиска связанной рекламации."
            )

        if not found_reclamation:
            if reclamation_act_number:
                raise forms.ValidationError(
                    f'Рекламация с номером акта "{reclamation_act_number}" не найдена. '
                    f"Убедитесь, что рекламация существует в базе данных."
                )
            elif engine_number:
                raise forms.ValidationError(
                    f'Рекламация с номером двигателя "{engine_number}" не найдена. '
                    f"Убедитесь, что рекламация существует в базе данных."
                )
            else:
                raise forms.ValidationError(
                    "Необходимо указать либо номер и дату рекламационного акта, "
                    "либо номер двигателя для поиска связанной рекламации."
                )

        # Сохраняем найденную рекламацию для save_model
        self._found_reclamation = found_reclamation

        return cleaned_data

    def _find_reclamation(self, reclamation_act_number, engine_number):
        from django.db import models
        from reclamations.models import Reclamation

        if reclamation_act_number:
            return Reclamation.objects.filter(
                models.Q(sender_outgoing_number=reclamation_act_number)
                | models.Q(consumer_act_number=reclamation_act_number)
                | models.Q(end_consumer_act_number=reclamation_act_number)
            ).first()
        elif engine_number:
            return Reclamation.objects.filter(engine_number=engine_number).first()

        return None
