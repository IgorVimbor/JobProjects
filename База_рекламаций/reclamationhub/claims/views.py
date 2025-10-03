from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import render

from .models import Claim
from .forms import ClaimAdminForm


# Пока views.py простой - будем расширять по мере необходимости
# Здесь будут групповые операции если понадобятся


def placeholder_view(admin_instance, request):
    """Заглушка для будущих view методов"""
    pass
