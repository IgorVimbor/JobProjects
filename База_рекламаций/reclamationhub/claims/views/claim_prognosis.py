from django.shortcuts import render


def claim_prognosis_view(request):
    """Заглушка для модуля"""
    context = {
        "page_title": "Прогноз по претензиям",
        "module_name": "Claims",
        "description": "Прогноз по выставленным претензиям",
        "status": "В разработке...",
    }
    return render(request, "claims/claim_prognosis.html", context)
