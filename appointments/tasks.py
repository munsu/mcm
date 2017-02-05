from __future__ import absolute_import

import logging
from celery import shared_task
from django.conf import settings
from django.utils import timezone
from twilio.rest import TwilioRestClient


from .models import Appointment, MessageTemplate, Message


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
def tw_send_sms(**kwargs):
    """Helper for sending SMS. Returns SID."""
    message = client.messages.create(**kwargs)
    return message.sid


@shared_task
def tw_send_call(**kwargs):
    """Helper for calling. Returns SID."""
    call = client.calls.create(**kwargs)
    return call.sid


@shared_task
def deliver_message(appointment_message_id):
    """
    first one is called with eta
    get protocol and template from appointment
    """
    try:
        appointment_message = Message.objects.get(id=appointment_message_id)
        appointment = appointment_message.appointment
    except (Appointment.DoesNotExist,
            Message.DoesNotExist):
        return {'status': 'Message or Appointment deleted.'}
    if not appointment.should_receive_messages():
        # stop
        appointment_message.cancel_send()
        return {'status': 'Patient cancelled.', 'next': None}
    # check time
    logger.info("times:\t{}\t{}".format(timezone.now(), appointment_message.scheduled_delivery_datetime))
    # if timezone.now() < appointment_message.scheduled_delivery_datetime:
    #     # don't send/ skip message
    #     logger.info("skipping message")
    #     pass
    # else:
    send_status = appointment_message.send()
    next_status = appointment.schedule_next_message()
    return {'status': {'message_sid': send_status}, 'next': {'task_id': next_status}}
