from django.db import models, transaction


# Create your models here.

class User(models.Model):
    name = models.CharField(max_length=200)
    avatar = models.ImageField(upload_to='avatar')
    email = models.EmailField(max_length=254)
    password = models.CharField(max_length=200)

    @transaction.atomic
    def save(self, *args, **kwargs):
        super(User, self).save(*args, **kwargs)
        if not Wallet.objects.filter(user=self).exists():
            w = Wallet(balance=0, user=self)
            w.save()

    # def make_wallet(self):
    #     w = Wallet(balance=0, user=self)
    #     w.save()

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

    @transaction.atomic
    def save(self, *args, **kwargs):
        super(Tutor, self).save(*args, **kwargs)
        if not PrivateTimetable.objects.filter(tutor=self).exists():
            ttmon = PrivateTimetable(tutor=self, day='Mon')
            ttmon.save()
            tttue = PrivateTimetable(tutor=self, day='Tue')
            tttue.save()
            ttwed = PrivateTimetable(tutor=self, day='Wed')
            ttwed.save()
            ttthu = PrivateTimetable(tutor=self, day='Thu')
            ttthu.save()
            ttfri = PrivateTimetable(tutor=self, day='Fri')
            ttfri.save()
            ttsat = PrivateTimetable(tutor=self, day='Sat')
            ttsat.save()
            ttsun = PrivateTimetable(tutor=self, day='Sun')
            ttsun.save()

    def __str__(self):
        return self.user.name


class PrivateTimetable(models.Model):
    tutor = models.ForeignKey(Tutor, on_delete=models.CASCADE)
    day = models.CharField(max_length=3)
    t07_08 = models.PositiveIntegerField(default=1)
    t08_09 = models.PositiveIntegerField(default=1)
    t09_10 = models.PositiveIntegerField(default=1)
    t10_11 = models.PositiveIntegerField(default=1)
    t11_12 = models.PositiveIntegerField(default=1)
    t12_13 = models.PositiveIntegerField(default=1)
    t13_14 = models.PositiveIntegerField(default=1)
    t14_15 = models.PositiveIntegerField(default=1)

    def __str__(self):
        return self.tutor.user.name



class Wallet(models.Model):
    balance = models.PositiveIntegerField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def add_funds(self, amount):
        self.balance += amount
        self.save()

    def subtract_funds(self, amount):
        self.balance -= amount
        self.save()

    def __str__(self):
        return self.user.name
