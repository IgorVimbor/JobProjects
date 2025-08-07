from django.urls import path
from core.views import home_view, export_excel


urlpatterns = [
    path("", home_view, name="home"),
    path("export-excel/", export_excel, name="export_excel"),
]

# urlpatterns = [
#     path("", home_view, name="home"),  # это обрабатывает корневой URL '/'
#     path("home/", home_view, name="home"),  # добавим явный путь для /home/
# ]
