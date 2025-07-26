from django import forms
from .models import Reclamation

# Базовые проверки целостности данных делаем в модели, а проверки, связанные с пользовательским вводом - в формах.

# Добавить проверку ввода в поле "Пробег" только число + км или число + м/ч


class ReclamationForm(forms.ModelForm):
    class Meta:
        model = Reclamation
        fields = [
            "consumer_act_number",
            "consumer_act_date",
            "end_consumer_act_number",
            "end_consumer_act_date",
        ]

    def clean(self):
        """Валидация данных при заполнении формы"""
        cleaned_data = super().clean()

        # Получаем значения полей акта рекламации (покупателя и конечного потребителя)
        consumer_number = cleaned_data.get("consumer_act_number")
        consumer_date = cleaned_data.get("consumer_act_date")
        end_consumer_number = cleaned_data.get("end_consumer_act_number")
        end_consumer_date = cleaned_data.get("end_consumer_act_date")

        # Проверка, что хотя бы одна пара заполнена, сделана в модели Reclamation

        # Проверяем заполнение пар
        if (consumer_number and not consumer_date) or (
            not consumer_number and consumer_date
        ):
            raise forms.ValidationError(
                {
                    "consumer_act_number": "Необходимо заполнить оба поля (номер и дата акта приобретателя изделия)",
                    "consumer_act_date": "Необходимо заполнить оба поля (номер и дата акта приобретателя изделия)",
                }
            )

        if (end_consumer_number and not end_consumer_date) or (
            not end_consumer_number and end_consumer_date
        ):
            raise forms.ValidationError(
                {
                    "end_consumer_act_number": "Необходимо заполнить оба поля (номер и дата акта конечного потребителя)",
                    "end_consumer_act_date": "Необходимо заполнить оба поля (номер и дата акта конечного потребителя)",
                }
            )

        return cleaned_data
