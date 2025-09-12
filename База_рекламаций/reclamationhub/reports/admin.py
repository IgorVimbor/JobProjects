from django.contrib import admin

from reclamationhub.admin import admin_site
from .models import EnquiryPeriod


@admin.register(EnquiryPeriod, site=admin_site)
class EnquiryPeriodAdmin(admin.ModelAdmin):
    list_display = ("sequence_number", "last_processed_id", "report_date")
    list_filter = ("report_date",)
    ordering = ("sequence_number",)

    # Для удобства редактирования
    list_editable = ("last_processed_id", "report_date")
