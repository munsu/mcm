from django.contrib import admin
from modeltranslation.admin import TranslationAdmin
from .models import (
    Client, UserProfile, Appointment, Patient, Protocol, MessageTemplate, Message,
    MessageAction, MessageLog, Reply, Constraint, Facility, Provider, DayAfterAppointment
)


class UserProfileAdmin(admin.ModelAdmin):
    pass


class FacilityInline(admin.StackedInline):
    model = Facility
    extra = 1


class ProviderInline(admin.StackedInline):
    model = Provider
    extra = 1


class ClientAdmin(admin.ModelAdmin):
    inlines = [
        FacilityInline,
        ProviderInline,
    ]


class AppointmentInline(admin.StackedInline):
    model = Appointment
    extra = 0


class DayAfterAppointmentInline(admin.StackedInline):
    model = DayAfterAppointment
    extra = 0


class PatientAdmin(admin.ModelAdmin):
    """
    display details.
    """
    list_display = (
        '__str__', 'patient_home_phone', 'patient_mobile_phone', 'patient_email_address'
    )
    inlines = [
        AppointmentInline,
    ]


class AppointmentAdmin(admin.ModelAdmin):
    inlines = [
        DayAfterAppointmentInline,
    ]

    def get_form(self, request, obj=None, **kwargs):
        form = super(AppointmentAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields['appointment_provider'].queryset = Provider.objects.filter(client=obj.client)
        form.base_fields['appointment_facility'].queryset = Facility.objects.filter(client=obj.client)
        return form


class MessageLogAdmin(admin.ModelAdmin):
    pass


class MessageActionInline(admin.StackedInline):
    model = MessageAction
    extra = 1


class MessageTemplateAdmin(TranslationAdmin):
    list_display = (
        'protocol',
        'message_type',
        'daydelta',
        'time'
    )
    inlines = [
        MessageActionInline
    ]


class MessageTemplateInline(admin.StackedInline):
    model = MessageTemplate
    extra = 1


class ConstraintInline(admin.TabularInline):
    model = Constraint
    readonly_fields = ('id',)
    fields = ('id', 'field', 'lookup_type', 'value')
    extra = 1


class ProtocolAdmin(admin.ModelAdmin):
    inlines = [
        ConstraintInline, MessageTemplateInline
    ]


class ReplyInline(admin.StackedInline):
    model = Reply
    extra = 0


class MessageAdmin(admin.ModelAdmin):
    inlines = [
        ReplyInline
    ]
    readonly_fields = ('created', 'modified')

admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(Client, ClientAdmin)
admin.site.register(Patient, PatientAdmin)
admin.site.register(Protocol, ProtocolAdmin)
admin.site.register(MessageTemplate, MessageTemplateAdmin)
admin.site.register(Message, MessageAdmin)
admin.site.register(MessageLog, MessageLogAdmin)
admin.site.register(Appointment, AppointmentAdmin)
