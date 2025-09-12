from django.shortcuts import render


def db_search_page(request):
    """Заглушка для модуля 'Поиск по базе рекламаций'"""
    context = {
        "page_title": "Поиск по базе рекламаций",
        "module_name": "Database search",
        "description": "Краткая информация из базы рекламаций",
        "status": "В разработке...",
    }
    return render(request, "reports/db_search.html", context)
