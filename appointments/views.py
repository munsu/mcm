from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse
from .tasks import send_sms


# Create your views here.
def send_sms_view(request):
    if request.method == "POST":
        body = request.POST.get('body')
        to = request.POST.get('phone')
        print "MSG REQ", body, to
        print send_sms(body, to)
    return HttpResponseRedirect(reverse('home'))

# Create Appointment viewset