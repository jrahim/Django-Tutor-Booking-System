from django.contrib import admin

# Register your models here.

from . import models

admin.site.register(models.Tutor)
admin.site.register(models.User)
admin.site.register(models.Course)
admin.site.register(models.Wallet)
admin.site.register(models.BookedSlot)
admin.site.register(models.UnavailableSlot)
admin.site.register(models.Student)
admin.site.register(models.University)
admin.site.register(models.Tag)


admin.site.register(models.Transaction)
admin.site.register(models.SpecialWallet)
admin.site.register(models.SessionTransaction)
admin.site.register(models.WalletTransaction)
admin.site.register(models.PrivateTutor)
admin.site.register(models.ContractedTutor)
admin.site.register(models.PasswordToken)
admin.site.register(models.Review)
admin.site.register(models.Admin)