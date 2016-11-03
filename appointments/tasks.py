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
def deliver_message(appointment_message_id):
    """
    first one is called with eta
    get protocol and template from appointment
    """
    try:
        appointment_message = Message.objects.get(id=appointment_message_id)
        appointment = appointment_message.appointment
        message_template = appointment_message.template
        # appointment = Appointment.objects.get(id=appointment_id)
        # message_template = MessageTemplate.objects.get(id=message_template_id)
    except (Appointment.DoesNotExist,
            MessageTemplate.DoesNotExist,
            Message.DoesNotExist):
        return
    if not appointment.should_receive_messages():
        # stop
        return
    # appointment_message = appointment.messages.create(template=message_template)
    # check time
    if timezone.now() < appointment_message.scheduled_delivery_datetime:
        # don't send/ skip message
        logger.info("skipping message")
        pass
    else:
        logger.info("sending message")
        message = client.messages.create(
            body=message_template.content.format(**appointment.get_data()),
            to=appointment_message.recipient.patient_phone,
            from_=settings.TWILIO_NUMBER,
            # Add callback to the thing
        )
        appointment_message.twilio_status = 'delivered'
        appointment_message.save()
        logger.info(message.sid)
        # TODO set a field in appointment_message as id from twilio
    appointment.schedule_next_message()
    # next_message = appointment.get_next_template()
    # deliver_message.apply_async((appointment_id, next_message.id), eta=TODOtime)
    pass
    """
    
        appointment_time = arrow.get(self.time, self.time_zone.zone)
        reminder_time = appointment_time.replace(minutes=-settings.REMINDER_TIME)

        # Schedule the Celery task
        from .tasks import send_sms_reminder
        result = send_sms_reminder.apply_async((self.pk,), eta=reminder_time)

        return result.id
    """