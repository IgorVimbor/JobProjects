from django.contrib import admin, messages
from django.contrib.admin import SimpleListFilter
from django.http import HttpResponseRedirect
from django.urls import path, reverse
from django.utils.safestring import mark_safe
from django.db.models import Count, Prefetch
from datetime import datetime

from reclamationhub.admin import admin_site
from reclamations.models import Reclamation
from claims.models import Claim
from .models import Investigation
from .forms import InvestigationAdminForm
from .views.add_group_investigation import add_group_investigation_view
from .views.add_invoice_out import add_invoice_out_view


class InvestigationYearListFilter(SimpleListFilter):
    """Класс для переопределения фильтра по году рекламации в админке InvestigationAdmin"""

    title = "Год исследований"
    parameter_name = "reclamation__year"

    def lookups(self, request, model_admin):
        # Получаем все годы из рекламаций и сортируем по убыванию
        years = (
            Reclamation.objects.values_list("year", flat=True)
            .distinct()
            .order_by("-year")
        )
        return [(year, str(year)) for year in years]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(reclamation__year=self.value())
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

    @admin.display(description="Претензия")
    def has_claim(self, obj):
        """Метод для отображения номера претензии как ссылки (оптимизация для ManyToManyField)"""
        # Проверяем, есть ли связанная рекламация (быстрая проверка через аннотацию)
        if getattr(obj, "claims_count", 0) == 0:
            return ""

        # Используем prefetch_related данные (без дополнительных запросов)
        claims = obj.reclamation.claims.all()

        if not claims:
            return ""

        # Формируем список ссылок
        links = []
        for claim in claims:
            # Базовый URL списка претензий
            url = reverse("admin:claims_claim_changelist")
            # Добавляем фильтрацию по номеру регистрации
            filtered_url = f"{url}?registration_number={claim.registration_number}"

            link = (
                f'<a href="{filtered_url}" '
                f'target="_blank" '
                f'rel="noopener" '
                f"onmouseover=\"this.style.fontWeight='bold'\" "
                f"onmouseout=\"this.style.fontWeight='normal'\" "
                f'title="Перейти к претензии">'
                f"{claim.registration_number}</a>"
            )
            links.append(link)

        # Возвращаем список через <br> (вертикально)
        return mark_safe("<br>".join(links))

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
        "has_claim",  # претензия
    ]

    exclude = ["act_number_sort"]  # Скрываем поле в админ-панели

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
    # list_filter = ['reclamation__year', "reclamation__defect_period", "reclamation__product__product_type"]
    list_filter = [
        InvestigationYearListFilter,
        "reclamation__defect_period",
        "reclamation__product__product_type",
    ]

    # Поля для поиска
    search_fields = [
        "act_number",  # номер акта исследования
        "reclamation__product__nomenclature",  # обозначение изделия
        "reclamation__product_number",  # номер изделия
        "reclamation__engine_number",  # номер двигателя
        "shipment_invoice_number",  # накладная отгрузки (расхода)
    ]

    search_help_text = mark_safe(
        """
    <p>ПОИСК ПО ПОЛЯМ:</p>
    <ul>
        <li>НОМЕР АКТА ИССЛЕДОВАНИЯ ••• ОБОЗНАЧЕНИЕ ИЗДЕЛИЯ</li>
        <li>НОМЕР ИЗДЕЛИЯ ••• НОМЕР ДВИГАТЕЛЯ ••• НАКЛАДНАЯ РАСХОДА</li>
    </ul>
    """
    )

    # Сортировка по умолчанию
    # ordering = ["reclamation"]
    ordering = ["-act_number_sort", "-act_date"]

    # def get_queryset(self, request):
    #     return (
    #         super()
    #         .get_queryset(request)
    #         .select_related(
    #             "reclamation",  # для доступа к pk рекламации
    #             "reclamation__product",  # для product в admin_display_by_reclamation
    #             "reclamation__product_name",  # для product_name в admin_display_by_reclamation
    #         )
    #     )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related(
                "reclamation",  # для доступа к pk рекламации
                "reclamation__product",  # для product в admin_display_by_reclamation
                "reclamation__product__product_type",  # наименование изделия для list_filter
                "reclamation__product_name",  # для product_name в admin_display_by_reclamation
                "reclamation__defect_period",  # период дефекта для list_filter
            )
            .defer(
                # Исключаем ненужные поля reclamation
                "reclamation__incoming_number",
                "reclamation__sender",
                "reclamation__sender_outgoing_number",
                "reclamation__message_sent_date",
                "reclamation__manufacture_date",
                "reclamation__purchaser",
                "reclamation__country_rejected",
                "reclamation__end_consumer",
                "reclamation__engine_brand",
                "reclamation__engine_number",
                "reclamation__transport_name",
                "reclamation__transport_number",
                "reclamation__defect_detection_date",
                "reclamation__away_type",
                "reclamation__mileage_operating_time",
                "reclamation__claimed_defect",
                "reclamation__consumer_requirement",
                "reclamation__products_count",
                "reclamation__measures_taken",
                "reclamation__outgoing_document_number",
                "reclamation__outgoing_document_date",
                "reclamation__letter_sending_method",
                "reclamation__consumer_response",
                "reclamation__consumer_response_number",
                "reclamation__consumer_response_date",
                "reclamation__volume_removal_reference",
                "reclamation__reclamation_documents",
                "reclamation__product_received_date",
                "reclamation__product_sender",
                "reclamation__receipt_invoice_number",
                "reclamation__receipt_invoice_date",
                "reclamation__updated_at",
            )
            .prefetch_related(
                Prefetch(
                    "reclamation__claims",
                    queryset=Claim.objects.only("registration_number", "id"),
                )
            )
            .annotate(claims_count=Count("reclamation__claims", distinct=True))
        )

    # Добавляем URL для групповой формы
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(  # для группового акта исследования
                "add_group_investigation/",
                self.add_group_investigation_view,
                name="add_group_investigation",
            ),
            path(  # для групповой накладной расхода
                "add_invoice_out/",
                self.add_invoice_out_view,
                name="add_invoice_out",
            ),
        ]
        return custom_urls + urls

    def changelist_view(self, request, extra_context=None):
        """Метод для настройки вывода актов исследования по текущему году по умолчанию"""
        # Проверяем есть ли фильтр по году от пользователя
        user_year_filter = "reclamation__year" in request.GET
        auto_year_filter = "reclamation__year__exact" in request.GET

        if user_year_filter and auto_year_filter:
            # Конфликт! Удаляем автоматический фильтр
            request.GET = request.GET.copy()
            del request.GET["reclamation__year__exact"]

        elif not user_year_filter and not auto_year_filter:
            # Никаких фильтров нет - добавляем текущий год
            current_year = datetime.now().year
            request.GET = request.GET.copy()
            request.GET["reclamation__year__exact"] = current_year

        return super().changelist_view(request, extra_context)

    def add_group_investigation_view(self, request):
        """Метод добавления группового акта исследования - делегируем вызов функции из views"""
        # Здесь используется self, а во views.py параметр admin_instance
        return add_group_investigation_view(self, request)

    def add_invoice_out_view(self, request):
        """Метод группового добавления накладной отгрузки изделий - делегируем вызов функции из views"""
        # Здесь используется self, а во views.py параметр admin_instance
        return add_invoice_out_view(self, request)

    # def get_form(self, request, obj=None, **kwargs):
    #     form = super().get_form(request, obj, **kwargs)

    #     # Делаем поле обязательным
    #     form.base_fields["reclamation"].required = True

    #     # Устанавливаем начальное значение из GET-параметра
    #     if not obj and "reclamation" in request.GET:
    #         form.base_fields["reclamation"].initial = request.GET.get("reclamation")

    #     return form

    def get_form(self, request, obj=None, **kwargs):
        """Передаем request в форму"""
        form_class = super().get_form(request, obj, **kwargs)

        class FormWithRequest(form_class):
            def __init__(self, *args, **kwargs):
                kwargs["request"] = request
                super().__init__(*args, **kwargs)

        return FormWithRequest

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
