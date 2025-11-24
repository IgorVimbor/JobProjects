from django.contrib import admin, messages
from django.contrib.admin import SimpleListFilter
from django.db.models import Q
from django.utils.html import format_html
from django.urls import path, reverse
from django.utils.safestring import mark_safe
from datetime import datetime
import re

from reclamationhub.admin import admin_site
from reclamations.models import Reclamation
from sourcebook.models import PeriodDefect
from .models import Claim
from .forms import ClaimAdminForm


class ClaimYearListFilter(SimpleListFilter):
    """Фильтр по году рекламации для использования в ClaimAdmin"""

    title = "Год претензии"
    parameter_name = "reclamations__year"

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
            return queryset.filter(reclamations__year=self.value())
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


class ConsumerListFilter(SimpleListFilter):
    """Фильтр по потребителям. В фильтре будут показываться только "ММЗ", "ЯМЗ" и другие потребители
    без суффиксов "-АСП" или "-эксплуатация". При выборе например "ММЗ" будут показаны все претензии,
    где период выявления дефекта начинается с "ММЗ -".
    """

    title = "Потребитель"  # Название фильтра в админке
    parameter_name = "consumer"  # Параметр в URL

    def lookups(self, request, model_admin):
        # Получаем названия потребителей из поля "consumer_name"
        consumers = (
            Claim.objects.values_list("consumer_name", flat=True)
            .distinct()
            .order_by("consumer_name")
        )
        # Возвращаем отсортированный список вариантов для фильтра
        return [(consumer, consumer) for consumer in consumers if consumer]
        # В Django фильтрах метод lookups должен возвращать список кортежей, где:
        # Первый элемент - значение для фильтрации (то, что попадет в self.value())
        # Второй элемент - текст, который видит пользователь в интерфейсе

    def queryset(self, request, queryset):
        # Фильтруем queryset на основе выбранного значения
        if self.value():
            return queryset.filter(consumer_name=self.value())
        return queryset


# class ConsumerListFilter(SimpleListFilter):
#     """Фильтр по потребителям. В фильтре будут показываться только "ММЗ", "ЯМЗ" и другие потребители
#     без суффиксов "-АСП" или "-эксплуатация". При выборе например "ММЗ" будут показаны все претензии,
#     где период выявления дефекта начинается с "ММЗ -".
#     """

#     title = "Потребитель"  # Название фильтра в админке
#     parameter_name = "consumer"  # Параметр в URL

#     def lookups(self, request, model_admin):
#         # Получаем все уникальные префиксы потребителей из PeriodDefect
#         consumers = set()

#         # Получаем все периоды дефектов
#         all_periods = PeriodDefect.objects.values_list("name", flat=True)

#         for period_name in all_periods:
#             if period_name and " - " in period_name:
#                 # Извлекаем часть до " - " (например, "ММЗ" из "ММЗ - АСП")
#                 consumer = period_name.split(" - ")[0].strip()
#                 consumers.add(consumer)

#         # Возвращаем отсортированный список вариантов для фильтра
#         return [(consumer, consumer) for consumer in sorted(consumers)]
#         # В Django фильтрах метод lookups должен возвращать список кортежей, где:
#         # Первый элемент - значение для фильтрации (то, что попадет в self.value())
#         # Второй элемент - текст, который видит пользователь в интерфейсе

#     def queryset(self, request, queryset):
#         # Фильтруем queryset на основе выбранного значения
#         if self.value():
#             return queryset.filter(
#                 reclamations__defect_period__name__startswith=f"{self.value()} - "
#             )
#         return queryset


@admin.register(Claim, site=admin_site)
class ClaimAdmin(admin.ModelAdmin):

    class Media:
        css = {"all": ("admin/css/custom_admin.css",)}
        js = ("admin/js/custom_admin.js", "admin\js\claim_search.js")

    form = ClaimAdminForm

    # Добавляем шаблон формы
    change_list_template = "admin/claim_changelist.html"

    # Отображение полей в таблице на админ-панели
    list_display = [
        # Регистрация
        "registration_number",
        # "registration_date",
        # Претензия
        "consumer_name",
        "claim_number",
        "claim_date",
        "type_money",
        "claim_amount_all_display",
        # Рекламационный акт
        "reclamation_display",
        "reclamation_act_number",
        "reclamation_act_date",
        "engine_number",
        "claim_amount_act_display",
        # Акт исследования рекламации
        "message_received_date",
        "receipt_invoice_number",
        "has_investigation_icon",
        "investigation_act_date",
        "investigation_act_result",
        "formatted_comment",
        # Решение по претензии
        "result_colored",
        "costs_act_display",
        "costs_all_display",
        # Ответ БЗА
        "response_number",
        "response_date",
    ]

    # Группировка полей в форме
    fieldsets = [
        (
            "1. ПОИСК по рекламационному акту, номеру двигателя или акту исследования",
            {
                "fields": [
                    "reclamation_act_number",
                    "reclamation_act_date",
                    "engine_number",
                    "investigation_act_number",
                    "investigation_act_date",
                ],
            },
        ),
        (
            "Дата уведомления и решение по рекламации",
            {
                "fields": [
                    "message_received_date",
                    "receipt_invoice_number",
                    "investigation_act_result",
                ],
            },
        ),
        (
            "2. РЕГИСТРАЦИЯ претензии",
            {
                "fields": [
                    "registration_number",
                    # "registration_date",
                    "consumer_name",
                    "claim_number",
                    "claim_date",
                    "type_money",
                    "claim_amount_all",
                    "claim_amount_act",
                    "comment",
                ],
            },
        ),
        (
            "3. РЕШЕНИЕ по претензии",
            {
                "fields": [
                    "result_claim",
                    "costs_act",
                    "costs_all",
                ],
            },
        ),
        (
            "4. ОТВЕТ на претензию",
            {
                "fields": [
                    "response_number",
                    "response_date",
                ],
            },
        ),
    ]

    # Фильтры
    list_filter = [
        ClaimYearListFilter,
        "result_claim",
        # "reclamation__defect_period",
        ConsumerListFilter,  # кастомный фильтр по потребителям
    ]

    # Поиск
    search_fields = [
        "registration_number",
        "claim_number",
        "response_number",
        "reclamation_act_number",
        "comment",
    ]

    search_help_text = mark_safe(
        """
    <p>ПОИСК ПО ПОЛЯМ:</p>
    <ul>
        <li>НОМЕР РЕГИСТРАЦИИ ••• НОМЕР ПРЕТЕНЗИИ ••• НОМЕР АКТА РЕКЛАМАЦИИ ••• НОМЕР ОТВЕТА БЗА ••• КОММЕНТАРИИ</li>
    </ul>
    """
    )

    # Оптимизация запросов
    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .prefetch_related(
                "reclamations",  # ManyToManyField требует prefetch_related
                "reclamations__product_name",
                "reclamations__product",
            )
        )

    # # Для оптимизации запросов можно использовать list_select_related
    # list_select_related = ["reclamation"]

    # Метод get_queryset лучше и полнее оптимизирует запросы!
    # -----------------------------------------------------------

    # Сортировка по умолчанию
    ordering = ["-registration_number"]

    # Отображение кнопок сохранения сверху и снизу
    save_on_top = True

    list_per_page = 10

    # ==================== Методы отображения ====================

    # @admin.display(description="Потребитель", ordering="consumer_name")
    # def consumer_display(self, obj):
    #     """Отображение потребителя"""
    #     return obj.consumer_name

    @admin.display(description="Рекламация")
    def reclamation_display(self, obj):
        """Отображение рекламации найденной по данным из претензии"""

        reclamation = None

        # 1. Ищем по номеру и дате акта рекламации
        if obj.reclamation_act_number and obj.reclamation_act_date:
            reclamation = Reclamation.objects.filter(
                Q(
                    sender_outgoing_number=obj.reclamation_act_number,
                    message_sent_date=obj.reclamation_act_date,
                )
                | Q(
                    consumer_act_number=obj.reclamation_act_number,
                    consumer_act_date=obj.reclamation_act_date,
                )
                | Q(
                    end_consumer_act_number=obj.reclamation_act_number,
                    end_consumer_act_date=obj.reclamation_act_date,
                )
            ).first()

        # 2. Если не найдена - ищем по номеру двигателя
        if not reclamation and obj.engine_number:
            reclamation = Reclamation.objects.filter(
                engine_number=obj.engine_number
            ).first()

        # 3. Если не найдена - ищем по номеру акта исследования
        if not reclamation and obj.investigation_act_number:
            try:
                from investigations.models import Investigation

                investigation = Investigation.objects.filter(
                    act_number=obj.investigation_act_number
                ).first()
                if investigation:
                    reclamation = investigation.reclamation
            except Investigation.DoesNotExist:
                pass

        if reclamation:
            url = reverse("admin:reclamations_reclamation_changelist")
            # Добавляем год рекламации в параметры ссылки
            filtered_url = f"{url}?id={reclamation.id}&year={reclamation.year}"

            return mark_safe(
                f'<a href="{filtered_url}" '
                f'target="_blank" '  # открывать в новой вкладке
                f'rel="noopener" '  # для безопасности (предотвращает доступ новой вкладки к родительскому окну)
                f"onmouseover=\"this.style.fontWeight='bold'\" "
                f"onmouseout=\"this.style.fontWeight='normal'\" "
                f'title="Перейти к рекламации">'
                f"{reclamation.year}-{reclamation.yearly_number:04d}</a><br>"
                f"<small>{reclamation.product_name} {reclamation.product}</small>"
            )

        return ""

    @admin.display(description="Акт исследования")
    def has_investigation_icon(self, obj):
        """Метод для отображения номера акта исследования как ссылки.
        Отображает номер акта из претензии, а не из связанной рекламации"""

        # Приоритет - номер акта из самой претензии
        act_number = obj.investigation_act_number

        # Если в претензии нет номера - берем из связанной рекламации
        if not act_number and obj.reclamations.exists():
            first_reclamation = obj.reclamations.first()
            if first_reclamation and first_reclamation.has_investigation:
                act_number = first_reclamation.investigation.act_number

        if act_number:
            url = reverse("admin:investigations_investigation_changelist")
            filtered_url = f"{url}?act_number={act_number}"

            return mark_safe(
                f'<a href="{filtered_url}" '
                f'target="_blank" '  # открывать в новой вкладке
                f'rel="noopener" '  # для безопасности (предотвращает доступ новой вкладки к родительскому окну)
                f"onmouseover=\"this.style.fontWeight='bold'\" "
                f"onmouseout=\"this.style.fontWeight='normal'\" "
                f'title="Перейти к акту исследования">'
                f"{act_number}</a>"
            )

        return "-"

    @admin.display(description="Комментарий")
    def formatted_comment(self, obj):
        if obj.comment:
            # Ищем "Вместе с ISKRA" и выделяем жирным темно-оранжевым цветом
            pattern = r"(Вместе с ISKRA)"
            highlighted_text = re.sub(
                pattern,
                r'<strong style="color: #FF8C00; font-weight: bold;">\1</strong>',
                obj.comment,
                flags=re.IGNORECASE,  # регистронезависимый поиск
            )
            return format_html(highlighted_text)
        return obj.comment or "-"

    # Технически вместо format_html() можно использовать mark_safe(). Но format_html() автоматически экранирует
    # опасные символы в тексте и защищает от XSS-атак, а mark_safe() просто помечает строку как "безопасную"
    # без дополнительной обработки

    @admin.display(description="Решение по претензии")
    def result_colored(self, obj):
        """Цветное отображение результата"""
        if obj.result_claim == Claim.Result.ACCEPTED:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ {}</span>',
                obj.get_result_claim_display(),
            )
        elif obj.result_claim == Claim.Result.REJECTED:
            return format_html(
                '<span style="color: red; font-weight: bold;">{}</span>',
                obj.get_result_claim_display(),
            )
        return "-"

    @admin.display(description="Сумма по претензии")
    def claim_amount_all_display(self, obj):
        """Отображение суммы претензии с форматированием"""
        if obj.claim_amount_all:
            # Простое форматирование: 12450.15 -> "12 450.15"
            amount_str = f"{obj.claim_amount_all:,.2f}"
            return amount_str.replace(",", " ")
        return "-"

    @admin.display(description="Сумма по акту рекламации")
    def claim_amount_act_display(self, obj):
        """Отображение суммы по акту с форматированием"""
        if obj.claim_amount_act:
            amount_str = f"{obj.claim_amount_act:,.2f}"
            return amount_str.replace(",", " ")
        return "-"

    @admin.display(description="Признано по претензии")
    def costs_all_display(self, obj):
        """Отображение признанной суммы претензии с форматированием"""
        if obj.costs_all:
            amount_str = f"{obj.costs_all:,.2f}"
            return amount_str.replace(",", " ")
        return "-"

    @admin.display(description="Признано по акту")
    def costs_act_display(self, obj):
        """Отображение признанной суммы по акту с форматированием"""
        if obj.costs_act:
            amount_str = f"{obj.costs_act:,.2f}"
            return amount_str.replace(",", " ")
        return "-"

    # @admin.display(description="Ответ")
    # def has_response_icon(self, obj):
    #     """Иконка наличия ответа"""
    #     if obj.has_response:
    #         return mark_safe(
    #             '<span style="color: green; font-size: 16px;" title="Ответ получен">✓</span>'
    #         )
    #     return mark_safe(
    #         '<span style="color: gray; font-size: 16px;" title="Ответ не получен">⏳</span>'
    #     )

    # ==================== Переопределение стандартных методов ====================

    def save_model(self, request, obj, form, change):
        """Переопределяем метод для установления связей с рекламациями перед сохранением"""

        # Сначала сохраняем объект (обязательно для ManyToMany!)
        super().save_model(request, obj, form, change)

        # Устанавливаем связи с найденными рекламациями (если есть)
        if hasattr(form, "_found_reclamations") and form._found_reclamations.exists():
            # Очищаем старые связи и устанавливаем новые
            obj.reclamations.set(form._found_reclamations)

            # Информационное сообщение
            count = form._found_reclamations.count()
            if count > 1:
                messages.info(
                    request,
                    f"Претензия связана с {count} рекламациями: "
                    f"{', '.join([str(r) for r in form._found_reclamations])}",
                )

        # Показываем предупреждение если рекламация не найдена
        if hasattr(form, "_warning_message"):
            messages.warning(request, form._warning_message)

    # ==================== Переопределение сообщений ====================

    def response_add(self, request, obj, post_url_continue=None):
        """Кастомное сообщение при добавлении"""
        storage = messages.get_messages(request)
        storage.used = True

        self.message_user(
            request, f"Претензия {obj} была успешно добавлена.", messages.SUCCESS
        )
        return super().response_add(request, obj, post_url_continue)

    def response_change(self, request, obj):
        """Кастомное сообщение при изменении"""
        storage = messages.get_messages(request)
        storage.used = True

        self.message_user(
            request, f"Претензия {obj} была успешно изменена.", messages.SUCCESS
        )
        return super().response_change(request, obj)
