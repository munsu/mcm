from django import forms
from appointments.models import MessageTemplate, Protocol


class AppointmentsUploadForm(forms.Form):
    file = forms.FileField()


class ProtocolForm(forms.ModelForm):
    class Meta:
        model = Protocol
        fields = '__all__'


class MessageTemplateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(MessageTemplateForm, self).__init__(*args, **kwargs)
        self.fields['protocol'].widget = forms.HiddenInput()

    class Meta:
        model = MessageTemplate
        exclude = ('content', 'content_tail')


class UpdateMessageTemplateForm(MessageTemplateForm):
    delete = forms.BooleanField(
        required=False,
        initial=False,
        help_text='Check this to delete this object'
    )
