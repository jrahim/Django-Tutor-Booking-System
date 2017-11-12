from django.core.management.base import BaseCommand
from mainApp.models import *
from django.db.models import Q


class Command(BaseCommand):
    def handle(self, **options):
        BookingsStarted = BookedSlot.objects.filter(Q(date=date.today(), time_start__gte=datetime.now().time(),
                                                      status='BOOKED') | Q(date__lt=date.today(), status='BOOKED'))
        for booking in BookingsStarted:
            booking.status = 'STARTED'
            booking.save()