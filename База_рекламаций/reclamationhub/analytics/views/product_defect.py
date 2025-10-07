from django.shortcuts import render


def product_defect_page(request):
    """Заглушка для модуля 'Анализ дефектности по изделию'"""
    context = {
        "page_title": "Анализ дефектности по изделию",
        "module_name": "Product Defect",
        "description": "Информация о дефектах конкретного изделия с указанием причин",
        "status": "В разработке...",
    }
    return render(request, "analytics/product_defect.html", context)
