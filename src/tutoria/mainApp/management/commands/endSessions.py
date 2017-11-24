from django.core.management.base import BaseCommand
from mainApp.models import *
from django.db.models import Q
from datetime import timedelta
from mainApp.functions import checkIfTutorPrivate, review_email, wallet_mail_add


class Command(BaseCommand):
    def handle(self, **options):
        BookingsEnded = BookedSlot.objects.filter(
            Q(date=date.today(), time_end__lt=datetime.now().time(), status='STARTED') | Q(date__lt=date.today(),
                                                                                             status='STARTED'))
        TempWallet = SpecialWallet.objects.get(name='Temporary')
        MyTutorWallet = SpecialWallet.objects.get(name='MyTutor')
        for booking in BookingsEnded:
            if checkIfTutorPrivate(booking.tutor):
                try:
                    transaction = SessionTransaction.objects.get(booking_id=booking)
                    TempWallet.subtract_funds(transaction.amount)
                    booking.tutor.user.wallet.add_funds(transaction.tutorCharges)
                    MyTutorWallet.add_funds(transaction.commission)
                except:
                    pass
            booking.update_booking('ENDED')
            review_email(booking)
            wallet_mail_add(booking.tutor.user, transaction.tutorCharges,booking.tutor.user.wallet, transaction)
