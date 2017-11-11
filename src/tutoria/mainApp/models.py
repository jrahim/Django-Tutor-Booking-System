from django.core import mail
from django.db import models
from django.db.models import Q


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
    # user = models.ForeignKey(User, on_delete=models.CASCADE)
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

    def create_booking(self, date, time_start, duration, tutor, charges):
        booking = BookedSlot(date=date, time_start=time_start, duration=duration, tutor=tutor, student=self,
                             status="BOOKED")
        booking.save()
        self.user.wallet.subtract_funds(int(charges))
        return booking

    def __str__(self):
        return self.user.name


class BookedSlot(models.Model):
    date = models.DateField()
    time_start = models.TimeField()
    duration = models.FloatField()  # time or integer?
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
    day = models.CharField(max_length=3)
    time_start = models.TimeField()
    duration = models.FloatField()
