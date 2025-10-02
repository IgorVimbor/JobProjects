from django.contrib import admin, messages
from django.contrib.admin.widgets import AdminDateWidget
from django.contrib.admin import SimpleListFilter
from django.utils.html import format_html
from django import forms
from django.utils import timezone
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import path, reverse
from django.db.models import Q
from django.utils.safestring import mark_safe
from datetime import datetime

from reclamationhub.admin import admin_site
from .models import Reclamation
from sourcebook.models import Product

# from utils.excel.exporters import ReclamationExcelExporter


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
        # список полей с типом CharField для которых добавим возможность переноса строк
        text_fields = [
            "consumer_requirement",
            "measures_taken",
            "consumer_response",
            "pkd_number",
            "reclamation_documents",
        ]
        date_fields = [
            "message_received_date",
            "message_sent_date",
            "consumer_act_date",
            "end_consumer_act_date",
            "defect_detection_date",
            "outgoing_document_date",
            "consumer_response_date",
            "product_received_date",
            "receipt_invoice_date",
        ]  # список полей с типом DateField

        widgets = {
            "away_type": forms.RadioSelect(),  # Добавляем RadioSelect для away_type
            **{  # устанавливаем высоту полей, возможность переноса строк и отключаем изменения размера
                field: forms.TextInput(
                    attrs={
                        "style": "width: 600px; text-overflow: ellipsis; resize: none;"
                    }
                )
                for field in text_fields
            },
            # **{  # устанавливаем виджет DateInput для полей дат
            #     field: forms.DateInput(attrs={"type": "date"}) for field in date_fields
            # },
            **{  # устанавливаем виджет AdminDateWidget для полей дат
                field: AdminDateWidget() for field in date_fields
            },
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


class YearListFilter(SimpleListFilter):
    """Класс для переопределения фильтра по году рекламации"""

    title = "Год рекламации"
    parameter_name = "year"

    def lookups(self, request, model_admin):
        # Получаем все годы и сортируем по убыванию: 2026, 2025, 2024...
        years = (
            Reclamation.objects.values_list("year", flat=True)
            .distinct()
            .order_by("-year")
        )
        return [(year, str(year)) for year in years]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(year=self.value())
        return queryset

    def choices(self, changelist):
        # Подсвечиваем текущий год как выбранный по умолчанию
        current_year = datetime.now().year

        # Если не выбрано значение, считаем что выбран текущий год
        selected_value = self.value() or str(current_year)

        # Возвращаем варианты выбора
        for lookup, title in self.lookup_choices:
            yield {
                "selected": str(selected_value) == str(lookup),
                "query_string": changelist.get_query_string(
                    {self.parameter_name: lookup}
                ),
                "display": title,
            }


@admin.register(Reclamation, site=admin_site)
class ReclamationAdmin(admin.ModelAdmin):
    class Media:
        css = {"all": ("admin/css/custom_admin.css",)}
        js = ("admin/js/custom_admin.js", "admin/js/copy_act_fields.js")

    form = ReclamationAdminForm

    # Отображение кнопок сохранения сверху и снизу формы
    save_on_top = True

    list_per_page = 10  # количество записей на странице

    # Основные поля для отображения в списке
    list_display = [
        # "id",
        "display_number",  # номер рекламации с учетом года
        "status_colored",  # статус рекламации (Новая, В работе, Закрыта)
        "incoming_number",  # входящий № по ОТК
        "message_received_date",  #  дата поступления ссобщения
        "defect_period",  # период выявления дефекта
        "sender_outgoing_number",  # исходящий № отправителя
        "product_name",  # наименование изделия
        "product",  # обозначение изделия
        "product_number",  # заводской номер изделия
        "manufacture_date",  # дата изготовления
        "claimed_defect",  # дефект
        "consumer_act_number",  # номер акта приобретателя изделия
        "consumer_act_date",  # дата акта приобретателя изделия
        "end_consumer_act_number",  # номер акта конечного потребителя
        "end_consumer_act_date",  # дата акта конечного потребителя
        "engine_number",  # номер двигателя
        "mileage_operating_time",  # пробег/наработка
        "products_count",  # количество изделий
        "measures_taken",  # принятые меры
        "outgoing_document_number",  # номер исходящего документа
        "pkd_number",  # номер 8D или ПКД
        "volume_removal_reference",  # справка снятия с объёмов
        "receipt_invoice_number",  # номер накладной поступления изделия
        "receipt_invoice_date",  # дата накладной поступления изделия
        "has_investigation_icon",  # акт исследования
        "reclamation_documents",  # дополнительные сведения по рекламации
    ]

    # Группировка полей в форме редактирования
    fieldsets = [
        (
            "Информация о сообщении",
            {
                "fields": [
                    "incoming_number",
                    "message_received_date",
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
                    "defect_period",
                    "product_name",
                    "product",
                    "product_number",
                    "manufacture_date",
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
                    "away_type",
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
                ],
                "classes": ["measures-section"],  # добавляем класс для якоря
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
            "Корректирующие действия",
            {
                "fields": [
                    "pkd_number",
                    "volume_removal_reference",
                    "reclamation_documents",
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
                ]
            },
        ),
    ]

    # Фильтры
    # list_filter = ['year', "status", "defect_period", "product__product_type"]
    list_filter = [YearListFilter, "status", "defect_period", "product__product_type"]

    # Поиск
    search_fields = [
        "id",  # номер строки (ID записи)
        "sender_outgoing_number",  # исходящий № отправителя
        "product_number",  # номер изделия
        "engine_number",  # номер двигателя
        "consumer_act_number",  # номер акта приобретателя изделия
        "end_consumer_act_number",  # номер акта конечного потребителя
        "receipt_invoice_number",  # номер накладной прихода изделия
        "investigation__act_number",  # номер акта исследования
    ]

    search_help_text = mark_safe(
        """
    <p>ПОИСК ПО ПОЛЯМ:</p>
    <ul>
        <li>НОМЕР СТРОКИ (ID) ••• ИСХОДЯЩИЙ № ОТПРАВИТЕЛЯ (№ ПСА) ••• НОМЕР ИЗДЕЛИЯ ••• НОМЕР ДВИГАТЕЛЯ</li>
        <li>НОМЕР АКТА РЕКЛАМАЦИИ ПРИОБРЕТАТЕЛЯ ИЛИ ПОТРЕБИТЕЛЯ ••• НОМЕР НАКЛАДНОЙ ПРИХОДА ••• НОМЕР АКТА ИССЛЕДОВАНИЯ</li>
    </ul>
    """
    )

    # Метод get_queryset с select_related используется для оптимизации запросов к базе данных.
    # Без select_related будет N+1 запросов (1 запрос для списка рекламаций + N запросов для связанных данных)
    # С select_related будет только 1 запрос
    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("product_name", "product", "defect_period")
        )

    def changelist_view(self, request, extra_context=None):
        """Метод для настройки вывода рекламаций по текущему году по умолчанию"""
        # Проверяем есть ли фильтр по году от пользователя
        user_year_filter = "year" in request.GET
        auto_year_filter = "year__exact" in request.GET

        if user_year_filter and auto_year_filter:
            # Конфликт! Удаляем автоматический фильтр
            request.GET = request.GET.copy()
            del request.GET["year__exact"]

        elif not user_year_filter and not auto_year_filter:
            # Никаких фильтров нет - добавляем текущий год
            current_year = datetime.now().year
            request.GET = request.GET.copy()
            request.GET["year__exact"] = current_year

        return super().changelist_view(request, extra_context)

    # ----------------------------- Вспомогательные методы для отображения -----------------------------------

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

    # Добавляем действия в панель "Действие / Выполнить"
    actions = ["add_measures", "add_investigation", "add_disposal_act"]

    @admin.action(description="Редактировать запись")
    def add_measures(self, request, queryset):
        """Действие для редактирования рекламации"""
        # Если выбрано больше одной записи
        if queryset.count() > 1:
            self.message_user(
                request,
                "Выберите только одну рекламацию для редактирования",
                level="ERROR",
            )
            return

        # Получаем выбранную запись
        reclamation = queryset.first()

        # Перенаправляем на форму редактирования с фокусом на секции "Принятые меры"
        return HttpResponseRedirect(
            f"../reclamation/{reclamation.pk}/change/#measures-section"
        )

    # add_measures.short_description = "Редактировать запись"

    @admin.action(description="Добавить акт исследования для рекламации")
    def add_investigation(self, request, queryset):
        # Проверяем, что выбрана только одна запись
        if queryset.count() != 1:
            self.message_user(
                request,
                "Выберите только одну рекламацию",
                level="ERROR",
            )
            return

        # # Получаем выбранную запись
        reclamation = queryset.first()

        # Перенаправляем на форму создания акта
        return HttpResponseRedirect(
            f"/admin/investigations/investigation/add/?reclamation={reclamation.id}"
        )

    @admin.action(description="Добавить акт утилизации для выбранных рекламаций")
    def add_disposal_act(self, request, queryset):
        # Если форма отправлена (POST-запрос)
        if "apply" in request.POST:
            disposal_act_number = request.POST.get("disposal_act_number")
            disposal_act_date = request.POST.get("disposal_act_date")

            if not disposal_act_number or not disposal_act_date:
                self.message_user(
                    request,
                    "Укажите номер и дату акта утилизации",
                    level="ERROR",
                )
                return HttpResponseRedirect(".")

            success_count = 0
            error_count = 0
            no_investigation_count = 0

            for reclamation in queryset:
                if not hasattr(reclamation, "investigation"):
                    no_investigation_count += 1
                    continue

                try:
                    investigation = reclamation.investigation
                    investigation.disposal_act_number = disposal_act_number
                    investigation.disposal_act_date = disposal_act_date
                    investigation.save()
                    success_count += 1
                except Exception as e:
                    error_count += 1
                    self.message_user(
                        request,
                        f"Ошибка при обновлении акта утилизации для рекламации {reclamation.id}: {str(e)}",
                        level="ERROR",
                    )

            if success_count:
                self.message_user(
                    request,
                    f"Акт утилизации успешно добавлен для {success_count} рекламации(-ий)",
                )
            if no_investigation_count:
                self.message_user(
                    request,
                    f"Пропущено {no_investigation_count} рекламаций без актов исследования",
                    level="WARNING",
                )

            return HttpResponseRedirect(".")

        # Если это первый запрос (GET-запрос), показываем форму
        context = {
            "title": "Добавление акта утилизации",
            "reclamations": queryset,
            "count": queryset.count(),
            "opts": self.model._meta,
            "action": "add_disposal_act",
            "action_checkbox_name": admin.helpers.ACTION_CHECKBOX_NAME,
        }
        return render(request, "admin/add_disposal_act.html", context)

    @admin.display(description="Номер рекламации")
    def display_number(self, obj):
        """Метод для отображения номера рекламации с учетом года (например, 2025-0001)"""
        return f"{obj.year}-{obj.yearly_number:04d}"

    # display_number.short_description = 'Номер рекламации'

    @admin.display(description="Статус рекламации")
    def status_colored(self, obj):
        """Метод для цветового отображения статуса рекламации"""
        colors = {"NEW": "blue", "IN_PROGRESS": "orange", "CLOSED": "green"}
        return format_html(
            '<span style="color: {};">{}</span>',
            colors[obj.status],
            obj.get_status_display(),
        )

    # status_colored.short_description = "Статус"

    # @admin.display(description="Исследование")
    # def has_investigation_icon(self, obj):
    #     """Метод для отображения номера акта исследования"""
    #     if obj.has_investigation:
    #         return obj.investigation.act_number
    #     return ""
    # вариант присваивания наименования has_investigation_icon.short_description = "Исследование"

    @admin.display(description="Исследование")
    def has_investigation_icon(self, obj):
        """Метод для отображения номера акта исследования как ссылки"""
        if obj.has_investigation:
            # Получаем базовый URL
            url = reverse("admin:investigations_investigation_changelist")
            # Добавляем параметр фильтрации по номеру акта
            filtered_url = f"{url}?act_number={obj.investigation.act_number}"
            # return mark_safe(
            #     f'<a href="{filtered_url}">{obj.investigation.act_number}</a>'
            # )
            return mark_safe(
                f'<a href="{filtered_url}" '
                f"onmouseover=\"this.style.fontWeight='bold'\" "  # жирный шрифт при наведении
                f"onmouseout=\"this.style.fontWeight='normal'\" "  # нормальный шрифт
                f'title="Перейти к акту исследования">'  # подсказка при наведении
                f"{obj.investigation.act_number}</a>"
            )
        return ""

    def response_add(self, request, obj, post_url_continue=None):
        """Переопределяем стандартный метод вывода сообщения при добавлении рекламации"""
        storage = messages.get_messages(request)
        storage.used = True  # Очищаем стандартное сообщение

        self.message_user(
            request, f"Рекламация <{obj}> была успешно добавлена.", messages.SUCCESS
        )
        return super().response_add(request, obj, post_url_continue)

    def response_change(self, request, obj):
        """Переопределяем стандартный метод вывода сообщения при изменении рекламации"""
        storage = messages.get_messages(request)
        storage.used = True  # Очищаем стандартное сообщение

        self.message_user(
            request, f"Рекламация <{obj}> была успешно изменена.", messages.SUCCESS
        )

        return super().response_change(request, obj)

    def save_model(self, request, obj, form, change):
        """
        Переопределяем стандартный метод сохранения для обновления статуса рекламации
        и добавления суффикса к пробегу
        """
        # Добавляем суффикс к пробегу/наработке в зависимости от типа
        if (
            obj.away_type == Reclamation.AwayType.KILOMETRE
            and not obj.mileage_operating_time.endswith(" км")
        ):
            obj.mileage_operating_time = f"{obj.mileage_operating_time} км"
        elif (
            obj.away_type == Reclamation.AwayType.MOTO
            and not obj.mileage_operating_time.endswith(" м/ч")
        ):
            obj.mileage_operating_time = f"{obj.mileage_operating_time} м/ч"
        # В базу данных записываем "ПСИ", если выбрано "ПСИ"
        elif obj.away_type == Reclamation.AwayType.PSI:
            obj.mileage_operating_time = "ПСИ"

        # Обновление статуса рекламации при добавлении или удалении накладной
        if change and "receipt_invoice_number" in form.changed_data:
            old_obj = Reclamation.objects.get(pk=obj.pk)

            # Если статус "Новая" и введена накладная - изменяем статус на "В работе"
            if obj.receipt_invoice_number and obj.is_new():
                obj.status = Reclamation.Status.IN_PROGRESS

            # Если статус "В работе" и была накладная, но поле стало пустым - изменяем статус на "Новая"
            elif (
                old_obj.receipt_invoice_number
                and not obj.receipt_invoice_number
                and obj.status == Reclamation.Status.IN_PROGRESS
            ):
                obj.status = Reclamation.Status.NEW

        super().save_model(request, obj, form, change)

    # Автозаполнение для связанных полей
    autocomplete_fields = ["product_name", "product"]

    # Быстрый поиск по ID
    raw_id_fields = ["product_name", "product"]

    # Сортировка по умолчанию
    ordering = ["-id"]

    # Добавляем шаблон формы, где можно будет ввести номера актов и номер накладной
    change_list_template = "admin/reclamation_changelist.html"

    # Добавляем URL
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(  # для групповой накладной прихода
                "add_invoice_into/", self.add_invoice_into_view, name="add_invoice_into"
            ),
            path(  # для добавления акта утилизации
                "add_disposal_act/", self.add_disposal_act, name="add_disposal_act"
            ),
            # # для выгрузки в Excel
            # path("export-excel/", self.export_excel, name="export_excel"),
        ]
        return custom_urls + urls

    def add_invoice_into_view(self, request):
        """Метод группового добавления накладной прихода рекламационных изделий"""
        context_vars = {
            "opts": Reclamation._meta,
            "app_label": Reclamation._meta.app_label,
            "has_view_permission": True,
            "original": None,
        }

        if request.method == "POST":
            form = UpdateInvoiceNumberForm(request.POST)
            if form.is_valid():
                received_date = form.cleaned_data["received_date"]
                product_sender = form.cleaned_data["product_sender"]
                invoice_number = form.cleaned_data["invoice_number"]
                invoice_date = form.cleaned_data["invoice_date"]

                # Собираем все введенные номера
                all_input_numbers = []
                filter_q = Q()

                if form.cleaned_data["sender_numbers"]:
                    sender_list = [
                        num.strip()
                        for num in form.cleaned_data["sender_numbers"].split(",")
                    ]
                    all_input_numbers.extend(sender_list)
                    filter_q |= Q(sender_outgoing_number__in=sender_list)
                    # filter_q |= это операция побитового ИЛИ с присваиванием в Python,
                    # которая в контексте Django Q-объектов используется для объединения
                    # условий фильтрации через логическое ИЛИ (OR)

                if form.cleaned_data["consumer_act_numbers"]:
                    consumer_list = [
                        num.strip()
                        for num in form.cleaned_data["consumer_act_numbers"].split(",")
                    ]
                    all_input_numbers.extend(consumer_list)
                    filter_q |= Q(consumer_act_number__in=consumer_list)

                if form.cleaned_data["end_consumer_act_numbers"]:
                    end_consumer_list = [
                        num.strip()
                        for num in form.cleaned_data["end_consumer_act_numbers"].split(
                            ","
                        )
                    ]
                    all_input_numbers.extend(end_consumer_list)
                    filter_q |= Q(end_consumer_act_number__in=end_consumer_list)

                filtered_queryset = self.model.objects.filter(filter_q)

                # Проверяем отсутствующие номера
                found_numbers = set()
                all_reclamations = self.model.objects.all()

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

                # Проверяем, найдены ли записи
                if filtered_queryset.exists():
                    # Обновляем накладную и статус для записей со статусом NEW
                    updated_count = filtered_queryset.filter(
                        status=self.model.Status.NEW
                    ).update(
                        product_received_date=received_date,
                        product_sender=product_sender,
                        receipt_invoice_number=invoice_number,
                        receipt_invoice_date=invoice_date,
                        status=self.model.Status.IN_PROGRESS,
                    )

                    # Обновляем только накладную для остальных записей
                    other_updated = filtered_queryset.exclude(
                        status=self.model.Status.NEW
                    ).update(
                        product_received_date=received_date,
                        product_sender=product_sender,
                        receipt_invoice_number=invoice_number,
                        receipt_invoice_date=invoice_date,
                    )

                    total_updated = updated_count + other_updated
                    status_message = (
                        f"Изменен статус для записей: {updated_count}"
                        if updated_count
                        else ""
                    )

                    # Формируем сообщения
                    info_message = f"Введено номеров актов: {len(all_input_numbers)}"
                    success_message = f"Обновлены данные накладной для записей: {total_updated} {status_message}"

                    if missing_numbers:
                        missing_text = ", ".join(missing_numbers)
                        error_part = (
                            f"Номер акта отсутствующий в базе данных: {missing_text}"
                        )

                        # Три отдельных сообщения с разными уровнями
                        self.message_user(request, info_message, level=messages.INFO)
                        self.message_user(
                            request, success_message, level=messages.SUCCESS
                        )
                        self.message_user(request, error_part, level=messages.WARNING)
                    else:
                        # Два сообщения если все номера найдены
                        self.message_user(request, info_message, level=messages.INFO)
                        self.message_user(
                            request, success_message, level=messages.SUCCESS
                        )

                    return HttpResponseRedirect(request.get_full_path())
                else:
                    # Все номера отсутствуют
                    if missing_numbers:
                        missing_text = ", ".join(missing_numbers)
                        error_message = (
                            f"Номер акта отсутствующий в базе данных: {missing_text}"
                        )
                    else:
                        error_message = (
                            "Указанные номера актов в базе данных отсутствуют."
                        )

                    return render(
                        request,
                        "admin/add_group_invoice_into.html",
                        {
                            "title": "Добавление накладной прихода изделий",
                            "form": form,
                            "search_result": error_message,
                            "found_records": False,
                            **context_vars,
                        },
                    )
            else:
                return render(
                    request,
                    "admin/add_group_invoice_into.html",
                    {
                        "title": "Добавление накладной прихода изделий",
                        "form": form,
                        **context_vars,
                    },
                )
        else:
            form = UpdateInvoiceNumberForm()

        return render(
            request,
            "admin/add_group_invoice_into.html",
            {
                "title": "Добавление накладной прихода изделий",
                "form": form,
                **context_vars,
            },
        )

    # def export_excel(self, request):
    #     """Метод для выгрузки данных по рекламациям и актам исследования в Excel"""
    #     exporter = ReclamationExcelExporter()
    #     return exporter.export_to_excel()
