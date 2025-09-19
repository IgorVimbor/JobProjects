from django.urls import path
from core.views import home_view, ajax_year_data, export_excel


urlpatterns = [
    path("", home_view, name="home"),
    path("ajax/year-data/", ajax_year_data, name="ajax_year_data"),
    path("export-excel/", export_excel, name="export_excel"),
]

# urlpatterns = [
#     path("", home_view, name="home"),  # это обрабатывает корневой URL '/'
#     path("home/", home_view, name="home"),  # добавим явный путь для /home/
# ]
