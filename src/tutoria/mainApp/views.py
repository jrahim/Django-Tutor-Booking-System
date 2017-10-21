import hashlib

from django.core import serializers
from django.core.validators import validate_email
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from .forms import ImageForm

from .models import *


# Create your views here.

@csrf_exempt
def index(request):
    form = ImageForm()  # make a form to get
    if 'uid' not in request.session:  # if user not already logged in
        if request.method == 'POST':  # if user submitted something
            if 'signup' in request.POST:  # if user submitted signup request
                form = ImageForm(request.POST, request.FILES)  # get the uploaded image
                if form.is_valid():  # check if imageform is valid
                    try:
                        validate_email(request.POST.get('email'))  # validate email address
                        if not User.objects.filter(email=request.POST.get(
                                'email')).exists():  # if email not already used in another account
                            user = User(name=request.POST.get('name'), avatar=request.FILES['docfile'],
                                        email=request.POST.get("email"), password=hashlib.md5(
                                    request.POST.get("password").encode(
                                        'utf-8')).hexdigest())  # make a new user with md5 hash of pwd
                            # user.make_wallet()
                            user.save()  # save new user in db
                            request.session['uid'] = user.id  # add user id to session
                            return render(request, 'mainApp/landing.html')  # take user to landing page
                        else:
                            return render(request, 'mainApp/index.html',
                                          {'form': form, 'emailError': 'Email Already Used'})  # else give error
                    except:
                        return render(request, 'mainApp/index.html', {'form': form,
                                                                      'emailError': 'Please Enter a Valid Email Address'})  # if email not valid, give error
                else:
                    return render(request, 'mainApp/index.html', {'form': form})  # else take back to same page
            if 'login' in request.POST:  # if login request submitted
                if User.objects.filter(email=request.POST.get('email'), password=hashlib.md5(
                        request.POST.get("password").encode('utf-8')).hexdigest()).exists():
                    request.session['uid'] = User.objects.get(email=request.POST.get('email'), password=hashlib.md5(
                        request.POST.get("password").encode('utf-8')).hexdigest()).id

                    return render(request, 'mainApp/landing.html')

        return render(request, 'mainApp/index.html', {'form': form})  # render index page if no post request
    else:
        if request.method == 'GET':  # handle logout
            if request.GET.get("logout", None) == '1':
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
    context = {'data': serializers.serialize("python", PrivateTimetable.objects.filter(tutor=pk)),
               'tutor': Tutor.objects.filter(id=pk)[0]}
    # tt = {'tt': PrivateTimetable.objects.filter(tutor=pk), 'fields':PrivateTimetable._meta.get_fields()}
    return render(request, 'mainApp/book.html', context)


@csrf_exempt
def confirmation(request):
    return render(request, 'mainApp/confirmation.html')


@csrf_exempt
def manageWallet(request, pk):
    w = Wallet.objects.get(user=pk)
    if request.GET.get('action', None) == "add":
        w.add_funds(int(request.GET.get('amount', None)))
    else:
        w.subtract_funds(int(request.GET.get('amount', None)))
    data = {'status': 'success'}
    return JsonResponse(data)
