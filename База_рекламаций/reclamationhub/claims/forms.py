from django import forms
from django.contrib.admin.widgets import AdminDateWidget
from django.db.models import Q
from django.utils import timezone
from datetime import datetime

from .models import Claim
from reclamations.models import Reclamation
from investigations.models import Investigation


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
        exclude = ["reclamations"]  # полностью исключаем из формы

        widgets = {
            # "result_claim": forms.RadioSelect(),  # RadioSelect для результата
            "comment": forms.Textarea(attrs={"rows": 2}),
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

        # Валидация рекламационного акта, двигателя или акта исследования для установления связи с рекламацией
        # Если это редактирование существующей претензии - проверка не нужна
        if self.instance.pk and self.instance.reclamations.exists():
            return cleaned_data

        reclamation_act_number = cleaned_data.get("reclamation_act_number")
        reclamation_act_date = cleaned_data.get("reclamation_act_date")
        engine_number = cleaned_data.get("engine_number")
        investigation_act_number = cleaned_data.get("investigation_act_number")
        comment = cleaned_data.get("comment", "")

        # Ищем рекламации (может быть несколько)
        # found_reclamations = self._find_reclamations(reclamation_act_number, engine_number)
        found_reclamations = self._find_reclamations(
            reclamation_act_number,
            reclamation_act_date,
            engine_number,
            investigation_act_number,
        )

        if found_reclamations:
            # Рекламация найдена - все отлично. Сохраняем рекламацию для save_model.
            self._found_reclamations = found_reclamations
        else:
            # Рекламации НЕ найдены - требуем комментарий
            if reclamation_act_number or engine_number or investigation_act_number:
                if not comment:
                    raise forms.ValidationError(
                        "Рекламация не найдена. Для сохранения претензии без связи "
                        "необходимо заполнить поле 'Комментарий' с объяснением."
                    )

                # Показываем предупреждение, но НЕ блокируем сохранение
                self._warning_message = (  # Сохраняем предупреждение для показа после сохранения
                    "Внимание: рекламация с указанными данными не найдена. "
                    "Претензия сохранена без связи с рекламацией."
                )
            else:
                # Если вообще ничего не указано - требуем хотя бы один из критериев
                raise forms.ValidationError(
                    "Рекламация не найдена. Для сохранения претензии без связи "
                    "необходимо указать либо номер и дату рекламационного акта, "
                    "либо номер двигателя, либо номер акта исследования, "
                    "либо заполнить комментарий."
                )

        return cleaned_data

    def _find_reclamations(
        self,
        reclamation_act_number,
        reclamation_act_date,
        engine_number,
        investigation_act_number,
    ):
        """Возвращает список найденных рекламаций"""

        # 1. Поиск по номеру акта рекламации (ВЫСШИЙ ПРИОРИТЕТ)
        if reclamation_act_number:
            # Если есть дата - ищем точно по номеру и дате
            if reclamation_act_date:
                try:
                    # Проверяем, что за объект в reclamation_act_date
                    if isinstance(reclamation_act_date, str):
                        # Если строка - преобразуем
                        search_date_obj = datetime.strptime(
                            reclamation_act_date, "%Y-%m-%d"
                        ).date()
                    else:
                        # Если уже date объект - используем как есть
                        search_date_obj = reclamation_act_date

                    return Reclamation.objects.filter(
                        Q(
                            sender_outgoing_number=reclamation_act_number,
                            message_sent_date=search_date_obj,
                        )
                        | Q(
                            consumer_act_number=reclamation_act_number,
                            consumer_act_date=search_date_obj,
                        )
                        | Q(
                            end_consumer_act_number=reclamation_act_number,
                            end_consumer_act_date=search_date_obj,
                        )
                    )
                except Exception:
                    pass

            # Если даты нет - ищем только по номеру
            return Reclamation.objects.filter(
                Q(sender_outgoing_number=reclamation_act_number)
                | Q(consumer_act_number=reclamation_act_number)
                | Q(end_consumer_act_number=reclamation_act_number)
            )

        # 2. Поиск по номеру двигателя
        elif engine_number:
            return Reclamation.objects.filter(engine_number=engine_number)

        # 3. Поиск по номеру акта исследования
        elif investigation_act_number:
            try:
                investigation = Investigation.objects.get(
                    act_number=investigation_act_number
                )
                return Reclamation.objects.filter(id=investigation.reclamation.id)
            except Investigation.DoesNotExist:
                pass

        return Reclamation.objects.none()
