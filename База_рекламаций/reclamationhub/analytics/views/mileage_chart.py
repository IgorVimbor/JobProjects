from django.shortcuts import render


def mileage_chart_page(request):
    """Заглушка для модуля 'Диаграмма по пробегу (наработке)'"""
    context = {
        "page_title": "Диаграмма по пробегу",
        "module_name": "Mileage Chart",
        "description": "Диаграмма по пробегу (наработке) в эксплуатации по виду изделия и потребителю",
        "status": "В разработке...",
    }
    return render(request, "analytics/mileage_chart.html", context)
