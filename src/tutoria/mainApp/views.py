from django.shortcuts import render


# Create your views here.

def index(request):
    return render(request, 'mainApp\landing.html')


def search(request):
    return render(request, 'mainApp\search.html')
