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
from django.urls import path, include
from django.conf import settings
from django.views.generic import RedirectView

from reclamations.views import get_products


urlpatterns = [
    path("", RedirectView.as_view(url="admin/", permanent=True)),
    path("admin/get_products/", get_products, name="get_products"),
    path("admin/", admin.site.urls),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns += [
        path("__debug__/", include(debug_toolbar.urls)),
    ]

# Изменяем заголовок админ-панели
admin.site.site_header = "Панель администрирования"

# Изменяем второй заголовок (над виджетами)
admin.site.index_title = "База рекламаций ОТК"
