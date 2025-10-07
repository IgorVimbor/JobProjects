from django.shortcuts import render


def combined_chart_page(request):
    """Заглушка для модуля 'Совмещенная диаграмма'"""
    context = {
        "page_title": "Совмещенная диаграмма",
        "module_name": "Combined Chart",
        "description": "Диаграмма по пробегу (наработке) в эксплуатации по виду изделия и потребителю",
        "status": "В разработке...",
    }
    return render(request, "analytics/combined_chart.html", context)
