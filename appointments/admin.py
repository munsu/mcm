from django.contrib import admin
from .models import Client, UserProfile, Appointment, Patient


class UserProfileAdmin(admin.ModelAdmin):
    pass


class ClientAdmin(admin.ModelAdmin):
    pass


class AppointmentInline(admin.StackedInline):
    model = Appointment
    extra = 0

class PatientAdmin(admin.ModelAdmin):
    inlines = [
        AppointmentInline,
    ]

admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(Client, ClientAdmin)
admin.site.register(Patient, PatientAdmin)
