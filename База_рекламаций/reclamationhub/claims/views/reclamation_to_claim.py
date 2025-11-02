from django.shortcuts import render


def reclamation_to_claim_view(request):
    """Заглушка для модуля"""
    context = {
        "page_title": "Графики и таблицы по претензиям",
        "module_name": "Claims",
        "description": "Графики и таблицы по выставленным и признанным претензиям",
        "status": "В разработке...",
    }
    return render(request, "claims/reclamation_to_claim.html", context)
