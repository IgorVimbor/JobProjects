from django.shortcuts import render
from django.db.models import Count, Q
from django.db.models.functions import TruncMonth
from datetime import datetime, timedelta
import json

from reclamations.models import Reclamation
from investigations.models import Investigation
from utils.excel.exporters import ReclamationExcelExporter


# def home_view(request):
#     return render(request, "home.html", {})


def home_view(request):
    # Последние 5 рекламаций
    latest_reclamations = Reclamation.objects.select_related(
        "product", "product_name"
    ).order_by("-id")[:5]

    # Общее количество рекламаций
    total_reclamations = Reclamation.objects.count()

    # Статистика по статусам
    status_data = (
        Reclamation.objects.values("status")
        .annotate(count=Count("id"))
        .order_by("-count")
    )

    # Статистика по изделиям
    products_data = (
        Reclamation.objects.values("product_name__name")
        .annotate(count=Count("id"))
        .order_by("-count")
    )

    # Временно отключена статистика по месяцам
    # # Статистика по месяцам (за последние 6 месяцев)
    # six_months_ago = datetime.now() - timedelta(days=180)
    # monthly_data = (
    #     Reclamation.objects.filter(message_received_date__gte=six_months_ago)
    #     .annotate(month=TruncMonth("message_received_date"))
    #     .values("month")
    #     .annotate(count=Count("id"))
    #     .order_by("month")
    # )

    # Статистика по виновникам дефектов
    fault_data = (
        Investigation.objects.values("fault_type")
        .annotate(count=Count("id"))
        .order_by("-count")
    )

    context = {
        "latest_reclamations": latest_reclamations,
        "total_reclamations": total_reclamations,
        "status_data": json.dumps(list(status_data)),
        "products_data": json.dumps(list(products_data)),
        "fault_data": json.dumps(list(fault_data)),
        "new_reclamations": Reclamation.objects.filter(
            status=Reclamation.Status.NEW
        ).count(),
        "in_progress": Reclamation.objects.filter(
            status=Reclamation.Status.IN_PROGRESS
        ).count(),
        "closed_reclamations": Reclamation.objects.filter(
            status=Reclamation.Status.CLOSED
        ).count(),
    }

    return render(request, "home.html", context)


def export_excel(request):
    """Метод для экспорта в Excel"""
    exporter = ReclamationExcelExporter()
    return exporter.export_to_excel()
