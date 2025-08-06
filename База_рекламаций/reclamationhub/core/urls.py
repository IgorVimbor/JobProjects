from django.urls import path
from core.views import home_view


urlpatterns = [
    path("", home_view, name="home"),
]

# urlpatterns = [
#     path("", home_view, name="home"),  # это обрабатывает корневой URL '/'
#     path("home/", home_view, name="home"),  # добавим явный путь для /home/
# ]
