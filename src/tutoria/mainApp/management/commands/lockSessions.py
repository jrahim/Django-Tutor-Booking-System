from django.core.management.base import BaseCommand
from mainApp.models import *
from django.db.models import Q


class Command(BaseCommand):
    def handle(self, **options):
        BookingsToLock = BookedSlot.objects.filter(Q(date__lte=date.today(), status='BOOKED') | Q(
            date=(datetime.now() + timedelta(days=1)).date(), time_start__lte=datetime.now().time(), status='BOOKED'))
        for booking in BookingsToLock:
            booking.update_booking('LOCKED')

        BookingsStarted = BookedSlot.objects.filter(Q(date=date.today(), time_start__lte=datetime.now().time(),
                                                      status='LOCKED') | Q(date__lt=date.today(), status='LOCKED'))
        for booking in BookingsStarted:
            booking.update_booking('STARTED')
