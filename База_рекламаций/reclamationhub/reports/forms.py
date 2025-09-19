# reports/forms.py
# Форма приложения "Поиск по номеру двигателя или акта рекламации"

from django import forms


class DbSearchForm(forms.Form):
    year = forms.IntegerField(
        label="Год поиска",
        min_value=2020,
        max_value=2030,
        initial=2025,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )

    engine_numbers = forms.CharField(
        label="Номера двигателей (через пробел)",
        widget=forms.Textarea(
            attrs={
                "rows": 3,
                "class": "form-control",
                "placeholder": "Введите номера двигателей через пробел",
            }
        ),
        required=False,
        help_text="Если в номере есть буквы, вводите только цифры",
    )

    act_numbers = forms.CharField(
        label="Номера актов рекламаций (через пробел)",
        widget=forms.Textarea(
            attrs={
                "rows": 3,
                "class": "form-control",
                "placeholder": "Введите номера актов через пробел",
            }
        ),
        required=False,
    )
