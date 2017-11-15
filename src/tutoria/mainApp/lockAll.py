
import hashlib
from datetime import datetime, timedelta, date
from dateutil import parser
from .models import BookedSlot
import math

BookingsStarted = BookedSlot.objects.filter(date>date.today(), time_start>datetime.now().time(), status='BOOKED')
for booking in BookingsStarted:
    booking.status='STARTED'
    booking.save()