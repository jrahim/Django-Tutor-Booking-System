from datetime import date, datetime, timedelta

from django.core import mail
from django.db import models
from django.db.models import Q
from polymorphic.models import PolymorphicModel


# Create your models here.

class University(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class Wallet(PolymorphicModel):
    balance = models.FloatField()

    # user = models.ForeignKey(User, on_delete=models.CASCADE)

    def add_funds(self, amount, isWalletManagement=False):
        self.balance += amount
        if isWalletManagement:
            user = User.objects.get(wallet=self)
            transaction = WalletTransaction(user=user, amount=amount, date=date.today(), time=datetime.now().time(),
                                            transaction_nature="FUNDSADDED", wallet_id=self)
            transaction.save()
        self.save()

    def subtract_funds(self, amount, isWalletManagement=False):
        self.balance -= amount
        if isWalletManagement:
            user = User.objects.get(wallet=self)
            transaction = WalletTransaction(user=user, amount=amount, date=date.today(), time=datetime.now().time(),
                                            transaction_nature="FUNDSWITHDRAWN", wallet_id=self)
            transaction.save()
        self.save()

    def __str__(self):
        return str(self.id)


class User(models.Model):
    name = models.CharField(max_length=200)  # given name
    last_name = models.CharField(max_length=200, blank=True)
    avatar = models.ImageField(upload_to='avatar')
    email = models.EmailField(max_length=254, unique=True)
    password = models.CharField(max_length=200)
    contact = models.CharField(max_length=20, blank=True)
    wallet = models.OneToOneField(Wallet)

    def create_wallet(self):
        w = Wallet(balance=0)
        w.save()
        return w

    def become_student(self):
        s = Student(user=self)
        s.save()
        return s

    def become_tutor(self, short_bio, is_private, rate=0):
        if is_private:
            t = PrivateTutor(user=self, shortBio=short_bio, rate=rate)
            t.save()
        else:
            t = ContractedTutor(user=self, shortBio=short_bio)
            t.save()
        return t

    def get_upcoming_bookings(self, isTutor, isStudent):
        statusesToGet = ['BOOKED', 'LOCKED', 'STARTED']

        if isTutor and isStudent:
            t = Tutor.objects.get(user=self)
            s = Student.objects.get(user=self)
            array1 = BookedSlot.objects.filter(tutor=t, status__in=statusesToGet).order_by('date')
            array2 = BookedSlot.objects.filter(student=s, status__in=statusesToGet).order_by('date')
            return array1, array2

        if isStudent and not isTutor:
            s = Student.objects.get(user=self)
            array = BookedSlot.objects.filter(student=s, status__in=statusesToGet).order_by('date')
            return array

        if isTutor and not isStudent:
            t = Tutor.objects.get(user=self)
            array = BookedSlot.objects.filter(tutor=t, status__in=statusesToGet).order_by('date')
            return array

    def get_past_bookings(self, isTutor, isStudent):
        if isTutor and isStudent:
            student = Student.objects.get(user=self)
            tutor = Tutor.objects.filter(user=self)
            a1 = BookedSlot.objects.filter(
                Q(student=student, status='ENDED') | Q(tutor=tutor, status='ENDED')).order_by('date').reverse()
        elif isStudent:
            student = Student.objects.get(user=self)
            a1 = BookedSlot.objects.filter(Q(student=student, status='ENDED')).order_by('date').reverse()
        else:
            tutor = Tutor.objects.filter(user=self)
            a1 = BookedSlot.objects.filter(Q(tutor=tutor, status='ENDED')).order_by('date').reverse()
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
    university = models.ForeignKey(University, on_delete=models.CASCADE, default=1)

    def __str__(self):
        return self.title


class Tag(models.Model):
    tag_name = models.CharField(max_length=200)

    def __str__(self):
        return self.tag_name


class Tutor(PolymorphicModel):
    user = models.OneToOneField(User)
    course = models.ManyToManyField(Course, blank=True)
    shortBio = models.CharField(max_length=300)
    rating = models.FloatField(default=0)
    subject_tags = models.ManyToManyField(Tag, blank=True)
    university = models.ManyToManyField(University, blank=True)
    isActivated = models.BooleanField(default=True)

    def create_unavailable_slot(self, day, time_start, duration):
        unavailable = UnavailableSlot(tutor=self, day=day, time_start=time_start, duration=duration)
        unavailable.save()

    def add_course(self, courseCode):
        c = Course.objects.get(code=courseCode)
        self.course.add(c)
        self.save()

    def remove_course(self, courseCode):
        c = Course.objects.get(code=courseCode)
        self.course.remove(c)
        self.save()

    def activate_deactivate(self):
        if self.isActivated:
            self.isActivated = False
            self.save()
        else:
            self.isActivated = True
            self.save()

    def __str__(self):
        return self.user.name


class PrivateTutor(Tutor):
    rate = models.PositiveIntegerField()

    def __str__(self):
        return self.user.name


class ContractedTutor(Tutor):
    def __str__(self):
        return self.user.name


class Student(models.Model):
    user = models.OneToOneField(User)

    def create_booking(self, date, time_start, duration, tutor):
        end = (datetime.strptime(str(time_start), '%H:%M:%S') + timedelta(hours=duration)).time()
        booking = BookedSlot(date=date, time_start=time_start, time_end=end, tutor=tutor, student=self, status="BOOKED")
        booking.save()
        transaction = None
        if isinstance(tutor, PrivateTutor):
            chargesWithCommission = round(tutor.rate * 1.05, 2)
            self.user.wallet.subtract_funds(chargesWithCommission)
            TempWallet = SpecialWallet.objects.get(name='Temporary')
            TempWallet.add_funds(chargesWithCommission)
            transaction = booking.create_transaction_record("SESSIONBOOKED", True, True)
        return booking, transaction

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
            if isinstance(self.tutor, PrivateTutor):
                booking_transaction = SessionTransaction.objects.get(booking_id=self)
                tempWallet = SpecialWallet.objects.get(name='Temporary')
                tempWallet.subtract_funds(booking_transaction.amount)
                self.student.user.wallet.add_funds(booking_transaction.amount)
                self.create_transaction_record("SESSIONCANCELLED", True)
        elif new_status == "ENDED":
            self.create_transaction_record("SESSIONBOOKED", False)
        self.save()

    def create_transaction_record(self, transactionNature, forStudent, isCreated=False):
        if forStudent:
            if isCreated:
                amount = 0
                tutorRate = 0
                commission = 0
                if isinstance(self.tutor, PrivateTutor):
                    amount = round(self.tutor.rate * 1.05, 2)
                    tutorRate = self.tutor.rate
                    commission = round(self.tutor.rate * 0.05, 2)
                transaction = SessionTransaction(amount=amount, date=date.today(),
                                                 time=datetime.now().time(),
                                                 other_party=self.tutor.user, transaction_nature=transactionNature,
                                                 user=self.student.user,
                                                 booking_id=self, commission=commission,
                                                 tutorCharges=tutorRate)
                transaction.save()
                return transaction
            else:
                student_transaction = SessionTransaction.objects.get(booking_id=self)
                transaction = SessionTransaction(amount=student_transaction.amount, date=date.today(),
                                                 time=datetime.now().time(),
                                                 other_party=self.tutor.user, transaction_nature=transactionNature,
                                                 user=self.student.user, commission=student_transaction.commission,
                                                 tutorCharges=student_transaction.tutorCharges, booking_id=self)
                transaction.save()
                return transaction
        else:
            student_transaction = SessionTransaction.objects.get(booking_id=self)
            transaction = SessionTransaction(amount=student_transaction.tutorCharges, date=date.today(),
                                             time=datetime.now().time(),
                                             other_party=self.student.user,
                                             transaction_nature=transactionNature, user=self.tutor.user,
                                             booking_id=self, commission=student_transaction.commission,
                                             tutorCharges=student_transaction.tutorCharges)
            transaction.save()
            return transaction

    def __str__(self):
        return str(self.id) + self.student.user.name + self.tutor.user.name


class UnavailableSlot(models.Model):
    tutor = models.ForeignKey(Tutor, on_delete=models.CASCADE)
    day = models.CharField(max_length=3)
    time_start = models.TimeField()
    duration = models.FloatField()


class Transaction(PolymorphicModel):
    user = models.ForeignKey(User)
    amount = models.FloatField()
    date = models.DateField()
    time = models.TimeField()


class SessionTransaction(Transaction):
    SessionTransactionNatures = (
        ('SESSIONBOOKED', 'sessionBooked'),
        ('SESSIONCANCELLED', 'sessionCancelled')
    )
    transaction_nature = models.CharField(max_length=20, choices=SessionTransactionNatures)
    booking_id = models.ForeignKey(BookedSlot, default=None)
    tutorCharges = models.PositiveIntegerField()
    commission = models.FloatField()
    other_party = models.ForeignKey(User, related_name='other_party')


class WalletTransaction(Transaction):
    WalletTransactionNatures = (
        ('FUNDSADDED', 'fundsAdded'),
        ('FUNDSWITHDRAWN', 'fundsWithdrawn')
    )
    transaction_nature = models.CharField(max_length=20, choices=WalletTransactionNatures)
    wallet_id = models.ForeignKey(Wallet, default=None)


class SpecialWallet(Wallet):
    name = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.name
