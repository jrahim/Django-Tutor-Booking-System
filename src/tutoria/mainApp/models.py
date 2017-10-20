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
        w = Wallet(balance = 0, user = self)
        w.save()

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
    rate = models.PositiveIntegerField()
    rating = models.FloatField()
    isPrivate = models.BooleanField()

    def __str__(self):
        return self.user.name



class PrivateTimetable(models.Model):

    tutor = models.ForeignKey(Tutor, on_delete=models.CASCADE)
    day = models.CharField(max_length=5)
    t07_08 = models.PositiveIntegerField()
    t08_09 = models.PositiveIntegerField()
    t09_10 = models.PositiveIntegerField()
    t10_11 = models.PositiveIntegerField()
    t11_12 = models.PositiveIntegerField()
    t12_13 = models.PositiveIntegerField()
    t13_14 = models.PositiveIntegerField()
    t14_15 = models.PositiveIntegerField()


    def __str__(self):
        return self.tutor.user.name

class Wallet(models.Model):

    balance = models.PositiveIntegerField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.name

