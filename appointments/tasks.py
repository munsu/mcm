from __future__ import absolute_import

from celery import shared_task
from django.conf import settings
from twilio.rest import TwilioRestClient


from .models import Appointment


# Uses credentials from the TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN
# environment variables
client = TwilioRestClient(settings.TWILIO_SID, settings.TWILIO_TOKEN)


@shared_task
def send_sms(body, to='+16095322026'):
    """Send a reminder to a phone using Twilio SMS"""
    message = client.messages.create(
        body=body,
        to=to,
        from_=settings.TWILIO_NUMBER,
    )
    print message.sid
