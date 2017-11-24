from django import template

register = template.Library()
from mainApp.models import PrivateTutor, SessionTransaction
from datetime import date, datetime


@register.filter
def mult(value, arg):
    return round(int(value) * float(arg), 2)


register.filter('mult', mult)


@register.filter
def firstname(value):
    return value.split(' ')[0]


register.filter('firstname', firstname)


@register.filter
def isPrivate(value):
    return isinstance(value, PrivateTutor)


register.filter('isPrivate', isPrivate)


@register.filter
def isSessionTransaction(value):
    return isinstance(value, SessionTransaction)


register.filter('isSessionTransaction', isSessionTransaction)


@register.filter
def isCancellable(value):
    if value.status == "BOOKED":
        return True
    else:
        return False


register.filter('isCancellable', isCancellable)


@register.filter
def getWeekDay(value):
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    return days[value.weekday()]


register.filter('getWeekDay', getWeekDay)
