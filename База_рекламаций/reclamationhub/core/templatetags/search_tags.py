# core/templatetags/search_tags.py

"""
Пользовательские теги (Template tags) шаблонов для работы с поиском в админке.

Доступные теги:
- `clear_search_url`: формирует URL для сброса поиска
- `preserve_filters`: генерирует скрытые поля формы для сохранения GET-параметров
"""

# Template tags — это функции Python, которые можно вызывать прямо из HTML-шаблонов.
# Они позволяют вынести сложную логику из шаблона в Python-код.

# Зачем нужны:
#     - Шаблоны Django поддерживают только простую логику (if, for, фильтры)
#     - Сложные операции (формирование URL, генерация HTML) лучше делать в Python
#     - Template tags — стандартный способ расширить возможности шаблонов

# Как использовать:
#     1. В шаблоне загрузить библиотеку. Пример: {% load search_tags %}
#     2. Вызвать тег. Пример: {% clear_search_url request %}

from django import template
from django.utils.http import urlencode
from django.utils.html import format_html_join

register = template.Library()


@register.simple_tag
def clear_search_url(request):
    """
    Генерирует URL для сброса поиска, сохраняя остальные фильтры.

    Использование:
        {% load search_tags %}
        <a href="{% clear_search_url request %}">Сбросить</a>
    """

    exclude = {"q", "product_number", "engine_number", "p"}
    params = {key: value for key, value in request.GET.items() if key not in exclude}
    return "?" + urlencode(params) if params else "?"


@register.simple_tag
def preserve_filters(request, *exclude_params):
    """
    Генерирует скрытые поля (hidden inputs) для сохранения GET-параметров.

    Зачем нужно:
        При отправке формы браузер отправляет ТОЛЬКО поля этой формы.
        Все текущие GET-параметры (фильтры, сортировка) теряются.
        Скрытые поля сохраняют эти параметры при отправке формы.

    Использование:
        {% load search_tags %}
        {% preserve_filters request 'q' 'product_number' 'engine_number' 'p' %}
    """

    exclude = set(exclude_params)

    return format_html_join(
        "\n",
        '<input type="hidden" name="{}" value="{}">',
        [(key, value) for key, value in request.GET.items() if key not in exclude],
    )
