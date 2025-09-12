from django.shortcuts import render


def length_study_page(request):
    """Заглушка для модуля 'Длительность исследования рекламаций'"""
    context = {
        "page_title": "Длительность исследования рекламаций",
        "module_name": "Length Study",
        "description": "Статистика длительности исследования рекламаций для показателей премирования",
        "status": "В разработке...",
    }
    return render(request, "reports/length_study.html", context)
