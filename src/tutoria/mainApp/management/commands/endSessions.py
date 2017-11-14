from django.core.management.base import BaseCommand
from mainApp.models import *
from django.db.models import Q
from datetime import timedelta


class Command(BaseCommand):
    def handle(self, **options):
        BookingsEnded = BookedSlot.objects.filter(
            Q(date=date.today(), time_end__lt=datetime.now().time(), status='STARTED') | Q(date__lt=date.today(),
                                                                                             status='STARTED'))
        TempWallet = SpecialWallet.objects.get(name='Temporary')
        MyTutorWallet = SpecialWallet.objects.get(name='MyTutor')
        for booking in BookingsEnded:
            transaction = SessionTransaction.objects.get(booking_id=booking)
            TempWallet.subtract_funds(transaction.amount)
            booking.tutor.user.wallet.add_funds(transaction.tutorCharges)
            MyTutorWallet.add_funds(transaction.commission)
            booking.update_booking('ENDED')
