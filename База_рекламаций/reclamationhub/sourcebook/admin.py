from django.contrib import admin
from .models import PeriodDefect, ProductType, Product


# В этой конфигурации админки:
# - Добавлен поиск по всем моделям
# - Для Product добавлена фильтрация по типу продукта
# - Используется select_related для оптимизации запросов
# - Отображается количество активных рекламаций
# - Добавлен raw_id_fields для product_type, что удобно при большом количестве записей


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
    list_display = ["nomenclature", "product_type", "active_reclamations_count"]
    list_filter = ["product_type"]
    search_fields = ["nomenclature", "product_type__name"]
    # raw_id_fields = ["product_type"]  # отображение поля product_type в виде отдельного окна
    # отображение поля product_type в виде выпадающего списка
    search_fields = ["nomenclature", "product_type__name"]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("product_type")
