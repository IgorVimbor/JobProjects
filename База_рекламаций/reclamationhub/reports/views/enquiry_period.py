from django.shortcuts import render


def enquiry_period_page(request):
    """Заглушка для модуля 'Справка за период'"""
    context = {
        "page_title": "Справка за период",
        "module_name": "Enquiry Period",
        "description": "Справка по количеству рекламаций за период",
        "status": "В разработке...",
    }
    return render(request, "reports/enquiry_period.html", context)
