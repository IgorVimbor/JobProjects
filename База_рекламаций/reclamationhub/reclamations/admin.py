from django.contrib import admin, messages
from django.contrib.admin import SimpleListFilter
from django.utils.html import format_html
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import path, reverse
from django.utils.safestring import mark_safe
from datetime import datetime

from reclamationhub.admin import admin_site
from reclamations.models import Reclamation
from reclamations.forms import ReclamationAdminForm
from reclamations.views.invoice_intake import add_invoice_into_view
from reclamations.views.disposal_act import add_disposal_act_view


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
        "has_claim",  # претензия
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

    # add_measures.short_description = "Редактировать запись"  # вариант присваивания наименования

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
        """Метод группового добавления акта утилизации - делегируем вызов к функции из views.py"""
        # Здесь используется self, а во views.py параметр admin_instance в функции -
        # через него передаем ссылку на ReclamationAdmin для вызова message_user.
        return add_disposal_act_view(self, request, queryset)

    @admin.display(description="Номер рекламации")
    def display_number(self, obj):
        """Метод для отображения номера рекламации с учетом года (например, 2025-0001)"""
        return f"{obj.year}-{obj.yearly_number:04d}"

    # display_number.short_description = 'Номер рекламации'  # вариант присваивания наименования

    @admin.display(description="Статус рекламации")
    def status_colored(self, obj):
        """Метод для цветового отображения статуса рекламации"""
        colors = {"NEW": "blue", "IN_PROGRESS": "orange", "CLOSED": "green"}
        return format_html(
            '<span style="color: {};">{}</span>',
            colors[obj.status],
            obj.get_status_display(),
        )

    # @admin.display(description="Исследование")
    # def has_investigation_icon(self, obj):
    #     """Метод для отображения номера акта исследования"""
    #     if obj.has_investigation:
    #         return obj.investigation.act_number
    #     return ""

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
                f'target="_blank" '  # открывать в новой вкладке
                f'rel="noopener" '  # для безопасности (предотвращает доступ новой вкладки к родительскому окну)
                f"onmouseover=\"this.style.fontWeight='bold'\" "  # жирный шрифт при наведении
                f"onmouseout=\"this.style.fontWeight='normal'\" "  # нормальный шрифт
                f'title="Перейти к акту исследования">'  # подсказка при наведении
                f"{obj.investigation.act_number}</a>"
            )
        return ""

    @admin.display(description="Претензия")
    def has_claim(self, obj):
        """Метод для отображения номера претензии как ссылки"""
        claims = obj.claims.all()

        if not claims.exists():
            return ""

        # Формируем список ссылок (вертикально)
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
        ]
        return custom_urls + urls

    # def add_invoice_into_view(self, request):
    #     """Метод группового добавления накладной прихода рекламационных изделий"""
    #     # Здесь используется self, а во views.py параметр admin_instance в функции -
    #     # через него передаем ссылку на ReclamationAdmin для вызова message_user.

    def add_invoice_into_view(self, request):
        """Метод добавления группового акта исследования - делегируем вызов к функции из views.py"""
        return add_invoice_into_view(self, request)
