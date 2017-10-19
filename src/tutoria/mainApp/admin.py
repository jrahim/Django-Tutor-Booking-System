from django.contrib import admin

# Register your models here.

from .models import Tutor, User, Course

admin.site.register(Tutor)
admin.site.register(User)
admin.site.register(Course)