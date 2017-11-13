from django.core.management.base import BaseCommand
from mainApp.models import *
from polymorphic.utils import reset_polymorphic_ctype




class Command(BaseCommand):
    def handle(self, **options):
        reset_polymorphic_ctype(Wallet, Tutor, Transaction, PrivateTutor, ContractedTutor, SpecialWallet, SessionTransaction, WalletTransaction)

