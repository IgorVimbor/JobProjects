from django.shortcuts import render


def accept_defect_page(request):
    """Заглушка для модуля 'Признанные/непризнанные рекламации'"""
    context = {
        "page_title": "Признанные/непризнанные рекламации",
        "module_name": "Accept Defect",
        "description": "Справка по количеству признанных/непризнанных рекламаций",
        "status": "В разработке...",
    }
    return render(request, "reports/accept_defect.html", context)
