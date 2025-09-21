from django.contrib import admin

from reclamationhub.admin import admin_site
from reclamations.models import Reclamation
from .models import EnquiryPeriod


# @admin.register(EnquiryPeriod, site=admin_site)
# class EnquiryPeriodAdmin(admin.ModelAdmin):
#     list_display = ("sequence_number", "last_processed_id", "report_date")
#     list_filter = ("report_date",)
#     # ordering = ("-sequence_number",)  # НЕ НУЖНО! Берется из модели, т.к. логика та же

#     # Для удобства редактирования
#     list_editable = ("last_processed_id", "report_date")


@admin.register(EnquiryPeriod, site=admin_site)
class EnquiryPeriodAdmin(admin.ModelAdmin):
    list_display = (
        "sequence_number",
        "last_processed_id",
        "last_processed_yearly_number_display",
        "report_date",
    )
    list_filter = ("report_date",)
    # ordering = ("-sequence_number",)  # НЕ НУЖНО! Берется из модели, т.к. логика та же
    list_editable = ("last_processed_id", "report_date")  # Оставляем для редактирования

    def last_processed_yearly_number_display(self, obj):
        # Показываем yearly_number КАК ДОПОЛНИТЕЛЬНУЮ колонку
        try:
            reclamation = Reclamation.objects.get(id=obj.last_processed_id)
            return f"{reclamation.year}-{reclamation.yearly_number}"
        except:
            return "Не найдено"

    last_processed_yearly_number_display.short_description = "№ записи в текущем году"
