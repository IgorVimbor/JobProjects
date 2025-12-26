# core\views\about_page.py

"""Представление для страницы 'О проекте'."""

from django.shortcuts import render
from django.urls import reverse, NoReverseMatch

from core.modules.project_info import (
    PROJECT_INFO,
    SITEMAP,
    TECHNOLOGIES,
    WHATS_NEW,
)


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

    context = {
        "project": PROJECT_INFO,
        "sitemap": sitemap_grouped,
        "technologies": TECHNOLOGIES,
        # "features": FEATURES,
        "whats_new": WHATS_NEW,
    }

    return render(request, "core/about.html", context)
