from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.template import loader
from .models import *

# Create your views here.

@csrf_exempt
def index(request):
    return render(request, 'mainApp/landing.html')

@csrf_exempt
def search(request):

    tutor_list = Tutor.objects.all()
    context = {
        'tutor_list': tutor_list,
    }

    return render(request, 'mainApp/search.html', context)

@csrf_exempt
def profile(request):
    return render(request, 'mainApp/profile.html')

@csrf_exempt
def bookings(request):
    return render(request, 'mainApp/bookings.html')

@csrf_exempt
def wallet(request):
    return render(request, 'mainApp/wallet.html')

@csrf_exempt
def book(request):
    return render(request, 'mainApp/book.html')

@csrf_exempt
def confirmation(request):
    return render(request, 'mainApp/confirmation.html')