# reclamations\views\product_utils.py
"""AJAX endpoint для получения списка изделий в зависимости от выбранного типа изделий."""

# Используется в форме добавления/изменения рекламации для каскадного представления (зависимые dropdown'ы):
# т.е. при выборе типа изделия динамически загружаются соответствующие обозначения изделий.
# Например: водяной насос -> 240-1307010, 245-1307010, 260-1307116-02  и др.

from django.http import JsonResponse

from sourcebook.models import Product


def get_products(request):
    """Возвращает список продуктов для выбранного типа"""
    product_type_id = request.GET.get("product_type_id")

    if product_type_id:
        products = (
            Product.objects.filter(product_type_id=product_type_id)
            .values("id", "nomenclature")
            .order_by("nomenclature")
        )

        product_list = list(products)
        return JsonResponse(product_list, safe=False)

    return JsonResponse([])


"""
    AJAX endpoint для получения списка продуктов по типу продукта.

    Используется для каскадного выбора в формах (зависимые dropdown'ы):
    при выборе типа продукта динамически загружаются соответствующие продукты.

    **GET параметры:**
        - product_type_id (int): ID типа продукта

    **Возвращает:**
        JsonResponse со списком продуктов:
        [
            {"id": 1, "nomenclature": "Название продукта 1"},
            {"id": 2, "nomenclature": "Название продукта 2"},
            ...
        ]

        Если product_type_id не передан или продукты не найдены - возвращает пустой список [].

    **Пример использования в JavaScript:**
        ```javascript
        fetch('/admin/get_products/?product_type_id=5')
            .then(response => response.json())
            .then(data => {
                // Обновляем select с продуктами
                updateProductSelect(data);
            });
        ```

    **URL:** /admin/get_products/
    """
