from dateutil import parser
from django.contrib.auth.hashers import make_password, check_password
from django.core.validators import validate_email
from django.db.models import Max
from django.http import JsonResponse
from django.shortcuts import redirect
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from .forms import ImageForm
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
                                request.POST.get("password")))  # make a new user with md5 hash of pwd
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
    if university == "0":
        university = ""
    course = request.POST.get('course', "")
    if course == "0":
        course = ""
    tag = request.POST.get('tag', "")
    if tag == "0":
        tag = ""
    max_rate = request.POST.get('maxRate', "")
    min_rate = request.POST.get('minRate', "")

    # sort
    sort = request.POST.get('sort', "")

    if tutor_type == "tutorPrivate":
        tutor_type = PrivateTutor
    elif tutor_type == "tutorContracted":
        tutor_type = ContractedTutor

    tutor_list = Tutor.objects.all()

    if given_name != "":
        user_list = User.objects.filter(name__istartswith=given_name)  # case insensitive matching - exact matching
        tutor_list = tutor_list.filter(user__in=user_list)

    if last_name != "":
        user_list = User.objects.filter(last_name__iexact=last_name)  # case insensitive matching - exact matching
        tutor_list = tutor_list.filter(user__in=user_list)

    if tutor_type != "":
        tutor_list = tutor_list.filter(Q(instance_of=tutor_type))

    if university != "":
        university_list = University.objects.filter(
            id=university)  # contains to allow custom input search
        tutor_list = tutor_list.filter(university__in=university_list)

    if course != "":
        course_list = Course.objects.filter(id=course)  # course code
        tutor_list = tutor_list.filter(course__in=course_list)

    if tag != "":
        tag_list = Tag.objects.filter(id=tag)
        tutor_list = tutor_list.filter(subject_tags__in=tag_list)

    if max_rate != "" and min_rate != "":
        if min_rate == "0":
            tutor_list = tutor_list.filter(
                Q(PrivateTutor___rate__lte=max_rate) & Q(PrivateTutor___rate__gte=min_rate) | Q(
                    instance_of=ContractedTutor))
        else:
            tutor_list = tutor_list.filter(
                Q(PrivateTutor___rate__lte=max_rate) & Q(PrivateTutor___rate__gte=min_rate))
    elif max_rate == "" and min_rate != "":
        max_query = Tutor.objects.all().aggregate(maxvalue=Max('PrivateTutor___rate'))
        if min_rate == "0":
            tutor_list = tutor_list.filter(
                Q(PrivateTutor___rate__lte=max_query['maxvalue']) & Q(PrivateTutor___rate__gte=min_rate) | Q(
                    instance_of=ContractedTutor))
        else:
            tutor_list = tutor_list.filter(
                Q(PrivateTutor___rate__lte=max_query['maxvalue']) & Q(PrivateTutor___rate__gte=min_rate))
    elif max_rate != "" and min_rate == "":
        tutor_list = tutor_list.filter(
            Q(PrivateTutor___rate__lte=max_rate) & Q(PrivateTutor___rate__gte=0) | Q(
                instance_of=ContractedTutor))

    # TODO only display tutors with an available slot in the coming 7 days

    if sort != "" and sort == "rateAsc":
        tutor_list = tutor_list.order_by('PrivateTutor___rate')
    elif sort != "" and sort == "rateDesc":
        tutor_list = tutor_list.order_by('-PrivateTutor___rate')
    else:
        tutor_list = tutor_list.order_by('PrivateTutor___rate')

    params = {'given_name': given_name, 'last_name': last_name, 'university': university,
              'tutor_type': request.POST.get('tutorType', ""), 'course': course, 'tag': tag, 'sort': sort,
              'max_rate': request.POST.get('maxRate', ""), 'min_rate': request.POST.get('minRate', "")}

    context = {
        'tutor_list': tutor_list,
        'user': user,
        'tag_list': tags,
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
    isTutor, isStudent = checkUser('uid', request);
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
    weekDays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
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
                if tutorUnavailable.filter(day=weekday, time_start=datetime.strptime(slot, '%H:%M').time()):
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
        w.add_funds(int(request.GET.get('amount', None)), True)
        message_body = "You added $" + str(
            request.GET.get('amount', None)) + " to your wallet."  # notification for wallet
    else:
        w.subtract_funds(int(request.GET.get('amount', None)), True)
        message_body = "You subtracted $" + str(request.GET.get('amount', None)) + " from your wallet."

    message_subject = "Wallet Update"
    mail_to = str(user.email)
    mail_from = "My Tutors"

    user.send_mail(mail_to, mail_from, message_body, message_subject)

    data = {'status': 'success'}
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
        print(request.GET.get('time'))
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
        if tutorUnavailable.filter(day=weekDays[dt.weekday()], time_start=slot):
            return JsonResponse({'status': 'fail', 'message': "Please select an available timeslot"})
        if tutorBookings.filter(student=student, tutor=tutor, date=dt).exists():
            return JsonResponse({'status': 'fail', 'message': "Can not book two slots for tutor on same day!"})
        booking = None
        transaction = None
        try:
            if checkIfTutorPrivate(tutor):
                booking, transaction = student.create_booking(parser.parse(request.GET.get('date')), slot, 1.0, tutor)
            else:
                booking, transaction = student.create_booking(parser.parse(request.GET.get('date')), slot, 0.5, tutor)
            # SEND NOTIFICATION ON BOOKING TO TUTOR
            message_subject = "New Booking"
            message_body = "You have been booked by " + student.user.name + " on " + str(
                parser.parse(request.GET.get('date'))) + "."
            mail_to = str(tutor.user.email)
            mail_from = "My Tutors"

            user.send_mail(mail_to, mail_from, message_body, message_subject)

            # SEND NOTIFICATION ON BOOKING TO STUDENT ABOUT WALLET
            message_subject = "Booking Update"
            message_body = "You booked  " + tutor.user.name + " on " + str(
                parser.parse(request.GET.get('date')))
            mail_to = str(student.user.email)
            mail_from = "My Tutors"

            user.send_mail(mail_to, mail_from, message_body, message_subject)

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
    return render(request, 'mainApp/tutorProfile.html', {'tutor': tutor, 'user': user, 'courses': courses})


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

        # NOTIFICATION ON Cancellation TO TUTOR
        message_subject = "Booking Cancellation"
        message_body = "Your booking on " + str(
            booking.date) + " have been cancelled by " + booking.student.user.name + ". "
        mail_to = str(booking.tutor.user.email)
        mail_from = "My Tutors"

        user.send_mail(mail_to, mail_from, message_body, message_subject)

        # SEND NOTIFICATION ON Cancellation TO STUDENT ABOUT WALLET
        message_subject = "Booking Update"
        message_body = "You cancelled  " + booking.tutor.user.name + " on " + str(booking.date)
        mail_to = str(booking.student.user.email)
        mail_from = "My Tutors"

        user.send_mail(mail_to, mail_from, message_body, message_subject)

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
