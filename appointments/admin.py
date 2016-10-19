from django.contrib import admin
from .models import (
    Client, UserProfile, Appointment, Patient, Protocol, MessageTemplate, Message
)


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


class MessageTemplateInline(admin.StackedInline):
    model = MessageTemplate
    extra = 1


class ProtocolAdmin(admin.ModelAdmin):
    inlines = [
        MessageTemplateInline
    ]

admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(Client, ClientAdmin)
admin.site.register(Patient, PatientAdmin)
admin.site.register(Protocol, ProtocolAdmin)
