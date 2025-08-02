from django.shortcuts import render
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
