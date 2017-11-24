from .models import *
import math


# functions

def rateWithCommision(tutorRate):
    return round(tutorRate * 1.05, 2)


def checkUser(uid, request):
    isTutor = False
    isStudent = False
    if 'tid' in request.session:
        isTutor = True
    if 'sid' in request.session:
        isStudent = True
    return isTutor, isStudent


def checkUserFromDB(uid):
    isTutor = Tutor.objects.filter(user=uid).exists()
    isStudent = Student.objects.filter(user=uid).exists()
    return isTutor, isStudent


def isAuthenticated(request):
    if 'uid' not in request.session:
        return False
    else:
        return True


def getTutor(uid):
    return Tutor.objects.get(user=uid)


def getStudent(uid):
    return Student.objects.get(user=uid)


def getPrivateSlots():
    slots = []
    slotsToRender = ["07:00-08:00", "08:00-09:00", "09:00-10:00", "10:00-11:00", "11:00-12:00", "12:00-13:00",
                     "13:00-14:00", "14:00-15:00"]
    for t in slotsToRender:
        slots.append(t.split('-')[0])
    return slots, slotsToRender


def getContractedSlots():
    slots = []
    slotsToRender = ["07:00-07:30", "07:30-08:00", "08:00-08:30", "08:30-09:00", "09:00-09:30", "09:30-10:00",
                     "10:00-10:30", "10:30-11:00", "11:00-11:30", "11:30-12:00", "12:00-12:30", "12:30-13:00",
                     "13:00-13:30", "13:30-14:00", "14:30-15:00"]
    for t in slotsToRender:
        slots.append(t.split('-')[0])
    return slots, slotsToRender


def getWeekdays():
    return ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']


def getMonths():
    return ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']


def getQuerySetWeekdays():
    return ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']


def checkIfTutorPrivate(tutor):
    return isinstance(tutor, PrivateTutor)
