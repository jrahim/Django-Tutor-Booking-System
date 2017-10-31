import hashlib
from datetime import datetime, timedelta, date

from dateutil import parser
from django.core.validators import validate_email
from django.http import JsonResponse
from django.shortcuts import redirect
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from .forms import ImageForm
from .models import *
import math


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
                            user.wallet = user.create_wallet()
                            user.save()  # save new user in db
                            # make wallet for new user
                            user.become_student();
                            request.session['uid'] = user.id  # add user id to session
                            return redirect('/mainApp/index?first=1')  # take user to landing page
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
                    request.session['uid'] = User.objects.get(email=request.POST.get('email')).id

                    return redirect('/mainApp/index')
                else:
                    return render(request, 'mainApp/index.html', {'form': form, 'loginError': 'Incorrect Combination'})

        return render(request, 'mainApp/index.html', {'form': form})  # render index page if no post request
    else:  # if user already logged in
        if request.method == 'GET':  # handle logout
            if request.GET.get("logout", None) == '1':
                del request.session['uid']
                return render(request, 'mainApp/index.html', {'form': form})
        try:
            user = User.objects.get(id=request.session['uid'])  # get user details
        except:
            del request.session['uid']
            return redirect('/mainApp/index')
        return render(request, 'mainApp/landing.html', {'user': user})  # take user to landing page


@csrf_exempt
def search(request):
    if 'uid' not in request.session:
        return redirect('/mainApp/index')
    user = User.objects.get(id=request.session['uid'])
    tutor_list = Tutor.objects.all()
    context = {
        'tutor_list': tutor_list,
        'user': user
    }
    return render(request, 'mainApp/search.html', context)


@csrf_exempt
def profile(request):
    if 'uid' not in request.session:
        return redirect('/mainApp/index')
    user = User.objects.get(id=request.session['uid'])
    isTutor = '0'
    tutor = {}
    if Tutor.objects.filter(user=request.session['uid']):
        isTutor = '1'
        tutor = Tutor.objects.get(user=request.session['uid'])
    return render(request, 'mainApp/profile.html', {'user': user, 'isTutor': isTutor, 'tutor': tutor})


@csrf_exempt
def bookings(request):
    if 'uid' not in request.session:
        return redirect('/mainApp/index')
    user = User.objects.get(id=request.session['uid'])
    return render(request, 'mainApp/bookings.html', {'user': user})


@csrf_exempt
def wallet(request):
    if 'uid' not in request.session:
        return redirect('/mainApp/index')
    user = User.objects.get(id=request.session['uid'])
    wallet = Wallet.objects.get(user=request.session['uid'])
    context = {
        'wallet': wallet,
        'user': user
    }
    return render(request, 'mainApp/wallet.html', context)


@csrf_exempt
def book(request, pk):
    if 'uid' not in request.session:
        return redirect('/mainApp/index')
    extra = parser.parse("Nov-2")
    tutor = Tutor.objects.get(id=pk)
    user = User.objects.get(id=request.session['uid'])
    if user.wallet.balance < math.ceil(tutor.rate * 1.05):
        return render(request, 'mainApp/lessBalance.html', {'user': user})
    tutorBookings = BookedSlot.objects.filter(tutor=pk)
    tutorUnavailable = UnavailableSlot.objects.filter(tutor=pk)
    today = date.today()
    slots = []
    if tutor.isPrivate:
        slots = ["07:00", "08:00", "09:00", "10:00", "11:00", "12:00", "13:00", "14:00"]
        slotsToRender = ["07:00-08:00", "08:00-09:00", "09:00-10:00", "10:00-11:00", "11:00-12:00", "12:00-13:00",
                         "13:00-14:00", "14:00-15:00"]
    else:
        slots = ["07:00", "07:30", "08:00", "08:30", "09:00", "09:30", "10:00", "10:30", "11:00", "11:30", "12:00",
                 "12:30", "13:00", "13:30", "14:00"]
        slotsToRender = ["07:00-07:30", "07:30-08:00", "08:00-08:30", "08:30-09:00", "09:00-09:30", "09:30-10:00",
                         "10:00-10:30", "10:30-11:00", "11:00-11:30", "11:30-12:00", "12:00-12:30", "12:30-13:00",
                         "13:00-13:30", "13:30-14:00", "14:30-15:00"]
    weekDays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    BookableDates = []
    for i in range(1, 8):
        nextDay = today + timedelta(days=i)
        BookableDates.append(
            {'dt': nextDay, 'weekday': weekDays[nextDay.weekday()], 'day': nextDay.day,
             'month': months[nextDay.month - 1], 'row': "", 'id': ""})
    for d in BookableDates:
        dt = d['dt']
        weekday = d['weekday']
        for slot in slots:
            isUnavailable = False
            for booking in tutorBookings:
                if booking.date == dt and booking.time_start == datetime.strptime(slot, '%H:%M').time():
                    isUnavailable = True
                    d['row'] = d['row'] + "<td class='unavailable' id=''></td>"
            if not isUnavailable:
                for unavailable in tutorUnavailable:
                    if unavailable.day == weekday and unavailable.time_start == datetime.strptime(slot,
                                                                                                  '%H:%M').time():
                        isUnavailable = True
                        d['row'] = d['row'] + "<td class='unavailable' id=''></td>"
            if not isUnavailable:
                day = d['day']
                month = d['month']
                if day < 10:
                    day = "0" + str(day)
                else:
                    day = str(day)
                tdid = month + "-" + day + "_" + slot
                d['row'] = d['row'] + "<td id='" + tdid + "'></td>"

    context = {'dates': BookableDates, 'user': user, 'tutor': tutor, 'today': today, 'slotsToRender': slotsToRender}
    return render(request, 'mainApp/book.html', context)


@csrf_exempt
def confirmation(request, pk):
    if 'uid' not in request.session:
        return redirect('/mainApp/index')
    user = User.objects.get(id=request.session['uid'])
    booking = BookedSlot.objects.get(id=pk)
    charges = math.ceil(booking.tutor.rate * 1.05)
    return render(request, 'mainApp/confirmation.html', {'user': user, 'booking': booking, 'charges': charges})


@csrf_exempt
def manageWallet(request):
    if 'uid' not in request.session:
        return JsonResponse({'status': 'fail'})
    w = Wallet.objects.get(user=request.session['uid']);
    if request.GET.get('action', None) == "add":
        w.add_funds(int(request.GET.get('amount', None)))
    else:
        w.subtract_funds(int(request.GET.get('amount', None)))
    data = {'status': 'success'}
    return JsonResponse(data)


@csrf_exempt
def makeTutor(request):
    if 'uid' not in request.session:
        return JsonResponse({'status': 'fail'})
    user = User.objects.get(id=request.session['uid'])
    if Tutor.objects.filter(user=user).exists():
        return JsonResponse({'status': 'fail'})
    if request.POST.get('isPrivate') == 'yes':
        user.become_tutor(request.POST.get('shortBio'), int(request.POST.get('rate')), True)
    else:
        user.become_tutor(request.POST.get('shortBio'), 0, False)
    return JsonResponse({'status': 'success'})


@csrf_exempt
def confirmBooking(request):
    if 'uid' not in request.session:
        return JsonResponse({'status': 'fail'})
    user = User.objects.get(id=request.session['uid'])
    student = Student.objects.get(user=request.session['uid'])
    if request.method == 'POST':
        tutor = Tutor.objects.get(id=request.POST.get('tutorid'))
        try:
            if tutor.isPrivate:
                booking = student.create_booking(parser.parse(request.POST.get('date')),
                                                 datetime.strptime(request.POST.get('time') + ":00:00",
                                                                   '%H:%M:%S').time(), 1.0,
                                                 tutor, math.ceil(tutor.rate * 1.05))
            else:
                booking = student.create_booking(parser.parse(request.POST.get('date')),
                                                 datetime.strptime(request.POST.get('time') + ":00", '%H:%M').time(),
                                                 0.5,
                                                 tutor, 0)
            return JsonResponse({'status': 'success', 'booking': booking.id})
        except:
            return JsonResponse({'status': 'fail'})
    else:
        return JsonResponse({'status': 'fail'})


@csrf_exempt
def tutorProfile(request, pk):
    tutor = Tutor.objects.get(id=pk)
    user = User.objects.get(id=request.session['uid'])
    return render(request, 'mainApp/tutorProfile.html', {'tutor': tutor, 'user': user})
