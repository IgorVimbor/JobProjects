from django.contrib import admin, messages
from django.contrib.admin import SimpleListFilter
from django.utils.html import format_html
from django.urls import path, reverse
from django.utils.safestring import mark_safe
from datetime import datetime

from reclamationhub.admin import admin_site
from reclamations.models import Reclamation
from .models import Claim
from .forms import ClaimAdminForm


class ClaimYearListFilter(SimpleListFilter):
    """Фильтр по году рекламации для использования в ClaimAdmin"""

    title = "Год претензии"
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


@admin.register(Claim, site=admin_site)
class ClaimAdmin(admin.ModelAdmin):

    class Media:
        css = {"all": ("admin/css/custom_admin.css",)}
        js = ("admin/js/custom_admin.js",)

    form = ClaimAdminForm

    # Отображение полей в списке
    list_display = [
        # Регистрация
        "registration_number",
        "registration_date",
        # Претензия
        "claim_number",
        "claim_date",
        "claim_amount_all",
        "reclamation_act_number",
        "reclamation_act_date",
        "claim_amount_act",
        # Результат рассмотрения
        "investigation_act_number",
        "investigation_act_date",
        "result",
        "comment",
        "costs_act",
        "costs_all",
        # Ответ БЗА
        "response_number",
        "response_date",
    ]

    # Группировка полей в форме
    fieldsets = [
        (
            "Регистрация",
            {
                "fields": [
                    "registration_number",
                    "registration_date",
                ],
            },
        ),
        (
            "Претензия",
            {
                "fields": [
                    "claim_number",
                    "claim_date",
                    "claim_amount_all",
                    "reclamation_act_number",
                    "reclamation_act_date",
                    "claim_amount_act",
                ],
            },
        ),
        (
            "Результат рассмотрения",
            {
                "fields": [
                    "investigation_act_number",
                    "investigation_act_date",
                    "result",
                    "comment",
                    "costs_act",
                    "costs_all",
                ],
            },
        ),
        (
            "Ответ БЗА",
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
        "result",
        "reclamation__defect_period",
    ]

    # Поиск
    search_fields = [
        "claim_number",
        "registration_number",
        "response_number",
        "reclamation__sender_outgoing_number",
        "reclamation__id",
    ]

    search_help_text = mark_safe(
        """
    <p>ПОИСК ПО ПОЛЯМ:</p>
    <ul>
        <li>НОМЕР ПРЕТЕНЗИИ ••• НОМЕР РЕГИСТРАЦИИ ••• НОМЕР ОТВЕТА БЗА</li>
        <li>НОМЕР ПСА РЕКЛАМАЦИИ ••• ID РЕКЛАМАЦИИ</li>
    </ul>
    """
    )

    # Оптимизация запросов
    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related(
                "reclamation",
                "reclamation__product_name",
                "reclamation__product",
            )
        )

    # Сортировка по умолчанию
    ordering = ["-claim_date"]

    # Отображение кнопок сохранения сверху и снизу
    save_on_top = True

    list_per_page = 10

    # ==================== Методы отображения ====================

    # @admin.display(description="Рекламация")
    # def reclamation_display(self, obj):
    #     """Отображение связанной рекламации"""
    #     reclamation = obj.reclamation
    #     url = reverse("admin:reclamations_reclamation_changelist")
    #     filtered_url = f"{url}?id={reclamation.id}"

    #     return mark_safe(
    #         f'<a href="{filtered_url}" title="Перейти к рекламации">'
    #         f"{reclamation.year}-{reclamation.yearly_number:04d}</a><br>"
    #         f'<small>{reclamation.product_name.name if reclamation.product_name else "Не указано"}</small>'
    #     )

    # @admin.display(description="Сумма претензии")
    # def claim_amount_display(self, obj):
    #     """Отображение суммы претензии с форматированием"""
    #     if obj.claim_amount:
    #         return f"{obj.claim_amount:,.2f} ₽"
    #     return "-"

    # @admin.display(description="Признанная сумма")
    # def bza_costs_display(self, obj):
    #     """Отображение признанной суммы с форматированием"""
    #     if obj.bza_costs:
    #         return f"{obj.bza_costs:,.2f} ₽"
    #     return "-"

    # @admin.display(description="Результат")
    # def result_colored(self, obj):
    #     """Цветное отображение результата"""
    #     if obj.result == Claim.Result.ACCEPTED:
    #         return format_html(
    #             '<span style="color: green; font-weight: bold;">✓ {}</span>',
    #             obj.get_result_display(),
    #         )
    #     elif obj.result == Claim.Result.REJECTED:
    #         return format_html(
    #             '<span style="color: red; font-weight: bold;">✗ {}</span>',
    #             obj.get_result_display(),
    #         )
    #     return "-"

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
