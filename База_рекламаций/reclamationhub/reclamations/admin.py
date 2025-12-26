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
from core.modules.search_mixin import ProductEngineSearchMixin
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
class ReclamationAdmin(ProductEngineSearchMixin, admin.ModelAdmin):
    """
    Миксин должен быть ПЕРВЫМ в списке наследования, чтобы его методы
    вызывались перед методами admin.ModelAdmin.

    MRO (Method Resolution Order):
    1. ReclamationAdmin
    2. ProductEngineSearchMixin
    3. admin.ModelAdmin
    4. object
    """

    class Media:
        css = {"all": ("admin/css/custom_admin.css",)}
        js = (
            "admin/js/custom_admin.js",
            "admin/js/reclamation_duplicates.js",
            "admin/js/reclamation_form.js",
        )

    form = ReclamationAdminForm

    # Добавляем шаблон формы
    change_list_template = "admin/reclamation_changelist.html"

    # Отображение кнопок сохранения сверху и снизу формы
    save_on_top = True

    list_per_page = 10  # количество записей на странице

    # Основные поля для отображения в списке
    list_display = [
        # "id",
        "display_number",  # номер рекламации с учетом года
        "status_colored",  # статус рекламации (Новая, В работе, Закрыта)
        "has_investigation_solution",  # решение по рекламации
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
        "consumer_response",  # ответ потребителя
        "consumer_response_number",  # номер ответа потребителя
        "pkd_number",  # номер 8D или ПКД
        "volume_removal_reference",  # справка снятия с объёмов
        "receipt_invoice_number",  # номер накладной поступления изделия
        "receipt_invoice_date",  # дата накладной поступления изделия
        "reclamation_documents",  # дополнительные сведения по рекламации
        "has_investigation_icon",  # акт исследования
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

    # Автозаполнение для связанных полей
    autocomplete_fields = ["product_name", "product"]

    # Сортировка по умолчанию
    ordering = ["-id"]

    # Фильтры
    # list_filter = ['year', "status", "defect_period", "product__product_type"]
    list_filter = [YearListFilter, "status", "defect_period", "product__product_type"]

    # Быстрый поиск по ID
    raw_id_fields = ["product_name", "product"]

    # Поиск
    """---- Убираем product_number и engine_number, т.к. их обрабатывает миксин через отдельные поля ----"""
    search_fields = [
        "year",  # год
        "yearly_number",  # номер в году
        "product__nomenclature",  # обозначение изделия
        "sender_outgoing_number",  # исходящий № отправителя
        # "product_number",  # номер изделия
        # "engine_number",  # номер двигателя
        "consumer_act_number",  # номер акта приобретателя изделия
        "end_consumer_act_number",  # номер акта конечного потребителя
        "receipt_invoice_number",  # номер накладной прихода изделия
        "investigation__act_number",  # номер акта исследования
    ]

    """---- Параметр search_help_text не используется, т.к. поля поиска добавлены в шаблон reclamation_changelist.html ----"""
    # search_help_text = mark_safe(
    #     """
    # <p>ПОИСК ПО ПОЛЯМ:</p>
    # <ul>
    #     <li>НОМЕР СТРОКИ (ID) ••• ИСХОДЯЩИЙ № ОТПРАВИТЕЛЯ (№ ПСА) ••• НОМЕР ИЗДЕЛИЯ ••• НОМЕР ДВИГАТЕЛЯ</li>
    #     <li>НОМЕР АКТА РЕКЛАМАЦИИ ПРИОБРЕТАТЕЛЯ ИЛИ ПОТРЕБИТЕЛЯ ••• НОМЕР НАКЛАДНОЙ ПРИХОДА ••• НОМЕР АКТА ИССЛЕДОВАНИЯ</li>
    # </ul>
    # """
    # )

    # Добавляем методы действия в панель "Действие/Выполнить"
    actions = ["add_measures", "add_investigation", "add_disposal_act"]

    # Добавляем URL для методов действий
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

    # ========= Определение методов действий ==========

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

        # Получаем выбранную запись
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

    def add_invoice_into_view(self, request):
        """Метод группового добавления накладной прихода рекламационных изделий"""
        # Здесь используется self, а во views.py параметр admin_instance в функции -
        # через него передаем ссылку на ReclamationAdmin для вызова message_user.
        return add_invoice_into_view(self, request)

    # ========= Переопределение стандартных методов Django ==========

    def get_queryset(self, request):
        """Метод get_queryset с select_related используется для оптимизации запросов к базе данных"""
        # Без select_related будет N+1 запросов (1 запрос для списка рекламаций + N запросов для связанных данных)
        # С select_related будет только 1 запрос
        queryset = (
            super()
            .get_queryset(request)
            .select_related("product_name", "product", "defect_period")
        )

        # Добавляем фильтрацию по номеру изделия и двигателя из миксина
        queryset = self._apply_product_engine_filter(request, queryset)

        return queryset

    def get_search_results(self, request, queryset, search_term):
        """Переопределяем стандартный метод для поиска по составному номеру рекламации"""

        # 1. Стандартный поиск Django по search_fields
        queryset, use_distinct = super().get_search_results(
            request, queryset, search_term
        )

        # 2. Добавляем свою дополнительную логику поиска
        if search_term and "-" in search_term:
            # Дополнительный поиск по формату "2025-1356"
            try:
                year, number = search_term.split("-")
                queryset |= self.model.objects.filter(
                    year=int(year), yearly_number=int(number)
                )
            except ValueError:
                pass

        # Возвращаем результат
        return queryset, use_distinct

    def changelist_view(self, request, extra_context=None):
        """Переопределяем стандартный метод для настройки вывода рекламаций
        по текущему году по умолчанию + ДОПОЛНЯЕМ явным вызовом миксина."""

        extra_context = extra_context or {}

        # 1. Извлекаем и удаляем параметры с номером изделия и двигателя из GET
        # Сохраняем значения до того, как Django их увидит
        request._product_number = request.GET.get("product_number", "").strip()
        request._engine_number = request.GET.get("engine_number", "").strip()

        # Убираем из GET, чтобы Django Admin не применял их как точный фильтр
        if "product_number" in request.GET or "engine_number" in request.GET:
            get_params = request.GET.copy()
            get_params.pop("product_number", None)
            get_params.pop("engine_number", None)
            request.GET = get_params

        # 2. Проверяем есть ли фильтр по году от пользователя
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

        # 3. Добавляем контекст полей поиска из миксина
        extra_context = self._add_product_engine_context(request, extra_context)

        # Вызываем родительский changelist_view
        response = super().changelist_view(request, extra_context)

        return response

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

    # ========= Вспомогательные методы для отображения в админ-панели ==========

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

    @admin.display(description="Решение по рекламации")
    def has_investigation_solution(self, obj):
        """Метод для цветного отображения решения по рекламации из акта исследования"""
        if obj.has_investigation:
            # Используем get_solution_display() для получения русского названия
            # Django автоматически создает метод get_ПОЛЕ_display() для полей с choices
            display = obj.investigation.get_solution_display()
            if obj.investigation.solution == "ACCEPT":
                return format_html('<span style="color: green;">✓ {}</span>', display)
            elif obj.investigation.solution == "DEFLECT":
                return format_html('<span style="color: red;">{}</span>', display)
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

    # Автозаполнение для связанных полей
    autocomplete_fields = ["product_name", "product"]

    # Быстрый поиск по ID
    raw_id_fields = ["product_name", "product"]

    # Сортировка по умолчанию
    ordering = ["-id"]

    # Добавляем шаблон формы, где можно будет ввести номера актов и номер накладной
    change_list_template = "admin/reclamation_changelist.html"
