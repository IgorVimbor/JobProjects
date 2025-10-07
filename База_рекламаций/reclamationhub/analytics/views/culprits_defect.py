from django.shortcuts import render


def culprits_defect_page(request):
    """Заглушка для модуля 'Анализ по виновникам дефектов'"""
    context = {
        "page_title": "Виновники дефектов",
        "module_name": "Culprits Defect",
        "description": "Количественный анализ по виновникам дефектов за отчетный период",
        "status": "В разработке...",
    }
    return render(request, "analytics/culprits_defect.html", context)
