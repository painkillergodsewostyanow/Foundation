from django.http import HttpResponse
from django.shortcuts import render
from django.shortcuts import reverse, redirect


def index(request):
    if request.user.is_authenticated:
        return HttpResponse('редирект на дашборд')
    return render(request, 'main_app/landing.html')
