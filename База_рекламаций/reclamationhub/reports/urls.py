from django.urls import path
from . import views


app_name = "reports"

urlpatterns = [
    path("analytics/", views.analytics_page, name="analytics"),
]
