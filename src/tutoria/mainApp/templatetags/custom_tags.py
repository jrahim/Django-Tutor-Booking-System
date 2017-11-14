from django import template
register = template.Library()
from mainApp.models import PrivateTutor, SessionTransaction

@register.filter
def mult(value, arg):
    return round(int(value)*float(arg), 2)
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