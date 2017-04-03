from django import forms
from appointments.models import MessageTemplate, Protocol


class AppointmentsUploadForm(forms.Form):
    file = forms.FileField()


class ProtocolForm(forms.ModelForm):
    class Meta:
        model = Protocol
        fields = '__all__'


class MessageTemplateForm(forms.ModelForm):
    class Meta:
        model = MessageTemplate
        exclude = ('content', 'content_tail')
