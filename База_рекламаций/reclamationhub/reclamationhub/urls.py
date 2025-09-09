"""
URL configuration for reclamationhub project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.views.static import serve
from django.conf.urls.static import static
from django.views.generic import RedirectView

from reclamationhub.admin import admin_site
from reclamations.views import get_products


urlpatterns = [
    path("", include("core.urls")),  # главная страница
    # path("", RedirectView.as_view(url="admin/", permanent=True)),
    path("admin/get_products/", get_products, name="get_products"),
    # Перенаправления для каждого приложения
    path(
        "admin/reclamations/",
        RedirectView.as_view(url="/admin/reclamations/reclamation/", permanent=True),
    ),
    path(
        "admin/investigations/",
        RedirectView.as_view(
            url="/admin/investigations/investigation/", permanent=True
        ),
    ),
    path(
        "admin/claims/",
        RedirectView.as_view(url="/admin/claims/claim/", permanent=True),
    ),
    path(
        "admin/sourcebook/",
        RedirectView.as_view(url="/admin/sourcebook/product/", permanent=True),
    ),
    path("admin/", admin_site.urls),
]

# ------------------- Вариант 1 - Djando для медиа и статики -------------------------
# # ПРИНУДИТЕЛЬНО добавляем обслуживание статических файлов
# urlpatterns += [
#     re_path(r"^static/(?P<path>.*)$", serve, {"document_root": settings.STATIC_ROOT}),
#     re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
# ]

# if settings.DEBUG:
#     import debug_toolbar

#     urlpatterns += [path("__debug__/", include(debug_toolbar.urls))]

# ------------------- Вариант 2 - Django + WhiteNoise --------------------------------
# # Django для медиа (статику обслуживает WhiteNoise)
# urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
# # Для этого варианта в production.py включить настройки WhiteNoise (MIDDLEWARE и STATICFILES_STORAGE)

# if settings.DEBUG:
#     urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
#     import debug_toolbar

#     urlpatterns += [path("__debug__/", include(debug_toolbar.urls))]

# ------------------- Вариант 3 - Django + Nginx --------------------------------------
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    import debug_toolbar

    urlpatterns += [path("__debug__/", include(debug_toolbar.urls))]

# Изменяем заголовок админ-панели
admin_site.site_header = "Панель редактирования"

# Изменяем второй заголовок (над виджетами)
admin_site.index_title = "База рекламаций ОТК"
