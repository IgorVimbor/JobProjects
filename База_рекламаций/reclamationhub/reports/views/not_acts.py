from django.shortcuts import render


def not_acts_page(request):
    """Заглушка для модуля 'Незакрытые акты рекламаций'"""
    context = {
        "page_title": "Незакрытые акты рекламаций",
        "module_name": "Not Acts",
        "description": "Перечень рекламационных изделий по которым нет актов исследования",
        "status": "В разработке...",
    }
    return render(request, "reports/not_acts.html", context)
