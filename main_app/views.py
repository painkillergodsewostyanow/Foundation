from django.shortcuts import render
from django.shortcuts import reverse, redirect


def index(request):
    if request.user.is_authenticated:
        return redirect(reverse('education_app:dashboard'))
    return render(request, 'main_app/landing.html')
