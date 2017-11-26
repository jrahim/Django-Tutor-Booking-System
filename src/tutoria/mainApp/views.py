from datetime import datetime, timedelta, date

from dateutil import parser
from django.core.validators import validate_email
from django.db.models import Max
from django.http import JsonResponse
from django.shortcuts import redirect
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from .forms import ImageForm
from .models import *
from django.contrib.auth.hashers import make_password, check_password
from .functions import *


# views
@csrf_exempt
def index(request):
    form = ImageForm()  # make a form to get
    if not isAuthenticated(request):  # if user not already logged in
        if request.method == 'POST':  # if user submitted something
            if 'signup' in request.POST:  # if user submitted signup request
                form = ImageForm(request.POST, request.FILES)  # get the uploaded image
                if form.is_valid():  # check if imageform is valid
                    try:
                        validate_email(request.POST.get('email'))  # validate email address
                    except:
                        return render(request, 'mainApp/index.html', {'form': form,
                                                                      'emailError': 'Please Enter a Valid Email Address'})  # if email not valid, give error
                    if not User.objects.filter(email=request.POST.get(
                            'email')).exists():  # if email not already used in another account
                        user = User(name=request.POST.get('name'), avatar=request.FILES['docfile'],
                                    email=request.POST.get("email"), password=make_password(
                                request.POST.get("password")), contact=request.POST.get("contact"),
                                    last_name=request.POST.get("lastName"))  # make a new user with md5 hash of pwd
                        # user.make_wallet()
                        user.wallet = user.create_wallet()
                        user.save()  # save new user in db
                        # make wallet for new user
                        user.become_student()
                        request.session['uid'] = user.id  # add user id to session
                        isTutor, isStudent = checkUserFromDB(user.id)
                        if isTutor:
                            request.session['tid'] = getTutor(user.id).id
                        if isStudent:
                            request.session['sid'] = getStudent(user.id).id
                        return redirect('/mainApp/index?first=1')  # take user to landing page
                    else:
                        return render(request, 'mainApp/index.html',
                                      {'form': form, 'emailError': 'Email Already Used'})  # else give error
                else:
                    return render(request, 'mainApp/index.html', {'form': form})  # else take back to same page
            if 'login' in request.POST:  # if login request submitted
                if User.objects.filter(email=request.POST.get('email')).exists():
                    user = User.objects.get(email=request.POST.get('email'))
                    if check_password(request.POST.get("password"), user.password):
                        request.session['uid'] = User.objects.get(email=request.POST.get('email')).id
                        isTutor, isStudent = checkUserFromDB(request.session['uid'])
                        if isTutor:
                            request.session['tid'] = getTutor(request.session['uid']).id
                        if isStudent:
                            request.session['sid'] = getStudent(request.session['uid']).id
                        return redirect('/mainApp/index')
                    else:
                        return render(request, 'mainApp/index.html',
                                      {'form': form, 'loginError': 'Incorrect Combination'})
                else:
                    return render(request, 'mainApp/index.html', {'form': form, 'loginError': 'Incorrect Combination'})

        return render(request, 'mainApp/index.html', {'form': form})  # render index page if no post request
    else:  # if user already logged in
        if request.method == 'GET':  # handle logout
            if request.GET.get("logout", None) == '1':
                keys = list(request.session.keys())
                for key in keys:
                    del request.session[key]
                return render(request, 'mainApp/index.html', {'form': form})
        try:
            user = User.objects.get(id=request.session['uid'])  # get user details
        except:
            del request.session['uid']
            return redirect('/mainApp/index')
        return render(request, 'mainApp/landing.html', {'user': user})  # take user to landing page


@csrf_exempt
def search(request):
    if not isAuthenticated(request):
        return redirect('/mainApp/index')
    user = User.objects.get(id=request.session['uid'])
    tags = Tag.objects.all()

    # search
    universities = University.objects.all()
    given_name = request.POST.get('givenName', "")
    last_name = request.POST.get('lastName', "")
    tutor_type = request.POST.get('tutorType', "")
    university = request.POST.get('universityName', "")
    availability = request.POST.get('available', "")

    if university == "0":
        university = ""
    course = request.POST.get('course', "")
    if course == "0":
        course = ""
    tag = request.POST.get('tagName', "")
    
    
    max_rate = request.POST.get('maxRate', "")
    min_rate = request.POST.get('minRate', "")

    # sort
    sort = request.POST.get('sort', "")

    if tutor_type == "tutorPrivate":
        tutor_type = PrivateTutor
    elif tutor_type == "tutorContracted":
        tutor_type = ContractedTutor

    tutor_list = Tutor.objects.all()
    tag_list=Tag.objects.all()
  
    if given_name != "":
        user_list = User.objects.filter(name__istartswith=given_name)  # case insensitive matching - exact matching
        tutor_list = tutor_list.filter(user__in=user_list)

    if last_name != "":
        user_list = User.objects.filter(last_name__iexact=last_name)  # case insensitive matching - exact matching
        tutor_list = tutor_list.filter(user__in=user_list)

    if tutor_type != "":
        tutor_list = tutor_list.filter(Q(instance_of=tutor_type))

    if university != "":
        # university_list = University.objects.filter(
        #     id=university)  # contains to allow custom input search
        # tutor_list = tutor_list.filter(university__in=university_list)
        courses = Course.objects.filter(university=university)
        tutor_list = tutor_list.filter(course__in=courses).distinct()

    if course != "":
        course_list = Course.objects.filter(id=course)  # course code
        tutor_list = tutor_list.filter(course__in=course_list)

    if tag != "":
        tag_list = Tag.objects.filter(tag_name__iexact=tag)
       
        tutor_list = tutor_list.filter(subject_tags__in=tag_list)

    if max_rate != "" and min_rate != "":
        if min_rate == "0":
            max_rate = round(float(max_rate) / 1.05, 2)
            tutor_list = tutor_list.filter(
                Q(PrivateTutor___rate__lte=max_rate) & Q(PrivateTutor___rate__gte=min_rate) | Q(
                    instance_of=ContractedTutor))
        else:
            min_rate = round(float(min_rate) / 1.05, 2)
            max_rate = round(float(max_rate) / 1.05, 2)
            tutor_list = tutor_list.filter(
                Q(PrivateTutor___rate__lte=max_rate) & Q(PrivateTutor___rate__gte=min_rate))
    elif max_rate == "" and min_rate != "":
        max_query = Tutor.objects.all().aggregate(maxvalue=Max('PrivateTutor___rate'))
        if min_rate == "0":
            tutor_list = tutor_list.filter(
                Q(PrivateTutor___rate__lte=max_query['maxvalue']) & Q(PrivateTutor___rate__gte=min_rate) | Q(
                    instance_of=ContractedTutor))
        else:
            min_rate = round(float(min_rate) / 1.05, 2)
            tutor_list = tutor_list.filter(
                Q(PrivateTutor___rate__lte=max_query['maxvalue']) & Q(PrivateTutor___rate__gte=min_rate))
    elif max_rate != "" and min_rate == "":
        max_rate = round(float(max_rate) / 1.05, 2)
        tutor_list = tutor_list.filter(
            Q(PrivateTutor___rate__lte=max_rate) & Q(PrivateTutor___rate__gte=0) | Q(
                instance_of=ContractedTutor))

    # TODO only display tutors with an available slot in the coming 7 days
    if availability != "":
        privateslots, _ = getPrivateSlots()
        contractedslots, _ = getContractedSlots()
        today = date.today()
        tomorrow = today + timedelta(days=1)
        last_date = today + timedelta(days=8)
        time_now = datetime.now().time()
        for tutor in tutor_list:
            upcoming_bookings = BookedSlot.objects.filter(tutor=tutor, status='BOOKED')
            unavailable_slots = UnavailableSlot.objects.filter(Q(tutor=tutor) &
                                                               (Q(date=tomorrow, time_start__gte=time_now) |
                                                               Q(date__range=(tomorrow + timedelta(days=1),
                                                                              last_date - timedelta(days=1))) |
                                                               Q(date=last_date, time_start__lt=time_now)))
            full_slots = upcoming_bookings.count() + unavailable_slots.count()
            weekdays = getWeekdays()
            for booking in upcoming_bookings:
                if unavailable_slots.filter(date=booking.date,
                                            time_start=booking.time_start).exists():
                    full_slots = full_slots - 1
            # print('checking')
            # print(full_slots)
            if isinstance(tutor, PrivateTutor):
                if full_slots >= 7 * len(privateslots):
                    tutor_list = tutor_list.exclude(id=tutor.id)
            elif isinstance(tutor, ContractedTutor):
                if full_slots >= 7 * len(contractedslots):
                    tutor_list = tutor_list.exclude(id=tutor.id)

    tutor_list = tutor_list.filter(isActivated=True)

    if sort != "" and sort == "rateAsc":
        tutor_list = tutor_list.order_by('PrivateTutor___rate')
    elif sort != "" and sort == "rateDesc":
        tutor_list = tutor_list.order_by('-PrivateTutor___rate')
    else:
        tutor_list = tutor_list.order_by('PrivateTutor___rate')
    print(availability)
    params = {'given_name': given_name, 'last_name': last_name, 'university': university,
              'tutor_type': request.POST.get('tutorType', ""), 'course': course, 'tag': tag, 'sort': sort,
              'max_rate': request.POST.get('maxRate', ""), 'min_rate': request.POST.get('minRate', ""),
              'available': availability}

    context = {
        'tutor_list': tutor_list,
        'tag_list': tag_list,
        'user': user,
        'university_list': universities,
        'params': params
    }
    return render(request, 'mainApp/search.html', context)


@csrf_exempt
def get_uni_courses(request):
    university_id = request.POST.get('university')
    course_list = Course.objects.filter(university=university_id)
    result = {}
    for course in course_list:
        result[course.id] = course.title
    print(result)
    return JsonResponse(result)


@csrf_exempt
def profile(request):
    if not isAuthenticated(request):
        return redirect('/mainApp/index')
    user = User.objects.get(id=request.session['uid'])
    isTutor, isStudent = checkUser(user.id, request)
    tutor = {}
    if isTutor:
        isTutor = '1'
        tutor = Tutor.objects.get(user=request.session['uid'])
    else:
        isTutor = '0'
    return render(request, 'mainApp/profile.html', {'user': user, 'isTutor': isTutor, 'tutor': tutor})


@csrf_exempt
def review(request, pk):
    if not isAuthenticated(request):
        return redirect('/mainApp/index')
    user = User.objects.get(id=request.session['uid'])
    booking = BookedSlot.objects.filter(id=pk, status='ENDED')
    if not booking.exists():
        return render(request, 'mainApp/error.html', {'user': user, 'error': 'This link is invalid!'})
    else:
        booking = booking[0]
    student = Student.objects.get(id=booking.student.id)
    if not student.user == user:
        return render(request, 'mainApp/error.html', {'user': user, 'error': 'You can only review your bookings!'})
    review = Review.objects.filter(booking=booking)
    if review.exists():
        return render(request, 'mainApp/error.html',
                      {'user': user, 'error': 'You have already submitted a review for this session!'})

    return render(request, 'mainApp/review.html', {'user': user, 'bookingID': pk})


@csrf_exempt
def bookings(request):
    if not isAuthenticated(request):
        return redirect('/mainApp/index')
    user = User.objects.get(id=request.session['uid'])
    isTutor, isStudent = checkUser(user.id, request)
    pb = user.get_past_bookings(isTutor, isStudent)
    if isTutor == 1 and isStudent == 1:
        tutor_bookings, student_bookings = user.get_upcoming_bookings(isTutor, isStudent)
        context = {
            'user': user,
            'tutor_bookings': tutor_bookings,
            'student_bookings': student_bookings,
            'isStudent': isStudent,
            'isTutor': isTutor,
            'past_bookings': pb
        }
    else:
        bookings = user.get_upcoming_bookings(isTutor, isStudent)
        if isStudent:
            context = {
                'user': user,
                'student_bookings': bookings,
                'isStudent': isStudent,
                'isTutor': isTutor,
                'past_bookings': pb
            }
        else:
            context = {
                'user': user,
                'tutor_bookings': bookings,
                'isStudent': isStudent,
                'isTutor': isTutor,
                'past_bookings': pb
            }

    return render(request, 'mainApp/bookings.html', context)


@csrf_exempt
def wallet(request):
    if not isAuthenticated(request):
        return redirect('/mainApp/index')
    user = User.objects.get(id=request.session['uid'])
    wallet = Wallet.objects.get(user=request.session['uid'])
    isTutor, isStudent = checkUser('uid', request)
    context = {
        'wallet': wallet,
        'user': user,
        'isTutor': isTutor,
        'isStudent': isStudent
    }
    return render(request, 'mainApp/wallet.html', context)


@csrf_exempt
def book(request, pk):
    if not isAuthenticated(request):
        return redirect('/mainApp/index')
    tutor = Tutor.objects.get(id=pk)
    isPrivate = checkIfTutorPrivate(tutor)
    user = User.objects.get(id=request.session['uid'])
    if tutor.user == user:
        return render(request, 'mainApp/error.html', {'user': user, 'error': "You can not book yourself!"})
    if isPrivate:
        if user.wallet.balance < rateWithCommision(tutor.rate):
            return render(request, 'mainApp/error.html', {'user': user,
                                                          'error': "You do not have enough balance in your wallet.<br>You can go to your <a href='/mainApp/wallet'>Wallet page here</a>"})

    tutorBookings = BookedSlot.objects.filter(tutor=pk, status='BOOKED')
    tutorUnavailable = UnavailableSlot.objects.filter(tutor=pk)
    today = date.today()
    slots = []
    if isPrivate:
        slots, slotsToRender = getPrivateSlots()
    else:
        slots, slotsToRender = getContractedSlots()
    weekDays = getWeekdays()
    months = getMonths()
    BookableDates = []
    for i in range(1, 9):
        nextDay = today + timedelta(days=i)
        BookableDates.append(
            {'dt': nextDay, 'weekday': weekDays[nextDay.weekday()], 'day': nextDay.day,
             'month': months[nextDay.month - 1], 'row': "", 'id': ""})
    for d in BookableDates:
        dt = d['dt']
        weekday = d['weekday']
        for slot in slots:
            isUnavailable = False
            today = date.today()
            if abs(dt - today).days == 1:
                if (datetime.now().time() >= datetime.strptime(slot, '%H:%M').time()):
                    isUnavailable = True
                    d['row'] = d['row'] + "<td class='closed' id=''></td>"
            elif abs(dt - today).days == 8:
                if (datetime.now().time() < datetime.strptime(slot, '%H:%M').time()):
                    isUnavailable = True
                    d['row'] = d['row'] + "<td class='notopen' id=''></td>"
            if not isUnavailable:
                if tutorBookings.filter(date=dt, time_start=datetime.strptime(slot, '%H:%M').time()).exists():
                    isUnavailable = True
                    d['row'] = d['row'] + "<td class='unavailable' id=''></td>"
            if not isUnavailable:
                if tutorUnavailable.filter(date=dt, time_start=datetime.strptime(slot, '%H:%M').time()):
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
                d['row'] = d['row'] + "<td class='available' id='" + tdid + "'></td>"

    context = {'dates': BookableDates, 'user': user, 'tutor': tutor, 'today': today, 'slotsToRender': slotsToRender}
    return render(request, 'mainApp/book.html', context)


@csrf_exempt
def confirmation(request, pk):
    if not isAuthenticated(request):
        return redirect('/mainApp/index')
    user = User.objects.get(id=request.session['uid'])
    booking = BookedSlot.objects.get(id=pk)
    charges = 0
    if checkIfTutorPrivate(booking.tutor):
        charges = rateWithCommision(booking.tutor.rate)
    return render(request, 'mainApp/confirmation.html', {'user': user, 'booking': booking, 'charges': charges})


@csrf_exempt
def manageWallet(request):
    if not isAuthenticated(request):
        return JsonResponse({'status': 'fail'})
    w = Wallet.objects.get(user=request.session['uid'])
    user = User.objects.get(id=request.session['uid'])
    if request.GET.get('action', None) == "add":
        transaction = w.add_funds(int(request.GET.get('amount', None)), True)
        wallet_mail_add(user, int(request.GET.get('amount', None)), w, transaction)
    else:
        transaction = w.subtract_funds(int(request.GET.get('amount', None)), True)
        wallet_mail_subtract(user, int(request.GET.get('amount', None)), w, transaction)

    data = {'status': 'success', 'balance': w.balance}
    return JsonResponse(data)


@csrf_exempt
def makeTutor(request):
    if not isAuthenticated(request):
        return JsonResponse({'status': 'fail'})
    user = User.objects.get(id=request.session['uid'])
    if Tutor.objects.filter(user=user).exists():
        return JsonResponse({'status': 'fail'})
    t = None
    if request.POST.get('isPrivate') == 'yes':
        t = user.become_tutor(request.POST.get('shortBio'), True, int(request.POST.get('rate')))
    else:
        t = user.become_tutor(request.POST.get('shortBio'), False)
    request.session['tid'] = t.id
    return JsonResponse({'status': 'success'})


@csrf_exempt
def confirmBooking(request):
    if not isAuthenticated(request):
        return JsonResponse({'status': 'fail', 'message': "Not logged in!"})
    user = User.objects.get(id=request.session['uid'])
    student = Student.objects.get(user=request.session['uid'])
    if request.method == 'GET':
        tutor = Tutor.objects.get(id=request.GET.get('tutorid'))
        tutorBookings = BookedSlot.objects.filter(tutor=tutor, status='BOOKED')
        tutorUnavailable = UnavailableSlot.objects.filter(tutor=tutor)
        dt = parser.parse(request.GET.get('date')).date()
        slot = datetime.strptime(request.GET.get('time'), '%H:%M').time()
        today = date.today()
        if checkIfTutorPrivate(tutor):
            slots, _ = getPrivateSlots()
        else:
            slots, _ = getContractedSlots()
        if request.GET.get('time') not in slots:
            return JsonResponse({'status': 'fail', 'message': "Please select a correct timeslot."})
        if abs(dt - today).days == 1:
            if datetime.now().time() >= slot:
                return JsonResponse({'status': 'fail', 'message': "Booking failed. This slot is now locked!"})
        elif abs(dt - today).days == 8:
            if datetime.now().time() < slot:
                return JsonResponse({'status': 'fail', 'message': "Booking failed. Booking for slot not opened yet!"})
        elif abs(dt - today).days > 8:
            return JsonResponse({'status': 'fail', 'message': "Booking failed. Booking for slot not opened yet!"})
        if tutorBookings.filter(date=dt, time_start=slot).exists():
            return JsonResponse({'status': 'fail', 'message': "Please select an available timeslot"})
        weekDays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        if tutorUnavailable.filter(date=dt, time_start=slot):
            return JsonResponse({'status': 'fail', 'message': "Please select an available timeslot"})
        if tutorBookings.filter(student=student, tutor=tutor, date=dt).exists():
            return JsonResponse({'status': 'fail', 'message': "Can not book two slots for tutor on same day!"})
        booking = None
        transaction = None
        try:
            if checkIfTutorPrivate(tutor):
                booking, transaction = student.create_booking(parser.parse(request.GET.get('date')), slot, 1.0, tutor)
                private_mail_book(student, tutor, dt, slot, booking.time_end, transaction)
            else:
                booking, transaction = student.create_booking(parser.parse(request.GET.get('date')), slot, 0.5, tutor)
                contracted_mail_book(student, tutor, dt, slot, booking.time_end)

            return JsonResponse({'status': 'success', 'booking': booking.id})
        except:
            return JsonResponse({'status': 'fail'})
    else:
        return JsonResponse({'status': 'fail'})


@csrf_exempt
def tutorProfile(request, pk):
    if not isAuthenticated(request):
        return redirect('/mainApp/index')
    tutor = Tutor.objects.get(id=pk)
    user = User.objects.get(id=request.session['uid'])
    courses = tutor.course.all()
    tags = tutor.subject_tags.all()
    reviews = Review.objects.filter(tutor=tutor).order_by('rating').reverse()[:10]
    if reviews.count() >= 3:
        avgRating = tutor.rating
    else:
        avgRating = -1
    return render(request, 'mainApp/tutorProfile.html',
                  {'tutor': tutor, 'user': user, 'courses': courses, 'reviews': reviews, 'rating': avgRating,
                   'tags': tags})


@csrf_exempt
def cancel(request, pk):
    if not isAuthenticated(request):
        return JsonResponse({'status': 'fail'})
    booking = BookedSlot.objects.get(id=pk)
    user = User.objects.get(id=request.session['uid'])
    if not booking.student.user.id == request.session['uid']:
        return JsonResponse(
            {'status': 'fail', 'message': "The booking you are trying to cancel has not been made by you"})
    dt = booking.date
    today = date.today()
    if booking.status == 'CANCELLED':
        return JsonResponse(
            {'status': 'fail', 'message': "The booking you are trying to cancel has already been cancelled"})
    if (dt < today):
        return JsonResponse({'status': 'fail', 'message': "Cannot cancel past booking!"})
    if (abs(dt - today).days == 0):
        return JsonResponse({'status': 'fail',
                             'message': "The booking you are trying to cancel is within the next 24 hours and cannot be cancelled"})
    if (abs(dt - today).days == 1):
        if (datetime.now().time() > booking.time_start):
            return JsonResponse({'status': 'fail',
                                 'message': "The booking you are trying to cancel is within the next 24 hours and cannot be cancelled"})
    try:
        booking.update_booking('CANCELLED')
        if (checkIfTutorPrivate(booking.tutor)):
            transaction = SessionTransaction.objects.get(booking_id=booking, transaction_nature='SESSIONCANCELLED')
            private_mail_cancel(booking.student, booking.tutor, booking.date, booking.time_start, booking.time_end,
                                transaction)
        else:
            contracted_mail_cancel(booking.student, booking.tutor, booking.date, booking.time_start, booking.time_end)

        return JsonResponse({'status': 'success'})
    except:
        return JsonResponse({'status': 'fail'})


@csrf_exempt
def transactionHistory(request):
    if not isAuthenticated(request):
        return redirect('/mainApp/index')
    user = User.objects.get(id=request.session['uid'])
    dt = date.today() - timedelta(days=30)
    transactions = Transaction.objects.filter(user=request.session['uid'], date__gte=dt).order_by("date",
                                                                                                  "time").reverse()
    return render(request, 'mainApp/transactionHistory.html', {'user': user, 'transactions': transactions})


@csrf_exempt
def addCourse(request):
    if not isAuthenticated(request):
        return JsonResponse({'status': 'fail'})

    user = User.objects.get(id=request.session['uid'])
    tutor = Tutor.objects.get(user=user)
    print("the course code value is " + str(request.POST.get('courseCode')))
    courseRequested = Course.objects.get(code=request.POST.get('courseCode'))

    courseRequestedCode = courseRequested.code

    if (tutor.course.filter(code=courseRequestedCode).exists()):
        message_body = "You already have " + str(courseRequestedCode) + " in your list of courses."
        print(message_body)
        return JsonResponse({'status': 'fail'})



    else:
        tutor.add_course(courseRequestedCode)
        message_body = "You added " + str(courseRequestedCode) + " to your list of courses."
        print(message_body)
        return JsonResponse({'status': 'success'})


@csrf_exempt
def removeCourses(request):
    if not isAuthenticated(request):
        return JsonResponse({'status': 'fail'})

    user = User.objects.get(id=request.session['uid'])
    tutor = Tutor.objects.get(user=user)
    listCourses = request.GET.getlist('listCourses[]')
    for courseCode in listCourses:
        tutor.remove_course(courseCode)

    return JsonResponse({'status': 'success'})


@csrf_exempt
def courses(request):
    if not isAuthenticated(request):
        return redirect('/mainApp/index')
    user = User.objects.get(id=request.session['uid'])
    tutor = Tutor.objects.get(user=request.session['uid'])

    presentCourses = tutor.course.all()
    print(presentCourses)
    allCourses = Course.objects.exclude(id__in=presentCourses)
    context = {
        'user': user,
        'tutor': tutor,
        'presentCourses': presentCourses,
        'allCourses': allCourses
    }
    return render(request, 'mainApp/courses.html', context)


@csrf_exempt
def activate_deactivate_tutor(request):
    if not isAuthenticated(request):
        return JsonResponse({'status': 'fail'})
    tutor = Tutor.objects.get(id=request.session['tid'])
    tutor.activate_deactivate()
    return JsonResponse({'status': 'success'})


@csrf_exempt
def manageSchedule(request):
    if not isAuthenticated(request):
        return redirect('/mainApp/index')
    user = User.objects.get(id=request.session['uid'])
    tutor = Tutor.objects.get(user=request.session['uid'])
    weekDays = getWeekdays()
    months = getMonths()
    isPrivate = checkIfTutorPrivate(tutor)
    slots = []
    slotsToRender = []
    if isPrivate:
        slots, slotsToRender = getPrivateSlots()
    else:
        slots, slotsToRender = getContractedSlots()
    upcoming_booking_statuses = ['BOOKED', 'LOCKED']
    tutorBookings = BookedSlot.objects.filter(tutor=tutor, status__in=upcoming_booking_statuses)
    tutorUnavailable = UnavailableSlot.objects.filter(tutor=tutor)
    schedule = []
    # for idx, day in enumerate(weekdays):
    #     row = ""
    #     for slot in slots:
    #         slot_time = datetime.strptime(slot, '%H:%M').time()
    #         booked = upcoming_bookings.filter(date__week_day=idx + 1, time_start=slot_time).exists()
    #         unavailable = unavailable_slots.filter(day=day, time_start=slot_time).exists()
    #         if booked and unavailable:
    #             row = row + "<td class='bookedunavailable' id='" + day + "_" + slot + "'></td>"
    #         elif booked:
    #             row = row + "<td class='booked' id='" + day + "_" + slot + "'></td>"
    #         elif unavailable:
    #             row = row + "<td class='unavailable' id='" + day + "_" + slot + "'></td>"
    #         else:
    #             row = row + "<td class='available' id='" + day + "_" + slot + "'></td>"
    #     schedule.append({'weekday': day, 'row': row})
    today = date.today()
    for i in range(0, 14):
        nextDay = today + timedelta(days=i)
        schedule.append(
            {'dt': nextDay, 'weekday': weekDays[nextDay.weekday()], 'day': nextDay.day,
             'month': months[nextDay.month - 1], 'row': "", 'id': ""})
    for d in schedule:
        dt = d['dt']
        weekday = d['weekday']
        for slot in slots:
            isUnavailable = False
            if not isUnavailable:
                if tutorBookings.filter(date=dt, time_start=datetime.strptime(slot, '%H:%M').time()).exists():
                    isUnavailable = True
                    d['row'] = d['row'] + "<td class='booked' id=''></td>"
            if not isUnavailable:
                if tutorUnavailable.filter(date=dt, time_start=datetime.strptime(slot, '%H:%M').time()):
                    isUnavailable = True
                    day = d['day']
                    month = d['month']
                    if day < 10:
                        day = "0" + str(day)
                    else:
                        day = str(day)
                    tdid = month + "-" + day + "_" + slot
                    d['row'] = d['row'] + "<td class='unavailable' id='" + tdid + "'></td>"
            if not isUnavailable:
                day = d['day']
                month = d['month']
                if day < 10:
                    day = "0" + str(day)
                else:
                    day = str(day)
                tdid = month + "-" + day + "_" + slot
                d['row'] = d['row'] + "<td class='available' id='" + tdid + "'></td>"

    return render(request, 'mainApp/managetimes.html',
                  {'user': user, 'tutor': tutor, 'schedule': schedule, 'slotsToRender': slotsToRender})


@csrf_exempt
def addUnavailable(request):
    if not isAuthenticated(request):
        return JsonResponse({'status': 'fail'})
    user = User.objects.get(id=request.session['uid'])
    tutor = Tutor.objects.get(user=request.session['uid'])
    weekdays = getQuerySetWeekdays()
    isPrivate = checkIfTutorPrivate(tutor)
    slots = []
    slotsToRender = []
    if isPrivate:
        slots, slotsToRender = getPrivateSlots()
    else:
        slots, slotsToRender = getContractedSlots()
    addTime = request.POST.get('time')
    addDay = parser.parse(request.POST.get('day')).date()
    if addTime not in slots:
        return JsonResponse({'status': 'fail'})
    upcoming_booking_statuses = ['BOOKED', 'LOCKED']
    upcoming_bookings = BookedSlot.objects.filter(tutor=tutor, status__in=upcoming_booking_statuses)
    unavailable_slots = UnavailableSlot.objects.filter(tutor=tutor)
    slot_time = datetime.strptime(addTime, '%H:%M').time()
    booked = upcoming_bookings.filter(date=addDay, time_start=slot_time).exists()
    unavailable = unavailable_slots.filter(date=addDay, time_start=slot_time).exists()
    if unavailable:
        return JsonResponse({'status': 'fail'})
    if booked:
        return JsonResponse({'status': 'fail'})
    tutor.create_unavailable_slot(addDay, addTime)
    return JsonResponse({'status': 'success'})


@csrf_exempt
def removeUnavailable(request):
    if not isAuthenticated(request):
        return JsonResponse({'status': 'fail'})
    user = User.objects.get(id=request.session['uid'])
    tutor = Tutor.objects.get(user=request.session['uid'])
    weekdays = getQuerySetWeekdays()
    isPrivate = checkIfTutorPrivate(tutor)
    slots = []
    slotsToRender = []
    if isPrivate:
        slots, slotsToRender = getPrivateSlots()
    else:
        slots, slotsToRender = getContractedSlots()
    addTime = request.POST.get('time')
    addDay = parser.parse(request.POST.get('day')).date()
    if addTime not in slots:
        return JsonResponse({'status': 'fail'})
    # upcoming_booking_statuses = ['BOOKED', 'LOCKED']
    # upcoming_bookings = BookedSlot.objects.filter(tutor=tutor, status__in=upcoming_booking_statuses)
    unavailable_slots = UnavailableSlot.objects.filter(tutor=tutor)
    slot_time = datetime.strptime(addTime, '%H:%M').time()
    # booked = upcoming_bookings.filter(date__week_day=weekdays.index(addDay)+1, time_start=slot_time).exists()
    unavailable = unavailable_slots.filter(date=addDay, time_start=slot_time).exists()
    if not unavailable:
        return JsonResponse({'status': 'fail'})
    tutor.remove_unavailable_slot(addDay, slot_time)
    return JsonResponse({'status': 'success'})


def getResetPwdToken(request):
    token, user = makeToken(request.GET.get('email'))
    print(token)
    if token is None:
        return JsonResponse({'status': 'fail'})
    else:
        pwd_reset_mail(user, token)
        return JsonResponse({'status': 'success'})


@csrf_exempt
def resetPwd(request):
    if 'token' not in request.GET:
        return render(request, 'mainApp/resetpwd.html', {'invalid': 1})
    else:
        user, _ = checkToken(request.GET.get('token'))
        if user is not None:
            return render(request, 'mainApp/resetpwd.html', {'invalid': 0, 'token': request.GET.get('token')})
        else:
            return render(request, 'mainApp/resetpwd.html', {'invalid': 1})


@csrf_exempt
def setNewPwd(request):
    user, pwdtkn = checkToken(request.POST.get('token'))
    if user is None:
        return JsonResponse({'status': 'fail'})
    else:
        setattr(user, 'password', make_password(request.POST.get('newpwd')))
        user.save()
        pwdtkn.delete()
        return JsonResponse({'status': 'success'})


@csrf_exempt
def tags(request):
    if not isAuthenticated(request):
        return redirect('/mainApp/index')
    user = User.objects.get(id=request.session['uid'])
    tutor = Tutor.objects.get(user=request.session['uid'])

    presentTags = tutor.subject_tags.all()
    print("the present tags are", presentTags)
    allTags = Tag.objects.exclude(id__in=presentTags)
    print("all tags: ", allTags)
    context = {
        'user': user,
        'tutor': tutor,
        'presentTags': presentTags,
        'allTags': allTags
    }
    return render(request, 'mainApp/tags.html', context)


@csrf_exempt
def addTag(request):
    if not isAuthenticated(request):
        return JsonResponse({'status': 'fail1'})

    user = User.objects.get(id=request.session['uid'])
    tutor = Tutor.objects.get(user=user)

    tagRequestedName = request.POST.get('tagName')

    


    create = request.POST.get('create')

    if create == "true":
        create = True
        

        if tutor.subject_tags.filter(tag_name__iexact=tagRequestedName).exists():
            return JsonResponse({'status': 'fail3'})

        elif Tag.objects.filter(tag_name__iexact=tagRequestedName).exists():
            return JsonResponse({'status': 'fail2'})

    else:
        create = False

    tutor.add_tag(tagRequestedName, create)
    message_body = "You added " + str(tagRequestedName) + " to your list of tags."
    print(message_body)
    return JsonResponse({'status': 'success'})


@csrf_exempt
def removeTags(request):
    if not isAuthenticated(request):
        return JsonResponse({'status': 'fail'})

    user = User.objects.get(id=request.session['uid'])
    tutor = Tutor.objects.get(user=user)
    listTags = request.GET.getlist('listTags[]')
    for tagName in listTags:
        tutor.remove_tag(tagName)

    return JsonResponse({'status': 'success'})


@csrf_exempt
def addReview(request, pk):
    if not isAuthenticated(request):
        return JsonResponse({'status': 'fail1'})
    user = User.objects.get(id=request.session['uid'])
    booking = BookedSlot.objects.filter(id=pk, status='ENDED')
    if not booking.exists():
        return JsonResponse({'status': 'fail2'})
    else:
        booking = booking[0]
    student = Student.objects.get(id=booking.student.id)
    if not student.user == user:
        return JsonResponse({'status': 'fail3'})
    review = Review.objects.filter(booking=booking)
    if review.exists():
        return JsonResponse({'status': 'fail4'})
    print(request.GET.get('rating'))
    review = Review(tutor=booking.tutor, student=booking.student, rating=request.GET.get('rating'),
                    content=request.GET.get('content'), reviewtype=request.GET.get('type'), booking=booking)
    review.save()

    booking.tutor.update_rating()
    return JsonResponse({'status': 'success'})


@csrf_exempt
def admin(request):
    if request.method == 'POST':
        if 'login' in request.POST:
            if Admin.objects.filter(user_name=request.POST.get('username'), password=request.POST.get('pwd')).exists():
                w = SpecialWallet.objects.get(name='MyTutor')
                return render(request, 'mainApp/adminwallet.html', {'wallet': w})
            else:
                return render(request, 'mainApp/admin.html')
        else:
            return render(request, 'mainApp/admin.html')
    else:
        return render(request, 'mainApp/admin.html')


@csrf_exempt
def adminWithdraw(request):
    w = SpecialWallet.objects.get(name='MyTutor')
    w.subtract_funds(float(request.POST.get('amount')))
    admin_withdraw_mail(request.POST.get('amount'), w.balance)
    return JsonResponse({'status': 'success', 'wallet': w.balance})
