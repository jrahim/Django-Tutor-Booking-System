from django import template
register = template.Library()
import math
from mainApp.models import PrivateTutor

@register.filter
def mult(value, arg):
    return math.ceil(int(value)*float(arg))
register.filter('mult', mult)

@register.filter
def firstname(value):
    return value.split(' ')[0]
register.filter('firstname', firstname)

@register.filter
def isPrivate(value):
    return isinstance(value, PrivateTutor)
register.filter('isPrivate', isPrivate)
