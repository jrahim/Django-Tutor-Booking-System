from django.contrib import admin

# Register your models here.

from .models import Tutor, User, Course, PrivateTimetable

admin.site.register(Tutor)
admin.site.register(User)
admin.site.register(Course)
admin.site.register(PrivateTimetable)
