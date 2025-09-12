from django.shortcuts import render


def date_pretence_page(request):
    """Заглушка для модуля 'Дата уведомления по номеру акта рекламации'"""
    context = {
        "page_title": "Дата уведомления о рекламации",
        "module_name": "Date Pretence",
        "description": "Справка по дате уведомления о рекламации (выходе из строя изделия)",
        "status": "В разработке...",
    }
    return render(request, "reports/date_pretence.html", context)
