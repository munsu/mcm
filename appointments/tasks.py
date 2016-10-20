from __future__ import absolute_import

import logging
from celery import shared_task
from django.conf import settings
from twilio.rest import TwilioRestClient


from .models import Appointment


logger = logging.getLogger(__name__)

# Uses credentials from the TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN
# environment variables
client = TwilioRestClient(settings.TWILIO_SID, settings.TWILIO_TOKEN)


@shared_task
def send_sms(body, to='+16095322026'):
    """Send a reminder to a phone using Twilio SMS"""
    # Get appointment
    # Check date and time
    # Check if cancelled
    # Check status of appointment
    message = client.messages.create(
        body=body,
        to=to,
        from_=settings.TWILIO_NUMBER,
        # Add callback to the thing
    )
    print message.sid
    # Update Message with sid

@shared_task
def deliver_message(appointment_id):
    pass