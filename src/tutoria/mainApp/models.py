from django.db import models


# Create your models here.

class User(models.Model):
    name = models.CharField(max_length=200)
    avatar = models.ImageField()
    email = models.EmailField(max_length=254)
    password = models.CharField(max_length=200)

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
    rate = models.PositiveIntegerField()
    rating = models.FloatField()
    isPrivate = models.BooleanField()

    def __str__(self):
        return self.user.name
