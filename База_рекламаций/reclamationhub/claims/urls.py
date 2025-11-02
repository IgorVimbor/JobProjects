# claims/urls.py

from django.urls import path
from .views import (
    claim_main,
    dashboard,
    consumer_analysis,
    reclamation_to_claim,
    claim_prognosis,
)

app_name = "claims"

urlpatterns = [
    # Главная страница аналитики претензий
    path("", claim_main.claim_page, name="claim_main"),
    # 4 вида анализа:
    path(  # Dashbord претензий
        "dashboard/", dashboard.dashboard_view, name="dashboard"
    ),
    path(  # Аналитиз претензий по потребителю
        "consumer-analysis/",
        consumer_analysis.consumer_analysis_view,
        name="consumer_analysis",
    ),
    path(  # Анализ связи рекламаций и претензий
        "reclamation-to-claim/",
        reclamation_to_claim.reclamation_to_claim_view,
        name="reclamation_to_claim",
    ),
    path(  # Прогноз по претензиям
        "claim-prognosis/", claim_prognosis.claim_prognosis_view, name="claim_prognosis"
    ),
]
