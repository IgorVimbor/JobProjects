# core\views\about_page.py

"""Представление для страницы 'О проекте'."""

from django.shortcuts import render
from django.urls import reverse, NoReverseMatch

from core.modules.project_info import (
    CHANGELOG,
    PROJECT_INFO,
    SITEMAP,
    TECHNOLOGIES,
    WHATS_NEW,
)


# Типы изменений с метаданными
CHANGE_TYPES = {
    "added": {"label": "Добавлено", "color": "success", "order": 1},
    "changed": {"label": "Изменено", "color": "success", "order": 2},  # "info"
    "fixed": {"label": "Исправлено", "color": "danger", "order": 3},  # "warning"
    "removed": {"label": "Удалено", "color": "danger", "order": 4},
}


def about(request):
    """
    Страница 'О проекте'.

    Отображает информацию о системе, карту сайта,
    используемые технологии и историю версий.
    """

    def resolve_url(url_name):
        """Безопасное разрешение URL по имени."""
        try:
            return reverse(url_name)
        except NoReverseMatch:
            return None

    # Добавляем resolved URLs к карте сайта
    sitemap_with_urls = []
    for item in SITEMAP:
        item_copy = item.copy()
        item_copy["url"] = resolve_url(item["url_name"])

        # Обрабатываем дочерние элементы
        if "children" in item:
            children_with_urls = []
            for child in item["children"]:
                child_copy = child.copy()
                child_copy["url"] = resolve_url(child["url_name"])
                children_with_urls.append(child_copy)
            item_copy["children"] = children_with_urls

        sitemap_with_urls.append(item_copy)

    # Группируем секции для кастомной раскладки
    sitemap_grouped = {
        "row1": sitemap_with_urls[0:4],  # Главная, Рекламации, Акты, Претензии
        "row2": sitemap_with_urls[4:7],  # Справки, Аналитика рекламаций + претензий
        "row3": sitemap_with_urls[7:],  # Экспорт, Администрирование
    }

    # Обрабатываем changelog: группируем изменения по типам
    changelog_enriched = []
    for release in CHANGELOG:
        release_copy = release.copy()

        # Группируем changes по типу
        changes_grouped = {}
        for change in release["changes"]:
            change_type = change["type"]
            if change_type not in changes_grouped:
                type_info = CHANGE_TYPES.get(
                    change_type,
                    {
                        "label": change_type,
                        "color": "secondary",
                        "order": 99,
                    },
                )
                changes_grouped[change_type] = {
                    "label": type_info["label"],
                    "color": type_info["color"],
                    "order": type_info["order"],
                    "items": [],
                }
            changes_grouped[change_type]["items"].append(change["text"])

        # Сортируем по order и преобразуем в список
        release_copy["changes_grouped"] = sorted(
            changes_grouped.values(), key=lambda x: x["order"]
        )

        changelog_enriched.append(release_copy)

    context = {
        "project": PROJECT_INFO,
        "sitemap": sitemap_grouped,
        "technologies": TECHNOLOGIES,
        # "features": FEATURES,
        "whats_new": WHATS_NEW,
        "changelog": changelog_enriched,
    }

    return render(request, "core/about.html", context)
