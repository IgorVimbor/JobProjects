from django.urls import path
from .views import (
    analytics,
    enquiry_period,
    accept_defect,
    length_study,
    not_acts,
    date_pretence,
    db_search,
)

app_name = "reports"

urlpatterns = [
    path("", analytics.analytics_page, name="analytics"),
    # Маршрут для приложения "Справка за период"
    path("enquiry-period/", enquiry_period.enquiry_period_page, name="enquiry_period"),
    # Маршрут для приложения "Количество признанных/непризнанных"
    path("accept-defect/", accept_defect.accept_defect_page, name="accept_defect"),
    # Маршрут для приложения "Длительность исследования"
    path("length-study/", length_study.length_study_page, name="length_study"),
    # Маршруты для приложения "Поиск по базе рекламаций"
    path("db-search/", db_search.db_search_page, name="db_search"),
    path(
        "db-search/download/",
        db_search.download_search_report,
        name="download_search_report",
    ),
    # Маршрут для приложения "Незакрытые акты рекламаций"
    path("not-acts/", not_acts.not_acts_page, name="not_acts"),
    # Маршрут для приложения "Даты уведомления по рекламациям"
    path("date-pretence/", date_pretence.date_pretence_page, name="date_pretence"),
]
