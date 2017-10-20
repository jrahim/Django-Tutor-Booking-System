from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.template import loader
from .models import *
from django.core import serializers
from django.http import JsonResponse
from mainApp.forms import ImageForm


# Create your views here.

@csrf_exempt
def index(request):
    form = ImageForm()
    if 'uid' not in request.session:
        if request.method == 'POST':
            if 'signup' in request.POST:
                form = ImageForm(request.POST, request.FILES)
                if form.is_valid():
                    if not User.objects.filter(email=request.POST.get('email')).exists():
                        user = User(name=request.POST.get('name'), avatar=request.FILES['docfile'], email=request.POST.get("email"), password=request.POST.get("password"))
                        user.save()
                        request.session['uid']=user.id
                        return render(request, 'mainApp/landing.html')
                    else:
                        return render(request, 'mainApp/index.html', {'form': form, 'error': 'Email already used'})
            if 'login' in request.POST:
                if User.objects.filter(email=request.POST.get('email'), password=request.POST.get('password')).exists():
                    request.session['uid'] = User.objects.get(email=request.POST.get('email'), password=request.POST.get('password')).id
                    return render(request, 'mainApp/landing.html')

        return render(request, 'mainApp/index.html', {'form': form})
    else:
        if request.method == 'GET':
            if request.GET.get("logout",None)=='1':
                del request.session['uid']
                return render(request, 'mainApp/index.html', {'form': form})
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
def wallet(request, pk):
    wallet = Wallet.objects.get(user=pk)
    context = {
        'wallet': wallet,
    }
    return render(request, 'mainApp/wallet.html', context)


@csrf_exempt
def book(request, pk):
    context = {'data': serializers.serialize("python", PrivateTimetable.objects.filter(tutor=pk))}
    # tt = {'tt': PrivateTimetable.objects.filter(tutor=pk), 'fields':PrivateTimetable._meta.get_fields()}
    return render(request, 'mainApp/book.html', context)


@csrf_exempt
def confirmation(request):
    return render(request, 'mainApp/confirmation.html')


@csrf_exempt
def manageWallet(request, pk):
    w = Wallet.objects.get(user=pk)
    if (request.GET.get('action', None) == "add"):
        w.balance = w.balance + int(request.GET.get('amount', None))
    else:
        w.balance = w.balance - int(request.GET.get('amount', None))
    w.save();
    data = {'status': 'success'}
    return JsonResponse(data)
