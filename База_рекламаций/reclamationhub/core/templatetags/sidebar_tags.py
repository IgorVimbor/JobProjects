from django import template

register = template.Library()


@register.inclusion_tag("sidebar_sections.html")
def show_sections(current_section=None):
    """Показывает разделы навигации"""
    sections = [
        {
            "name": "Рекламации",
            "url_name": "admin:reclamations_reclamation_changelist",
            "slug": "reclamations",
            "available": True,
        },
        {
            "name": "Акты исследования",
            "url_name": "admin:investigations_investigation_changelist",
            "slug": "investigations",
            "available": True,
        },
        {"name": "Претензии", "url_name": "#", "slug": "claims", "available": False},
        {"name": "Аналитика", "url_name": "#", "slug": "analytics", "available": False},
    ]

    return {"sections": sections, "current_section": current_section}
