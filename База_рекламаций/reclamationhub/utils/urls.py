from django.urls import path
from .views import excel_exporter

app_name = "utils"

urlpatterns = [
    path("export/", excel_exporter.excel_exporter_page, name="excel_exporter"),
    path(
        "export/quick/", excel_exporter.quick_export_reclamations, name="quick_export"
    ),
    path("export/preview/", excel_exporter.get_fields_preview, name="fields_preview"),
    # path("export/template/", excel_exporter.export_template_download, name="export_template"),
]
