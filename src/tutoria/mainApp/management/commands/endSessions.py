from django.core.management.base import BaseCommand
from mainApp.models import *
from django.db.models import Q
from datetime import timedelta


class Command(BaseCommand):
    def handle(self, **options):
        BookingsEnded = BookedSlot.objects.filter(
            Q(date=date.today(), time_end__lt=datetime.now().time(), status='STARTED') | Q(date__lt=date.today(),
                                                                                             status='STARTED'))
        for booking in BookingsEnded:
            booking.status = "ENDED"
            booking.save()
        t = datetime.now().time()
