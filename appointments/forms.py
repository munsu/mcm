from django import forms

class AppointmentsUploadForm(forms.Form):
    file = forms.FileField()
