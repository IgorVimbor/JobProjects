from django.contrib import admin
from django.db.models import Count, Q
from django.utils.html import format_html

from .models import PeriodDefect, ProductType, Product


# В этой конфигурации админки:
# - Добавлен поиск по всем моделям
# - Для Product добавлена фильтрация по типу продукта
# - Используется select_related для оптимизации запросов
# - Отображается количество активных рекламаций


@admin.register(PeriodDefect)
class PeriodDefectAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]


@admin.register(ProductType)
class ProductTypeAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    # список отображаемых полей
    list_display = [
        "product_type",
        "nomenclature",
        "total_reclamations_count",
        "active_reclamations_count",
    ]
    # поля в панели фильтрации
    list_filter = ["product_type"]
    # поля в панели поиска
    search_fields = ["nomenclature", "product_type__name"]
    # сортировка полей при отображении в админ-панели
    ordering = ["product_type__name", "nomenclature"]

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("product_type")
            .annotate(
                total_count=Count("reclamations"),
                active_count=Count(
                    "reclamations", filter=~Q(reclamations__status="CLOSED")
                ),
            )
        )

    def total_reclamations_count(self, obj):
        count = obj.total_count
        if count > 0:
            return format_html("<strong>{}</strong>", count)
        return count

    total_reclamations_count.admin_order_field = "-total_count"
    total_reclamations_count.short_description = "Всего рекламаций"

    def active_reclamations_count(self, obj):
        count = obj.active_count
        if count > 0:
            return format_html('<strong style="color: #ba2121;">{}</strong>', count)
        return count

    active_reclamations_count.admin_order_field = "-active_count"
    active_reclamations_count.short_description = "Активные рекламации"

    # select_related - это метод оптимизации запросов к БД.
    # Он выполняет JOIN и получает связанные данные в одном SQL-запросе вместо нескольких отдельных запросов

    # .annotate - это метод, который позволяет добавлять вычисляемые поля, как атрибуты к объектам QuerySet.
    # В данном случае мы добавляем поле total_count и active_count, которые показывают количество всех рекламаций
    # и открытых. Когда пользователь кликнет на заголовок столбца "Всего рекламаций" Django будет сортировать
    # по полю 'total_count' или 'active_count', которые мы создали в аннотации
