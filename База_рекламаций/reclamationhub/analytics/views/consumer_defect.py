from django.shortcuts import render


def consumer_defect_page(request):
    """Заглушка для модуля 'Анализ дефектности по потребителю'"""
    context = {
        "page_title": "Дефектность по потребителю",
        "module_name": "Consumer Defect",
        "description": "Количественный анализ дефектности по потребителям за отчетный период",
        "status": "В разработке...",
    }
    return render(request, "analytics/consumer_defect.html", context)
