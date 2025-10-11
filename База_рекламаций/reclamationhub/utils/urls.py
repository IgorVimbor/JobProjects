from django.urls import path
from . import views

app_name = "utils"

urlpatterns = [
    path("export/", views.excel_exporter_page, name="excel_exporter"),
    path("export/quick/", views.quick_export_reclamations, name="quick_export"),
    path("export/preview/", views.get_fields_preview, name="fields_preview"),
    # path("export/template/", views.export_template_download, name="export_template"),
]
