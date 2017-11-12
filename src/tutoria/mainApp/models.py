from django.db import models
from datetime import date, time, datetime, timedelta
from django.db.models import Q
from django.core import mail
from math import ceil
from polymorphic.models import PolymorphicModel


# Create your models here.

class Wallet(models.Model):
    balance = models.PositiveIntegerField()

    # user = models.ForeignKey(User, on_delete=models.CASCADE)

    def add_funds(self, amount):
        self.balance += amount
        self.save()

    def subtract_funds(self, amount):
        self.balance -= amount
        self.save()

    def __str__(self):
        return str(self.id)


class User(models.Model):
    name = models.CharField(max_length=200)
    avatar = models.ImageField(upload_to='avatar')
    email = models.EmailField(max_length=254)
    password = models.CharField(max_length=200)
    contact = models.CharField(max_length=20, blank=True)
    wallet = models.OneToOneField(Wallet)

    # @transaction.atomic
    # def save(self, *args, **kwargs):
    #     super(User, self).save(*args, **kwargs)
    #     if not Wallet.objects.filter(user=self).exists():
    #         w = Wallet(balance=0, user=self)
    #         w.save()

    def create_wallet(self):
        w = Wallet(balance=0)
        w.save()
        return w

    def become_student(self):
        s = Student(user=self)
        s.save()
        return s

    def become_tutor(self, short_bio, rate, is_private):
        t = Tutor(user=self, shortBio=short_bio, rate=rate,
                  isPrivate=is_private)  # what to do about course
        t.save()
        return t

    def get_upcoming_bookings(self, isTutor, isStudent):

        if isTutor and isStudent:
            t = Tutor.objects.get(user=self)
            s = Student.objects.get(user=self)
            array1 = BookedSlot.objects.filter(tutor=t, status='BOOKED').order_by('date')
            array2 = BookedSlot.objects.filter(student=s, status='BOOKED').order_by('date')
            return array1, array2

        if isStudent and not isTutor:
            s = Student.objects.get(user=self)
            array = BookedSlot.objects.filter(student=s, status='BOOKED').order_by('date')
            return array

        if isTutor and not isStudent:
            t = Tutor.objects.get(user=self)
            array = BookedSlot.objects.filter(tutor=t, status='BOOKED').order_by('date')
            return array

    def get_past_bookings(self, isTutor, isStudent):
        if isTutor and isStudent:
            student = Student.objects.get(user=self)
            tutor = Tutor.objects.filter(user=self)
            a1 = BookedSlot.objects.filter(
                Q(student=student, status='ENDED') | Q(tutor=tutor, status='ENDED')).order_by('date').reverse()
        elif isStudent:
            student = Student.objects.get(user=self)
            a1 = BookedSlot.objects.filter(Q(student=student, status='ENDED'))
        else:
            tutor = Tutor.objects.filter(user=self)
            a1 = BookedSlot.objects.filter(Q(tutor=tutor, status='ENDED'))
        return a1

    def send_mail(self, mail_to, mail_from, message_body, message_subject):
        connection = mail.get_connection()
        connection.open()
        email = mail.EmailMessage(
            message_subject,
            message_body,
            mail_from,
            [mail_to],
            connection=connection,
        )
        email.send()  # Send the email
        # We need to manually close the connection.
        connection.close()
        return

    def __str__(self):
        return self.name


class Course(models.Model):
    code = models.CharField(max_length=50)
    title = models.CharField(max_length=200)

    def __str__(self):
        return self.title


class Tutor(models.Model):
    user = models.OneToOneField(User)
    course = models.ManyToManyField(Course, blank=True)
    shortBio = models.CharField(max_length=300)
    rate = models.PositiveIntegerField(default=0)
    rating = models.FloatField(default=0)
    isPrivate = models.BooleanField()

    def create_unavailable_slot(self, day, time_start, duration):
        unavailable = UnavailableSlot(tutor=self, day=day, time_start=time_start, duration=duration)
        unavailable.save()

    def __str__(self):
        return self.user.name


class Student(models.Model):
    user = models.OneToOneField(User)

    def create_booking(self, date, time_start, duration, tutor):
        end = (datetime.strptime(str(time_start), '%H:%M:%S') + timedelta(hours=duration)).time()
        booking = BookedSlot(date=date, time_start=time_start, time_end=end, tutor=tutor, student=self, status="BOOKED")
        self.user.wallet.subtract_funds(ceil(tutor.rate * 1.05))
        TempWallet = SpecialWallet.objects.get(name='Temporary')
        TempWallet.add_funds(ceil(tutor.rate * 1.05))
        booking.save()
        booking.create_transaction_record("SESSIONBOOKED", True, True)
        return booking

    def __str__(self):
        return self.user.name


class BookedSlot(models.Model):
    date = models.DateField()
    time_start = models.TimeField()
    time_end = models.TimeField()
    tutor = models.ForeignKey(Tutor, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    STATUSES = (
        ('BOOKED', 'booked'),
        ('LOCKED', 'locked'),
        ('STARTED', 'started'),
        ('ENDED', 'ended'),
        ('CANCELLED', 'cancelled')
    )
    status = models.CharField(max_length=9, choices=STATUSES)

    def update_booking(self, new_status):
        setattr(self, 'status', new_status)
        if new_status == "CANCELLED":
            self.create_transaction_record("SESSIONCANCELLED", True)
        elif new_status == "ENDED":
            self.create_transaction_record("SESSIONBOOKED", False)
        self.save()

    def create_transaction_record(self, transactionNature, forStudent, isCreated=False):
        if forStudent:
            if isCreated:
                transaction = SessionTransaction(amount=ceil(self.tutor.rate * 1.05), date=date.today(),
                                                 time=datetime.now().time(),
                                                 other_party=self.tutor.user, transaction_nature=transactionNature,
                                                 user=self.student.user,
                                                 booking_id=self, commission=ceil(self.tutor.rate * 0.05),
                                                 tutorCharges=self.tutor.rate)
                transaction.save()
            else:
                student_transaction = SessionTransaction.objects.get(booking_id=self)
                transaction = SessionTransaction(amount=ceil(student_transaction.amount), date=date.today(),
                                                 time=datetime.now().time(),
                                                 other_party=self.tutor.user, transaction_nature=transactionNature,
                                                 user=self.student.user,
                                                 booking_id=self)
                transaction.save()
        else:
            student_transaction = SessionTransaction.objects.get(booking_id=self)
            transaction = SessionTransaction(amount=student_transaction.tutorCharges, date=date.today(),
                                             time=datetime.now().time(),
                                             other_party=self.student.user,
                                             transaction_nature=transactionNature, user=self.tutor.user,
                                             booking_id=self, commission=student_transaction.commission,
                                             tutorCharges=student_transaction.tutorCharges)
            transaction.save()

    def __str__(self):
        return self.student.user.name + self.tutor.user.name


class UnavailableSlot(models.Model):
    tutor = models.ForeignKey(Tutor, on_delete=models.CASCADE)
    day = models.CharField(max_length=3)
    time_start = models.TimeField()
    duration = models.FloatField()


class Transaction(models.Model):
    user = models.ForeignKey(User)
    amount = models.PositiveIntegerField()
    date = models.DateField()
    time = models.TimeField()


class SessionTransaction(Transaction):
    TransactionNatures = (
        ('SESSIONBOOKED', 'sessionBooked'),
        ('SESSIONCANCELLED', 'sessionCancelled')
    )
    transaction_nature = models.CharField(max_length=20, choices=TransactionNatures)
    booking_id = models.ForeignKey(BookedSlot, default=None)
    tutorCharges = models.PositiveIntegerField()
    commission = models.PositiveIntegerField()
    other_party = models.ForeignKey(User, related_name='other_party')


class WalletTransaction(Transaction):
    TransactionNatures = (
        ('FUNDSADDED', 'fundsAdded'),
        ('FUNDSWITHDRAWN', 'fundsWithdrawn')
    )
    transaction_nature = models.CharField(max_length=20, choices=TransactionNatures)
    wallet_id = models.ForeignKey(Wallet, default=None)


class SpecialWallet(Wallet):
    name = models.CharField(max_length=20, unique=True)
