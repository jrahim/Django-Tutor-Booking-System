from datetime import date, datetime, timedelta

from django.db import models
from django.db.models import Avg
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
            return transaction
        self.save()

    def subtract_funds(self, amount, isWalletManagement=False):
        self.balance -= amount
        if isWalletManagement:
            user = User.objects.get(wallet=self)
            transaction = WalletTransaction(user=user, amount=amount, date=date.today(), time=datetime.now().time(),
                                            transaction_nature="FUNDSWITHDRAWN", wallet_id=self)
            transaction.save()
            self.save()
            return transaction
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
    # university = models.ManyToManyField(University, blank=True)
    isActivated = models.BooleanField(default=True)

    def create_unavailable_slot(self, date, time_start):
        pass

    def remove_unavailable_slot(self, date, time_start):
        UnavailableSlot.objects.get(tutor=self, date=date, time_start=time_start).delete()

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

    def add_tag(self, tagName, create):
        if create:
        	
            t = Tag(tag_name=tagName)
            t.save()

        t2 = Tag.objects.get(tag_name=tagName)
        self.subject_tags.add(t2)
        self.save()

    def remove_tag(self, tagName):
        t = Tag.objects.get(tag_name=tagName)
        self.subject_tags.remove(t)
        self.save()

    def update_rating(self):

        newRating = Review.objects.filter(tutor=self).aggregate(Avg('rating'))
        print(newRating)
        setattr(self, 'rating', newRating['rating__avg'])

        self.save()

    def __str__(self):
        return self.user.name


class PrivateTutor(Tutor):
    rate = models.PositiveIntegerField()

    def __str__(self):
        return self.user.name

    def create_unavailable_slot(self, date, time_start):
        unavailable = UnavailableSlot(tutor=self, date=date, time_start=time_start, duration=1.0)
        unavailable.save()


class ContractedTutor(Tutor):
    def __str__(self):
        return self.user.name

    def create_unavailable_slot(self, date, time_start):
        unavailable = UnavailableSlot(tutor=self, date=date, time_start=time_start, duration=0.5)
        unavailable.save()


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
            if isinstance(self.tutor, PrivateTutor):
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
    # day = models.CharField(max_length=3)
    date = models.DateField()
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


class PasswordToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=200)

    def __str__(self):
        return self.user.name


class Review(models.Model):
    tutor = models.ForeignKey(Tutor, on_delete=models.CASCADE)
    content = models.CharField(max_length=400)
    rating = models.PositiveIntegerField()
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    booking = models.OneToOneField(BookedSlot, on_delete=models.CASCADE)

    TYPES = (
        ('ANONYMOUS', 'anonymous'),
        ('NONANONYMOUS', 'nonanonymous'),

    )
    reviewtype = models.CharField(max_length=9, choices=TYPES)


class Admin(models.Model):
    user_name = models.CharField(max_length=20)
    password = models.CharField(max_length=20)