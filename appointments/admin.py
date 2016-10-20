from django.contrib import admin
from .models import (
    Client, UserProfile, Appointment, Patient, Protocol, MessageTemplate, Message,
    MessageAction, Reply
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


class MessageActionInline(admin.StackedInline):
    model = MessageAction
    extra = 1


class MessageTemplateAdmin(admin.ModelAdmin):
    inlines = [
        MessageActionInline
    ]


class MessageTemplateInline(admin.StackedInline):
    model = MessageTemplate
    extra = 1


class ProtocolAdmin(admin.ModelAdmin):
    inlines = [
        MessageTemplateInline
    ]


class ReplyInline(admin.StackedInline):
    model = Reply
    extra = 0


class MessageAdmin(admin.ModelAdmin):
    inlines = [
        ReplyInline
    ]

admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(Client, ClientAdmin)
admin.site.register(Patient, PatientAdmin)
admin.site.register(Protocol, ProtocolAdmin)
admin.site.register(MessageTemplate, MessageTemplateAdmin)
admin.site.register(Message, MessageAdmin)
