# claims/urls.py

from django.urls import path
from claims.views.analytics import dashboard_view

app_name = "claims"

urlpatterns = [
    # Маршрут до основной страницы аналитики претензий
    path("", dashboard_view, name="dashboard"),
]
