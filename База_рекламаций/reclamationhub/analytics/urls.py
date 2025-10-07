from django.urls import path
from .views import (
    analytic,
    combined_chart,
    culprits_defect,
    mileage_chart,
    product_defect,
)


app_name = "analytics"

urlpatterns = [
    # Маршрут до основной страницы аналитики
    path("", analytic.analytic_page, name="analytic"),
    # Маршрут для приложения 'Совмещенная диаграмма'
    path("combined_chart/", combined_chart.combined_chart_page, name="combined_chart"),
    # Маршрут для приложения 'Анализ по виновникам дефектов'
    path(
        "culprits_defect/", culprits_defect.culprits_defect_page, name="culprits_defect"
    ),
    # Маршрут для приложения 'Диаграмма по пробегу (наработке)'
    path("mileage_chart/", mileage_chart.mileage_chart_page, name="mileage_chart"),
    # Маршруты для приложения 'Анализ дефектности по изделию'
    path("product_defect/", product_defect.product_defect_page, name="product_defect"),
]
