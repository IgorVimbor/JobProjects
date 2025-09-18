from django.contrib import admin, messages
from django.contrib.admin.widgets import AdminDateWidget
from django import forms
from django.http import HttpResponseRedirect
from django.db.models import Q
from django.utils import timezone
from django.urls import path
from django.shortcuts import render
from django.utils.safestring import mark_safe

from reclamationhub.admin import admin_site
from reclamations.models import Reclamation
from .models import Investigation


# список полей с типом CharField для которых добавим возможность переноса строк
INVESTIGATION_TEXT_FIELDS = [
    "defect_causes",
    "defect_causes_explanation",
    "return_condition_explanation",
]
# список полей с типом DateField
INVESTIGATION_DATE_FIELDS = [
    "act_date",
    "shipment_date",
    "disposal_act_date",
    "shipment_invoice_date",
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
            # Сначала поля поиска
            "sender_numbers",
            "consumer_act_numbers",
            "end_consumer_act_numbers",
            # Акт исследования
            "act_number",
            "act_date",
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
            "fault_type": forms.RadioSelect(),  # Добавляем RadioSelect для fault_type
            **{  # устанавливаем высоту полей, возможность переноса строк и отключаем изменения размера
                field: forms.TextInput(
                    attrs={
                        "style": "width: 600px; text-overflow: ellipsis; resize: none;"
                    }
                )
                for field in INVESTIGATION_TEXT_FIELDS
            },
            **{  # устанавливаем виджет DateInput для полей дат
                field: forms.DateInput(attrs={"type": "date"})
                for field in INVESTIGATION_DATE_FIELDS
            },
            # **{  # устанавливаем виджет AdminDateWidget для полей дат
            #     field: AdminDateWidget() for field in INVESTIGATION_DATE_FIELDS
            # },
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.data:
            filter_q = Q()
            self.all_input_numbers = []  # Добавляем сохранение всех введенных номеров

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


class InvestigationAdminForm(forms.ModelForm):
    class Meta:
        model = Investigation
        fields = "__all__"

        widgets = {
            "fault_type": forms.RadioSelect(),  # Добавляем RadioSelect для fault_type
            **{  # устанавливаем высоту полей, возможность переноса строк и отключаем изменения размера
                field: forms.TextInput(
                    attrs={
                        "style": "width: 600px; text-overflow: ellipsis; resize: none;"
                    }
                )
                for field in INVESTIGATION_TEXT_FIELDS
            },
            # **{  # устанавливаем виджет DateInput для полей дат
            #     field: forms.DateInput(attrs={"type": "date"}) for field in INVESTIGATION_DATE_FIELDS
            # },
            **{  # устанавливаем виджет AdminDateWidget для полей дат
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
            # self.fields["act_scan"].initial = self.instance.act_scan_filename


@admin.register(Investigation, site=admin_site)
class InvestigationAdmin(admin.ModelAdmin):

    class Media:
        css = {"all": ("admin/css/custom_admin.css",)}
        js = ("admin/js/custom_admin.js",)

    form = InvestigationAdminForm

    change_list_template = "admin/investigation_changelist.html"

    @admin.display(description="Рекламация: ID и изделие")
    def reclamation_display(self, obj):
        """Метод для отображения рекламации в админке (в две строки)"""
        return obj.reclamation.admin_display_by_reclamation()

    # reclamation_display.short_description = "Рекламация (ID и изделие)"

    @admin.display(description="Номер изделия")
    def product_number_display(self, obj):
        """Метод для отображения номера изделия из модели reclamation"""
        return obj.reclamation.product_number

    @admin.display(description="Номер и дата акта рекламации")
    def act_reclamation_display(self, obj):
        """Метод для отображения акта рекламации приобретателя в админке"""
        return obj.reclamation.admin_display_by_consumer_act()

    # act_reclamation_display.short_description = "Номер и дата акта рекламации"

    @admin.display(description="Период выявления дефекта")
    def get_defect_period(self, obj):
        """Метод для отображения поля "Период выявления дефекта" из модели reclamation"""
        return obj.reclamation.defect_period

    # get_defect_period.short_description = "Период выявления дефекта"

    @admin.display(description="Виновник дефекта")
    def get_fault_display(self, obj):
        """Метод для отображения виновника"""
        if obj.fault_type == Investigation.FaultType.BZA:
            return f"БЗА ({obj.guilty_department})" if obj.guilty_department else "БЗА"
        return obj.get_fault_type_display()

    # get_fault_display.short_description = "Виновник дефекта"

    @admin.display(description="Копия акта")
    def has_act_scan_icon(self, obj):
        """Отображение иконки наличия скана"""
        if obj.has_act_scan:
            return mark_safe(
                f'<div style="display: flex; justify-content: center; align-items: center; height: 100%;">'
                f'<a href="{obj.act_scan.url}" '
                f'target="_blank" '
                f'style="font-size: 24px; text-decoration: none;" '
                f'title="Открыть скан акта">'
                f"📄</a>"
                f"</div>"
            )
        return ""

    @admin.display(description="Номерок 8D (ПКД)")
    def has_pkd_number(self, obj):
        """Отображение номера 8D (ПКД) из модели reclamation при наличии"""
        return obj.reclamation.pkd_number

    # Отображаем все поля модели Investigation
    list_display = [
        "act_number",
        "act_date",
        "reclamation_display",
        "product_number_display",
        "get_defect_period",
        "act_reclamation_display",
        "solution",
        "get_fault_display",
        "defect_causes",
        "defect_causes_explanation",
        "defective_supplier",
        "shipment_date",
        "recipient",
        "has_act_scan_icon",
        "has_pkd_number",
        "disposal_act_number",
        "disposal_act_date",
        "shipment_invoice_number",
        "shipment_invoice_date",
        "return_condition",
        "return_condition_explanation",
    ]

    # Группировка полей
    fieldsets = [
        (
            "Акт исследования",
            {
                "fields": [
                    "reclamation",
                    "act_number",
                    "act_date",
                    "act_scan",
                ],
            },
        ),
        (
            "Решение по рекламации",
            {
                "fields": [
                    "solution",
                ],
            },
        ),
        (
            "Виновник дефекта и причины",
            {
                "fields": [
                    "fault_type",
                    "guilty_department",
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
                "classes": ["shipment-section"],
            },
        ),
        (
            "Утилизация",
            {
                "fields": [
                    "disposal_act_number",
                    "disposal_act_date",
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

    # Отображение кнопок сохранения сверху и снизу формы
    save_on_top = True

    list_per_page = 10  # количество записей на странице

    # Поля для фильтрации
    list_filter = [
        'reclamation__year',
        "reclamation__defect_period",
        "reclamation__product__product_type",
    ]

    # Поля для поиска
    search_fields = [
        "act_number",  # номер акта исследования
        "reclamation__product__nomenclature",  # обозначение изделия
        "reclamation__product_number",  # номер изделия
        "reclamation__engine_number",  # номер двигателя
    ]

    search_help_text = mark_safe(
        """
    <p>ПОИСК ПО ПОЛЯМ:</p>
    <ul>
        <li>НОМЕР АКТА ИССЛЕДОВАНИЯ ••• ОБОЗНАЧЕНИЕ ИЗДЕЛИЯ</li>
        <li>НОМЕР ИЗДЕЛИЯ ••• НОМЕР ДВИГАТЕЛЯ</li>
    </ul>
    """
    )

    # Сортировка по умолчанию
    ordering = ["reclamation"]

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related(
                "reclamation",  # для доступа к pk рекламации
                "reclamation__product",  # для product в admin_display_by_reclamation
                "reclamation__product_name",  # для product_name в admin_display_by_reclamation
            )
        )

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
        """Метод добавления группового акта исследования"""
        context_vars = {
            "opts": Investigation._meta,
            "app_label": Investigation._meta.app_label,
            "has_view_permission": True,
            "original": None,
        }

        if request.method == "POST":
            form = AddInvestigationForm(request.POST)

            if form.is_valid():
                reclamations = form.filtered_reclamations
                all_input_numbers = form.all_input_numbers

                # Проверяем отсутствующие номера ДО создания актов
                found_numbers = set()
                all_reclamations = Reclamation.objects.all()

                for num in all_input_numbers:
                    if all_reclamations.filter(
                        Q(sender_outgoing_number=num)
                        | Q(consumer_act_number=num)
                        | Q(end_consumer_act_number=num)
                    ).exists():
                        found_numbers.add(num)

                missing_numbers = [
                    num for num in all_input_numbers if num not in found_numbers
                ]

                if reclamations.exists():
                    # Создаем акты для найденных рекламаций
                    for reclamation in reclamations:
                        try:
                            investigation_fields = [
                                f
                                for f in form.Meta.fields
                                if f
                                not in [
                                    "sender_numbers",
                                    "consumer_act_numbers",
                                    "end_consumer_act_numbers",
                                ]
                            ]

                            investigation_data = {
                                field: form.cleaned_data[field]
                                for field in investigation_fields
                            }

                            investigation = Investigation(
                                reclamation=reclamation, **investigation_data
                            )
                            investigation.save()

                            reclamation.status = reclamation.Status.CLOSED
                            reclamation.save()

                        except Exception as e:
                            return render(
                                request,
                                "admin/add_group_investigation.html",
                                {
                                    "title": "Добавление группового акта исследования",
                                    "form": form,
                                    "search_result": f"Ошибка при сохранении: {str(e)}",
                                    "found_records": False,
                                    **context_vars,  # Добавляем переменные для breadcrumbs
                                },
                            )

                    # Формируем сообщение
                    info_message = f"Введено номеров актов: {len(all_input_numbers)}"
                    success_message = (
                        f"Создано актаов исследования: {reclamations.count()}"
                    )

                    if missing_numbers:
                        missing_text = ", ".join(missing_numbers)
                        error_part = (
                            f"Номер акта отсутствующий в базе данных: {missing_text}"
                        )

                        # Три отдельных сообщения с разными уровнями
                        self.message_user(  # Синее/серое
                            request, info_message, level=messages.INFO
                        )
                        self.message_user(  # Зеленое
                            request, success_message, level=messages.SUCCESS
                        )
                        self.message_user(  # Желтое
                            request, error_part, level=messages.WARNING
                        )
                    else:
                        # Два сообщения если все номера найдены
                        self.message_user(  # Синее/серое
                            request, info_message, level=messages.INFO
                        )
                        self.message_user(  # Зеленое
                            request, success_message, level=messages.SUCCESS
                        )

                    # остаемся на этой же странице
                    return HttpResponseRedirect(request.get_full_path())
                    # return HttpResponseRedirect("../")  # возвращает на страницу актов исследования
                else:
                    # Все номера отсутствуют
                    if missing_numbers:
                        missing_text = ", ".join(missing_numbers)
                        error_message = (
                            f"Номер акта отсутствующий в базе данных: {missing_text}"
                        )
                    else:
                        error_message = (
                            "Указанные номера актов в базе данных отсутствуют"
                        )

                    return render(
                        request,
                        "admin/add_group_investigation.html",
                        {
                            "title": "Добавление группового акта исследования",
                            "form": form,
                            "search_result": error_message,
                            "found_records": False,
                            **context_vars,  # Добавляем переменные для breadcrumbs
                        },
                    )
            else:
                return render(
                    request,
                    "admin/add_group_investigation.html",
                    {
                        "title": "Добавление группового акта исследования",
                        "form": form,
                        **context_vars,  # Добавляем переменные для breadcrumbs
                    },
                )
        else:
            form = AddInvestigationForm()

        return render(
            request,
            "admin/add_group_investigation.html",
            {
                "title": "Добавление группового акта исследования",
                "form": form,
                **context_vars,  # Добавляем переменные для breadcrumbs
            },
        )

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        # Делаем поле обязательным
        form.base_fields["reclamation"].required = True

        # Устанавливаем начальное значение из GET-параметра
        if not obj and "reclamation" in request.GET:
            form.base_fields["reclamation"].initial = request.GET.get("reclamation")

        return form

    def response_add(self, request, obj, post_url_continue=None):
        """Переопределяем стандартный метод вывода сообщения при добавлении акта"""
        storage = messages.get_messages(request)
        storage.used = True  # Очищаем стандартное сообщение

        self.message_user(request, f"{obj} был успешно добавлен.", messages.SUCCESS)
        return super().response_add(request, obj, post_url_continue)

    def response_change(self, request, obj):
        """Переопределяем стандартный метод вывода сообщения при изменении акта"""
        storage = messages.get_messages(request)
        storage.used = True  # Очищаем стандартное сообщение

        self.message_user(request, f"{obj} был успешно изменен.", messages.SUCCESS)
        return super().response_change(request, obj)

    def save_model(self, request, obj, form, change):
        """Проверка и изменение статуса рекламации на закрытую"""
        # Если есть номер и дата акта, закрываем рекламацию
        super().save_model(request, obj, form, change)
        obj.reclamation.update_status_on_investigation()
        if obj.act_number and obj.act_date and not obj.reclamation.is_closed():
            self.message_user(request, f"Рекламация {obj.reclamation} закрыта")

    def delete_model(self, request, obj):
        """Удаление акта исследования"""
        reclamation = obj.reclamation  # Сохраняем ссылку для сообщения
        # Удаляем объект (статус изменится в методе delete модели Investigation)
        super().delete_model(request, obj)

        self.message_user(
            request, f"Статус рекламации {reclamation} изменен на 'Исследование'"
        )

    # Добавляем действие в панель "Действие / Выполнить"
    actions = ["edit_shipment"]

    @admin.action(description="Редактировать запись")
    def edit_shipment(self, request, queryset):
        """Действие для редактирования даты отправки акта"""
        # Если выбрано больше одной записи
        if queryset.count() > 1:
            self.message_user(
                request,
                "Выберите только один акт исследования для редактирования",
                level="ERROR",
            )
            return

        # Получаем единственную выбранную запись
        investigation = queryset.first()

        # Перенаправляем на форму редактирования с фокусом на секции отправки
        return HttpResponseRedirect(
            f"../investigation/{investigation.pk}/change/#shipment-section"
        )

    # edit_shipment.short_description = "Редактировать запись"
