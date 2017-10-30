from django.db import models


# Create your models here.

class User(models.Model):
    name = models.CharField(max_length=200)
    avatar = models.ImageField(upload_to='avatar')
    email = models.EmailField(max_length=254)
    password = models.CharField(max_length=200)
    contact = models.CharField(max_length=20)
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

    def become_tutor(self, short_bio, rate, rating, is_private):
        t = Tutor(user=self, shortBio=short_bio, rate=rate, rating=rating,
                  isPrivate=is_private)  # what to do about course
        t.save()
        return t

    def get_upcoming_bookings(self):
        if Student.objects.filter(user=self).exists():
            s = Student.objects.get(user=self)
            return BookedSlot.objects.get(student=s)
        elif Tutor.objects.filter(user=self).exists():
            t = Tutor.objects.filter(user=self)
            return BookedSlot.objects.get(tutor=t)

    def __str__(self):
        return self.name


class Course(models.Model):
    code = models.CharField(max_length=50)
    title = models.CharField(max_length=200)

    def __str__(self):
        return self.title


class Tutor(models.Model):
    # user = models.ForeignKey(User, on_delete=models.CASCADE)
    user = models.OneToOneField(User)
    course = models.ManyToManyField(Course)
    shortBio = models.CharField(max_length=300)
    rate = models.PositiveIntegerField(default=0)
    rating = models.FloatField(default=0)
    isPrivate = models.BooleanField()

    def create_unavailable_slot(self, day, time_start, duration):
        unavailable = UnavailableSlot(tutor=self, day=day, time_start=time_start, duration=duration)
        unavailable.save()

    # @transaction.atomic
    # def save(self, *args, **kwargs):
    #     super(Tutor, self).save(*args, **kwargs)
    #     if not PrivateTimetable.objects.filter(tutor=self).exists():
    #         ttmon = PrivateTimetable(tutor=self, day='Mon')
    #         ttmon.save()
    #         tttue = PrivateTimetable(tutor=self, day='Tue')
    #         tttue.save()
    #         ttwed = PrivateTimetable(tutor=self, day='Wed')
    #         ttwed.save()
    #         ttthu = PrivateTimetable(tutor=self, day='Thu')
    #         ttthu.save()
    #         ttfri = PrivateTimetable(tutor=self, day='Fri')
    #         ttfri.save()
    #         ttsat = PrivateTimetable(tutor=self, day='Sat')
    #         ttsat.save()
    #         ttsun = PrivateTimetable(tutor=self, day='Sun')
    #         ttsun.save()

    def __str__(self):
        return self.user.name


# class PrivateTimetable(models.Model):
#     tutor = models.ForeignKey(Tutor, on_delete=models.CASCADE)
#     day = models.CharField(max_length=3)
#     t07_08 = models.PositiveIntegerField(default=1)
#     t08_09 = models.PositiveIntegerField(default=1)
#     t09_10 = models.PositiveIntegerField(default=1)
#     t10_11 = models.PositiveIntegerField(default=1)
#     t11_12 = models.PositiveIntegerField(default=1)
#     t12_13 = models.PositiveIntegerField(default=1)
#     t13_14 = models.PositiveIntegerField(default=1)
#     t14_15 = models.PositiveIntegerField(default=1)
#
#     def __str__(self):
#         return self.tutor.user.name
#

class Student(models.Model):
    user = models.OneToOneField(User)

    def create_booking(self, date, time_start, duration, tutor):
        booking = BookedSlot(date=date, time_start=time_start, duration=duration, tutor=tutor, student=self,
                             status="BOOKED")
        booking.save()

    def __str__(self):
        return self.user.name


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
        return self.user.name


class BookedSlot(models.Model):
    date = models.DateTimeField()
    time_start = models.TimeField()
    duration = models.TimeField()  # time or integer?
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
        self.save()

    def __str__(self):
        return self.student.user.name + self.tutor.user.name


class UnavailableSlot(models.Model):
    tutor = models.ForeignKey(Tutor, on_delete=models.CASCADE)
    day = models.DateField()  # type??
    time_start = models.TimeField()
    duration = models.TimeField()  # time or integer?

    # modify/delete unavailable slot?
