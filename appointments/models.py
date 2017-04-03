from __future__ import unicode_literals

import logging
import pytz
import string

from django.contrib.postgres.fields import JSONField
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.forms.models import model_to_dict
from django.urls import reverse
from django.utils import timezone

from model_utils import Choices
from model_utils.models import TimeStampedModel

from mcm import celery_app
from .utils import flatten_dict, language


logger = logging.getLogger(__name__)
"""
APPOINTMENTS FILE LAYOUT
field name              logical name                    type        preferred format    description
appointment_facility    facility name                   required    string  facility at which this appointment is scheduled or occured; required for organizations submitting data for more than one facility
appointment_number      appointment or procedure number required    string  uniquely identifies an appointment or procedure within the health system
account_number          patient account identifier      required    string  unique identifier assigned by the provider patient accounting system (pas) when a patient is admitted or seen for services
patient_first_name      patient first name              required    string  patient first name as in the clinical system
patient_last_name       patient last name               required    string  patient last name as in the clinical system
appointment_provider    primary provider, surgeon       required    string  the primary care provider or surgeon of record for this appointment
appointment_scheduled_service   service                 required    string  service under which the appointment is scheduled (e.g., orthopedics, ent, open heart, etc.)
appointment_status      actual appointment status       required    string  status of the appointment - only scheduled appointments should be collected here.
patient_type            patient type                    required    string  inpatient - surgery admit / outpatient status of patient
procedure_description   scheduled procedure description required    string  what is the primary procedure patient is scheduled for - provide base procedure
scheduled_room          scheduled operating room or procedure room  required    string  procedure, operating or exam room into which this case or appointment was scheduled
scheduled_duration      scheduled procedure duration    required    string  how long procedure, operation or appointment scheduled to last for
appointment_date        appointment or procedure date   required    yyyy-mm-dd hh:mm:ss date of appointment.  the daily upload should include t+1 through t+8
appointment_scheduled_dt    date appointment was scheduled  required    yyyy-mm-dd hh:mm:ss date on which the scheduler added the appointment to the schedule (e.g., the date that the surgeon's office called have the case put on the or schedule)
provider_specialty      surgeon specialty               optional    string  specialty of the primary provider or surgeon on the appointment or case
appointment_type        appointment or case type        optional    string  type of case (e.g., urgent, emergent, elective, etc.) or type of appointment (new visit, follow-up, etc.)
appointment_class       appointment or case class       optional    string  classification of the case (e.g., day surgery, same day admit, inpatient, etc.) or appointment (outpatient, procedure, inpatient consult etc.)
asa_rating              asa rating                      optional    string  the american society of anesthesiologists acuity rating for this patient
modified_procedure_description  modified or updated procedure desc  optional    string  what is the modified procedure description
asa_cd                  asa code                        optional    string  code associated with the american society of anesthesiologists acuity rating for this patient
provider_id             physician id                    optional    string  employee number for the primary surgeon. must match to physician id in patient accounting system.
provider_npi_id         physician npi id                optional    string  national provider identification for the primary provider.
patient_mrn             medical record number           desired     string  unique identifier assigned to an individual patient used to associate clinical records from one or more encounters
patient_home_phone      patient home phone number       desired     string  patient home phone number as recorded on the system. if unavailable, leave blank
patient_mobile_phone    patient cell or mobile phone number desired string  patient cell or mobile phone number as recorded on the system. if unavailable, leave blank
patient_email_address   patient email address           desired     string  patient email address as recorded on the system. if unavailable, leave blank
"""


# Create your models here.
class UserProfile(models.Model):
    """
    Auth User extension
    """
    user = models.OneToOneField('auth.User', related_name='profile')
    client = models.ForeignKey('Client', null=True, blank=True)


class Client(models.Model):
    """
    For multi tenancy
    timezone
    yyyy-mm-dd hh:mm am/pm
    nov, dd, 2016
    TODO datetime_format
    YYYY-MM-DDTHH:MM:SS+HH:MM
    """
    TIMEZONE_CHOICES = zip(pytz.all_timezones, pytz.all_timezones)
    DATETIME_FORMAT_CHOICES = (
        # '%d/%m/%y',
        ('%d %b %Y %I:%M%p', '25 Oct 2006 02:30PM'),
        ('%b %d, %Y %I:%M%p', 'Oct 25, 2006 02:30PM'),
        ('%B %d, %Y %I:%M%p', 'October 25, 2006 02:30PM'),
        ('%m/%d/%Y %I:%M%p', '10/25/2006 02:30PM'),
        ('%Y-%m-%d %H:%M', '2006-10-25 14:30'),
        ('%Y-%m-%d', '2006-10-25'),
        ('%m/%d/%Y %H:%M', '10/25/2006 14:30'),
        ('%m/%d/%Y', '10/25/2006'),
        ('%m/%d/%y %H:%M', '10/25/06 14:30'),
        ('%m/%d/%y', '10/25/06'),
    )
    name = models.CharField(max_length=255)
    active = models.BooleanField(default=True)
    datetime_format = models.CharField(
        max_length=32, default='%m/%d/%Y %I:%M%p',choices=DATETIME_FORMAT_CHOICES)
    timezone = models.CharField(
        max_length=64, default='America/New_York', choices=TIMEZONE_CHOICES)
    address = models.TextField()
    # we want this to unique to each client eventually.
    twilio_number = models.CharField(max_length=16, default='+15702343621')
    office_hours = models.TextField()
    contact_details = models.TextField()

    def __str__(self):
        return self.name


class Facility(models.Model):
    """
    Where patients are appointed to.
    """
    client = models.ForeignKey('Client', models.PROTECT)
    name = models.CharField(max_length=255)
    # TODO shortform for sms?
    address = models.CharField(max_length=255, null=True, blank=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True)

    class Meta:
        verbose_name_plural = 'facilities'
        unique_together = ('client', 'name')

    def __str__(self):
        return self.name


class Provider(models.Model):
    client = models.ForeignKey('Client', models.PROTECT)
    name = models.CharField(max_length=128)
    provider_id = models.CharField(max_length=64, null=True, blank=True)  #            physician id                    optional    string  employee number for the primary surgeon. must match to physician id in patient accounting system.
    provider_npi_id = models.CharField(max_length=64)  #        physician npi id                optional    string  national provider identification for the primary provider.
    provider_specialty = models.CharField(max_length=64, null=True, blank=True)  #   surgeon specialty               optional    string  specialty of the primary provider or surgeon on the appointment or case
    office_hours = models.TextField(null=True, blank=True)
    contact_details = models.TextField(null=True, blank=True)

    @property
    def get_office_hours(self):
        return self.office_hours or self.client.office_hours

    @property
    def get_contact_details(self):
        return self.contact_details or self.client.contact_details

    class Meta:
        unique_together = ('client', 'provider_npi_id')

    def __str__(self):
        return self.name


class Constraint(models.Model):
    LOOKUP_TYPE_CHOICES = (
        ('exact', 'exact'),
        ('iexact', 'Case-insensitive exact'),
        ('contains', 'contains'),
        ('icontains', 'Case-insensitive contains'),
        ('regex', 'Regex'),
        ('iregex', 'Case-insensitive regex'),
    )
    FIELD_CHOICES = (
        ('procedure_description', 'procedure_description'),
        ('appointment_scheduled_service', 'appointment_scheduled_service'),
    )
    OPERATOR_TYPE_CHOICES = (
        ('and', 'and'),
        ('or', 'or'),
    )
    protocol = models.ForeignKey(
        'Protocol', models.CASCADE, related_name='constraints')
    field = models.CharField(max_length=32, choices=FIELD_CHOICES)
    lookup_type = models.CharField(max_length=32, choices=LOOKUP_TYPE_CHOICES)
    value = models.CharField(max_length=255)

    def as_q_str(self):
        return "Q({}__{}='{}')".format(self.field, self.lookup_type, self.value)


class Protocol(models.Model):
    """
    has message templates, message actions
    RULE:
    {
        "and": {
            "key__type": "value",
            "or": {
                "key__type": "value"
            }
        }
    }
    "{} & {} | ({})"
    """
    ALLOWED_CHARS = string.digits + ' ()|&$~\{\}'
    name = models.CharField(max_length=64)
    clients = models.ManyToManyField('Client', related_name='protocols')
    priority = models.IntegerField()
    # rule = JSONField()
    constraint_relationship = models.CharField(
        help_text=("Please use {$constraint_id} for Constraint, & for AND, "
                   "| for OR, ~ for NOT, and () for grouping. Sample: "
                   "{$1} & ~({$2} | {$3})."), blank=True, max_length=255)

    def eval_constraints(self):
        try:
            return eval(self.constraint_relationship.format(**self.constraints_dict()))
        except SyntaxError:
            # When constraint_relationship is blank
            return Q()

    def constraints_dict(self):
        return {'$' + str(c.id): c.as_q_str() for c in self.constraints.all()}

    def get_absolute_url(self):
        return reverse("protocols:detail", args=[self.pk])

    def __str__(self):
        return self.name

    def clean(self):
        for c in self.constraint_relationship:
            if c not in self.ALLOWED_CHARS:
                raise ValidationError('Invalid characters on `constraint_relationship`.')


class MessageTemplate(models.Model):
    """
    Template for Mobile Terminating (MT) Messages
    """
    MESSAGE_TYPES = (
        ('email', 'Email Message'),  # use email_address field
        ('text', 'Text Message'),  # use mobile_phone field
        ('call', 'Phone Call'),  # use home_phone or mobile_phone field
    )
    created_datetime = models.DateTimeField(auto_now_add=True)
    message_type = models.CharField(max_length=255, choices=MESSAGE_TYPES)  # TODO
    content = models.TextField()  # sms
    content_tail = models.TextField(blank=True)
    daydelta = models.DurationField()  # TODO order is separate field
    time = models.TimeField()  # TODO widget for this should be choices
    protocol = models.ForeignKey('Protocol', models.CASCADE, related_name='templates')

    @property
    def message_body(self):
        return "{}\n{}".format(self.content.strip(), self.content_tail.strip())

    @property
    def message_tail(self):
        return self.content_tail.strip()

    def clean(self):
        try:
            # Archaic. Fails if there are no Appointments yet. TODO this better.
            print self.message_body.format(**Appointment.objects.last().get_data())
        except KeyError, e:
            raise ValidationError('Invalid variable: {}'.format(str(e)))
        except Exception, e:
            print e
            pass

    def __str__(self):
        return "{} - {} {} - {}".format(self.message_type, self.daydelta, self.time, self.protocol)


class MessageLog(TimeStampedModel):
    SENDER_CHOICES = (
        ('client', 'Client'),
        ('patient', 'Patient'),
        ('system', 'System')
    )
    appointment = models.ForeignKey('Appointment', models.CASCADE, related_name='messages_log')
    sender = models.CharField(max_length=7, choices=SENDER_CHOICES)
    body = models.TextField()

    class Meta:
        ordering = ['created', ]

    def __str__(self):
        return "[{}] {}: {}".format(self.appointment, self.sender, self.body)


class MessageAction(models.Model):
    ACTION = Choices(
        ('confirm', 'Confirm Appointment'),
        ('stop', 'Stop Sending Further Messages'),  # TODO not sure if this equates to cancelled
        ('reschedule', 'Reschedule Appointment'),
        ('cancel', 'Cancel Appointment'),
        ('lang', 'Change Patient Preferred Language')
    )
    LANG = Choices(
        ('en', 'English'),
        ('es', 'Spanish')
    )
    template = models.ForeignKey('MessageTemplate', models.CASCADE, related_name='actions')
    keyword = models.CharField(max_length=160)
    action = models.CharField(max_length=255, choices=ACTION)
    lang = models.CharField(max_length=5, choices=LANG, null=True, blank=True)
    # TODO validate this

    def __str__(self):
        return "{}: {}".format(self.keyword, self.action)



class Message(TimeStampedModel):
    """
    TODO Separate emaill???

    TWILIO ERRORS
    30001   Queue overflow  You tried to send too many messages too quickly and your message queue overflowed. Try sending your message again after waiting some time.
    30002   Account suspended   Your account was suspended between the time of message send and delivery. Please contact Twilio.
    30003   Unreachable destination handset The destination handset you are trying to reach is switched off or otherwise unavailable.
    30004   Message blocked The destination number you are trying to reach is blocked from receiving this message (e.g. due to blacklisting).
    30005   Unknown destination handset The destination number you are trying to reach is unknown and may no longer exist.
    30006   Landline or unreachable carrier The destination number is unable to receive this message. Potential reasons could include trying to reach a landline or, in the case of short codes, an unreachable carrier.
    30007   Carrier violation   Your message was flagged as objectionable by the carrier. In order to protect their subscribers, many carriers have implemented content or spam filtering. Learn more about carrier filtering
    30008   Unknown error   The error does not fit into any of the above categories.
    30009   Missing segment One or more segments associated with your multi-part inbound message was not received.
    30010   Message price exceeds max price.    The price of your message exceeds the max price parameter.

    TWILIO STATUS
    accepted    Twilio has received your API request to send a message with a Messaging Service and a From number is being dynamically selected. This is still the initial status when sending with a Messaging Service and the From parameter.
    queued  The API request to send a message was successful and the message is queued to be sent out. This is the initial status when you are not using a Messaging Service.
    sending Twilio is in the process of dispatching your message to the nearest upstream carrier in the network.
    sent    The message was successfully accepted by the nearest upstream carrier.
    receiving   The inbound message has been received by Twilio and is currently being processed.
    received    On inbound messages only. The inbound message was received by one of your Twilio numbers.
    delivered   Twilio has received confirmation of message delivery from the upstream carrier, and, where available, the destination handset.
    undelivered Twilio has received a delivery receipt indicating that the message was not delivered. This can happen for a number of reasons including carrier content filtering, availability of the destination handset, etc.
    failed  The message could not be sent. This can happen for various reasons including queue overflows, account suspensions and media errors (in the case of MMS). Twilio does not charge you for failed messages.
    """
    TWILIO_STATUS = Choices(
        ('queued', 'Queued'),
        ('failed', 'Failed'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('undelivered', 'Undelivered'),
    )
    TWILIO_ERROR_CHOICES = (
        ('30001', 'Queue overflow'),
        ('30002', 'Account suspended'),
        ('30003', 'Unreachable destination'),
        ('30004', 'Message blocked'),
        ('30005', 'Unknown destination handset'),
        ('30006', 'Landline or unreachable carrier'),
        ('30007', 'Carrier violation'),
        ('30008', 'Unknown error'),
        ('30009', 'Missing segment'),
        ('30010', 'Message price exceeds max price'),
    )
    template = models.ForeignKey('MessageTemplate', models.CASCADE)
    appointment = models.ForeignKey(
        'Appointment', models.CASCADE, related_name='messages')
    for_appointment_date = models.DateTimeField()
    twilio_status = models.CharField(
        max_length=64, blank=True, null=True, choices=TWILIO_STATUS)
    twilio_error = models.CharField(
        max_length=64, blank=True, null=True, choices=TWILIO_ERROR_CHOICES)
    message_sid =  models.CharField(
        max_length=64, blank=True, null=True)
    task_id = models.CharField(
        max_length=64, blank= True, null=True)

    class Meta:
        ordering = ['created', ]

    @property
    def recipient(self):
        return self.appointment.patient

    @property
    def scheduled_delivery_datetime(self):
        ddate = self.appointment.local_appointment_date + self.template.daydelta
        dtime = self.template.time
        return ddate.replace(
            hour=dtime.hour, minute=dtime.minute,
            second=dtime.second, microsecond=dtime.microsecond)

    @property
    def body(self):
        with language(self.appointment.patient.lang):
            return self.template.message_body.format(**self.appointment.get_data())

    @property
    def tail(self):
        with language(self.appointment.patient.lang):
            return self.template.message_tail.format(**self.appointment.get_data())

    def get_voice_url(self):
        """
        1 - confirm
        2 - cancel -> 1 - reschedule ()
        0 - repeat
        """
        return 'http://mcm.komadori.xyz{}'.format(
            reverse('twilio-voice-detail', args=[self.id]))

    def send(self):
        """
        Should not be called directly. Will not schedule the next message.
        """
        from .tasks import tw_send_call, tw_send_sms
        data = {
            'to': self.recipient.patient_phone,  # TODO should change for call
            'from_': self.appointment.client.twilio_number,
        }
        if self.template.message_type == 'text':
            logger.info("sending sms message")
            data['body'] = self.body
            try:
                self.message_sid = tw_send_sms(**data)  # TODO doesn't error?
                self.twilio_status = Message.TWILIO_STATUS.delivered
                self.appointment.messages_log.create(
                    sender='client',
                    body=self.body)
            except Exception, e:
                logger.warning(e)
            self.save()
        elif self.template.message_type == 'call':
            logger.info("sending voice call request")
            try:
                data['url'] = self.get_voice_url()
                self.message_sid = tw_send_call(**data)
                self.twilio_status = Message.TWILIO_STATUS.delivered
            except Exception, e:
                logger.warning(e)
            self.save()
        else:
            raise Exception("Email not yet allowed.")

        return self.message_sid

    def cancel_send(self):
        # TODO what else to put here
        self.twilio_status = Message.TWILIO_STATUS.undelivered
        self.save()

    def check_for_action(self, body):
        if self.template.message_type == 'text':
            for ma in self.template.actions.all():
                if ma.keyword.lower() == body.lower():
                    return ma
        else:
            raise Exception("Email/Call not yet parsed.")

    def __str__(self):
        return "{}: {}".format(
            self.scheduled_delivery_datetime, self.template)


class Reply(TimeStampedModel):
    """
    Mobile Originating (MO) Message

    TODO parse content for actions.
    Should actions be a separate table or hardcoded:
        OK - confirm
        STOP - stop
        RE - resched and stuff
    """
    message = models.ForeignKey('Message', models.CASCADE)
    content = models.TextField()
    message_action = models.ForeignKey('MessageAction', models.SET_NULL, null=True)

    def save(self, *args, **kwargs):
        self.message_action = self.message.check_for_action(self.content)
        super(Reply, self).save(*args, **kwargs)
        logger.info("<reply save>\tReply:{}\tAction:{}".format(self.content, self.message_action))
        if self.message_action:
            try:
                handler = getattr(self.message.appointment, self.message_action.action)
                handler(message_id=self.message.id, language=self.message_action.lang)
                # TODO call handler. somehow pass/record message.id
            except AttributeError:
                raise NotImplementedError("Missing appointment method: {}".format(self.message_action.action))
        # TODO action loop

    class Meta:
        ordering = ['created', ]

    def __str__(self):
        return self.content


class AppointmentManager(models.Manager):
    def get_confirmed(self):
        return self.get_queryset().filter_by(appointment_confirm_status='confirmed')

    def get_confirmed_by_date(self, date):
        return self.get_confirmed().filter(appointment_confirm_date__date=date)


class Appointment(models.Model):
    APPOINTMENT_TYPE_CHOICES = (
        ('urgent', 'Urgent Case'),
        ('emergent', 'Emergent Case'),
        ('elective', 'Elective Case'),
        ('new visit', 'New Visit Appointment'),
        ('follow-up', 'Follow-Up Appointment'),
    )
    APPOINTMENT_CLASS_CHOICES = (
        ('day surgery', 'Day Surgery Case'),
        ('same day admit', 'Same Day Admit Case'),
        ('inpatient', 'Inpatient Case'),
        ('outpatient', 'Outpatient Appointment'),
        ('procedure', 'Procedure Appointment'),
        ('inpatient consult', 'Inpatient Consult Appointment'),
    )
    APPOINTMENT_CONFIRM = Choices(
        ('confirmed', 'Confirmed'),
        ('unconfirmed', 'Unconfirmed'),
        ('cancelled', 'Cancelled')
    )
    PATIENT_TYPE = Choices('inpatient', 'outpatient')
    client = models.ForeignKey('Client', models.PROTECT)
    patient = models.ForeignKey('Patient', models.PROTECT)
    protocols = models.ManyToManyField('Protocol', blank=True)
    # TODO choices
    appointment_confirm_status = models.CharField(
        max_length=64,
        default=APPOINTMENT_CONFIRM.unconfirmed,
        choices=APPOINTMENT_CONFIRM)
    appointment_confirm_date = models.DateTimeField(null=True, blank=True)

    appointment_facility = models.ForeignKey('Facility', models.PROTECT, null=True)  #    facility name                   required    string  facility at which this appointment is scheduled or occured; required for organizations submitting data for more than one facility
    # appointment_facility = models.CharField(max_length=255)  # temporary for demo
    appointment_number = models.CharField(max_length=64)  #     appointment or procedure number required    string  uniquely identifies an appointment or procedure within the health system
    appointment_provider = models.ForeignKey('Provider', models.PROTECT, null=True)  #   primary provider, surgeon       required    string  the primary care provider or surgeon of record for this appointment
    appointment_scheduled_service = models.CharField(max_length=255)  #  service                 required    string  service under which the appointment is scheduled (e.g., orthopedics, ent, open heart, etc.)
    appointment_status = models.CharField(max_length=64)  #     actual appointment status       required    string  status of the appointment - only scheduled appointments should be collected here.
    appointment_date = models.DateTimeField()  #     appointment or procedure date   required    yyyy-mm-dd hh:mm:ss date of appointment.  the daily upload should include t+1 through t+8
    appointment_scheduled_dt = models.DateTimeField()  # date appointment was scheduled  required    yyyy-mm-dd hh:mm:ss date on which the scheduler added the appointment to the schedule (e.g., the date that the surgeon's office called have the case put on the or schedule)
    # TODO Add choices
    appointment_type = models.CharField(max_length=64, null=True, blank=True)  #       appointment or case type        optional    string  type of case (e.g., urgent, emergent, elective, etc.) or type of appointment (new visit, follow-up, etc.)
    # TODO Add choices
    appointment_class = models.CharField(max_length=64, null=True, blank=True)  #      appointment or case class       optional    string  classification of the case (e.g., day surgery, same day admit, inpatient, etc.) or appointment (outpatient, procedure, inpatient consult etc.)

    procedure_description = models.CharField(max_length=255)  #  scheduled procedure description required    string  what is the primary procedure patient is scheduled for - provide base procedure
    # TODO not needed?
    # modified_procedure_description = models.CharField(max_length=255, null=True, blank=True)  # modified or updated procedure desc  optional    string  what is the modified procedure description
    scheduled_room = models.CharField(max_length=64)  #         scheduled operating room or procedure room  required    string  procedure, operating or exam room into which this case or appointment was scheduled
    # TODO or daterange or string or durationfield lol
    scheduled_duration = models.CharField(max_length=64)  #  scheduled procedure duration    required    string  how long procedure, operation or appointment scheduled to last for
    # provider_id = models.CharField(max_length=64, null=True, blank=True)  #            physician id                    optional    string  employee number for the primary surgeon. must match to physician id in patient accounting system.
    # provider_npi_id = models.CharField(max_length=64)  #        physician npi id                optional    string  national provider identification for the primary provider.

    # provider_specialty = models.CharField(max_length=64, null=True, blank=True)  #   surgeon specialty               optional    string  specialty of the primary provider or surgeon on the appointment or case

    # Patient stuff but changes per appointment
    patient_type = models.CharField(max_length=64)  #            patient type                    required    string  inpatient - surgery admit / outpatient status of patient
    asa_rating = models.CharField(max_length=64, null=True, blank=True)  #             asa rating                      optional    string  the american society of anesthesiologists acuity rating for this patient
    asa_cd = models.CharField(max_length=64, null=True, blank=True)  #                 asa code

    # misc
    notes = models.TextField(blank=True)
    objects = AppointmentManager()

    @property
    def timezone(self):
        return pytz.timezone(self.client.timezone)

    @property
    def local_appointment_date(self):
        return timezone.localtime(self.appointment_date, self.timezone)

    def get_data(self):
        # TODO just edit the field's to_repr method
        datetime_fields = (
            'appointment_date',
            'appointment_scheduled_dt',
            'appointment_confirm_date'
        )
        data = model_to_dict(self)
        for field in datetime_fields:
            try:
                data[field] = (
                    timezone
                    .localtime(data[field], self.timezone)
                    .strftime(self.client.datetime_format)
                )
            except Exception:
                pass
        data['patient'] = model_to_dict(self.patient)
        data['client'] = model_to_dict(self.client)
        data['appointment_facility'] = model_to_dict(self.appointment_facility)
        data['appointment_provider'] = model_to_dict(self.appointment_provider)
        data['protocols'] = list(self.protocols.values_list('name', flat=True))
        return flatten_dict(data)

    def should_receive_messages(self):
        """TODO set this on the patient level."""
        return self.appointment_confirm_status != self.APPOINTMENT_CONFIRM.cancelled

    def confirm(self, message_id, *args, **kwargs):
        # TODO where to put message_id reference
        self.appointment_confirm_date = timezone.now()
        self.appointment_confirm_status = self.APPOINTMENT_CONFIRM.confirmed
        self.save()
        self.messages_log.create(
            sender='system',
            body="Appointment Confirmed."
        )

    def stop(self, *args, **kwargs):
        self.appointment_confirm_status = self.APPOINTMENT_CONFIRM.cancelled
        self.save()
        self.messages_log.create(
            sender='system',
            body="Appointment Canceled."
        )

    def reschedule(self, *args, **kwargs):
        self.appointment_confirm_status = self.APPOINTMENT_CONFIRM.cancelled
        self.save()
        self.messages_log.create(
            sender='system',
            body="Appointment Canceled."
        )

    def cancel(self, *args, **kwargs):
        self.appointment_confirm_status = self.APPOINTMENT_CONFIRM.cancelled
        self.save()
        self.messages_log.create(
            sender='system',
            body="Appointment Canceled."
        )

    def lang(self, language, *args, **kwargs):
        self.patient.lang = language
        # TODO validate this
        self.patient.save()
        self.messages_log.create(
            sender='system',
            body="Preferred Language set to {}.".format(language)
        )

    def find_protocols(self):
        """
        For each protocol,
            check if appointment fits.
        """
        for protocol in self.client.protocols.all():
            if Appointment.objects.filter(protocol.eval_constraints(), id=self.id).exists():
                print "found protocol for {}: {}".format(self.id, protocol.name)
                self.protocols.add(protocol)

    def get_next_template(self, datetime=None):
        if datetime is None:
            datetime = timezone.now()
        # we have to convert this to localtime first else the daydelta becomes a pain
        # to compute
        # TODO if there's a queued message, watdo
        dday_daydelta = (
            timezone.localtime(timezone.now(), self.timezone).date()
            - self.local_appointment_date.date()
        )
        if dday_daydelta.days == 0:
            return (
                MessageTemplate.objects
                .filter(protocol__in=self.protocols.all(),
                        daydelta__gte=dday_daydelta,
                        time__gte=self.local_appointment_date.time())
                .exclude(id__in=(
                            self.messages
                            .filter(for_appointment_date=self.appointment_date)
                            .values_list('template_id', flat=True)
                            ))
                .order_by('daydelta', 'time')
                .first()
            )
        else:
            return (
                MessageTemplate.objects
                .filter(protocol__in=self.protocols.all(),
                        daydelta__gte=dday_daydelta)
                .exclude(id__in=(
                            self.messages
                            .filter(for_appointment_date=self.appointment_date)
                            .values_list('template_id', flat=True)
                            ))
                .order_by('daydelta', 'time')
                .first()
            )

    def save(self, *args, **kwargs):
        if timezone.is_naive(self.appointment_date):
            self.appointment_date = timezone.make_aware(
                self.appointment_date, timezone=self.timezone)
        if timezone.is_naive(self.appointment_scheduled_dt):
            self.appointment_scheduled_dt = timezone.make_aware(
                self.appointment_scheduled_dt, timezone=self.timezone)
        # set confirm date on save
        if self.appointment_confirm_status == self.APPOINTMENT_CONFIRM.confirmed and \
                self.appointment_confirm_date is None:
            self.appointment_confirm_date = timezone.now()
        else:
            self.appointment_confirm_date = None
        # TODO check the case for adjusted appointment dates.
        super(Appointment, self).save(*args, **kwargs)
        self.find_protocols()
        self.schedule_next_message()

    def schedule_next_message(self):
        # check if no messages are queued first
        if self.messages.filter(twilio_status=Message.TWILIO_STATUS.queued).exists():
            logger.info("found message already queued. Skipping schedule_next_message")
            return None
        template = self.get_next_template()
        logger.info("found template {} for {}".format(template, self.__str__()))
        if template:
            message, created = self.messages.get_or_create(
                template=template,
                for_appointment_date=self.appointment_date,
                defaults={'twilio_status': Message.TWILIO_STATUS.queued})
            if created:
                from .tasks import deliver_message
                logger.info("scheduling message for {} to be sent at {}".format(
                    self.__str__(), message.scheduled_delivery_datetime))
                task_id = deliver_message.apply_async(
                    (message.id,), eta=message.scheduled_delivery_datetime)
                message.task_id = task_id
                message.save()
                return task_id
        return None

    def as_row(self):
        color_class = ""
        if self.appointment_confirm_status == self.APPOINTMENT_CONFIRM.unconfirmed:
            color_class = "bg-warning"
        elif self.appointment_confirm_status == self.APPOINTMENT_CONFIRM.cancelled:
            color_class = "bg-danger"
        return """
        <tr class="{0}">
          <td data-order="{1:%Y-%m-%dT%H:%M:%S}"><time title="{1:%b %d, %Y}" datetime="{1:%Y-%m-%dT%H:%M:%S}">{1:%b %d, %Y}</time></td>
          <td data-order="{2:%Y-%m-%dT%H:%M:%S}"><time>{3:%I:%M%p}</time></td>
          <td>{4}</td>
          <td>{5}</td>
          <td>{6}</td>
          <td>{7}</td>
          <td>
            <span>mobile:{8}</span><br />
            <span>home:{9}</span><br />
            <span>email:{10}</span>
          </td>
          <td>{11}</td>
          <td>{12}</td>
          <td>{13}</td>
          <td><a href="{14}">Details</a><!-- &nbsp;|&nbsp;<a href="#">SMS</a>&nbsp;|&nbsp;<a href="#">Call</a> --></td>
        </tr>
        """.format(
        color_class,
        self.appointment_date.date(),
        self.appointment_date, self.appointment_date.time(),
        self.scheduled_room,
        self.patient.name,
        self.patient.patient_mrn,
        self.patient.age,
        self.patient.patient_mobile_phone,
        self.patient.patient_home_phone,
        self.patient.patient_email_address,
        self.get_appointment_confirm_status_display(),
        self.procedure_description,
        self.appointment_provider.name,
        reverse('appointments:detail', args=[self.pk])).replace('\n', '')

    def __str__(self):
        return "{} at {} for pid {}: {}".format(
            self.scheduled_room,
            self.local_appointment_date,
            self.patient.id,
            self.appointment_confirm_status)


class Patient(models.Model):
    LANG = Choices(
        ('en', 'English'),
        ('es', 'Spanish')
    )
    # use as id?? TODO
    account_number = models.CharField(max_length=64)  #          patient account identifier      required    string  unique identifier assigned by the provider patient accounting system (pas) when a patient is admitted or seen for services
    patient_first_name = models.CharField(max_length=255)  #       patient first name              required    string  patient first name as in the clinical system
    patient_last_name = models.CharField(max_length=255)  #     patient last name               required    string  patient last name as in the clinical system
    patient_mrn = models.CharField(max_length=64, null=True, blank=True)  #            medical record number           desired     string  unique identifier assigned to an individual patient used to associate clinical records from one or more encounters
    patient_home_phone = models.CharField(max_length=64, null=True, blank=True)  #     patient home phone number       desired     string  patient home phone number as recorded on the system. if unavailable, leave blank
    patient_mobile_phone = models.CharField(max_length=64, null=True, blank=True)  #   patient cell or mobile phone number desired string  patient cell or mobile phone number as recorded on the system. if unavailable, leave blank
    patient_email_address = models.EmailField(null=True, blank=True)  #  patient email address           desired     string  patient email address as recorded on the system. if unavailable, leave blank
    patient_date_of_birth = models.DateField()
    lang = models.CharField(max_length=5, choices=LANG, default=LANG.en)
#   # strikes and stuff

    def save(self, *args, **kwargs):
        # TODO Will fail if number has + in the middle.
        self.patient_home_phone = self.number_to_e164_format(
            filter(lambda x: x.isdigit() or x == '+',
                   self.patient_home_phone))
        self.patient_mobile_phone = self.number_to_e164_format(
            filter(lambda x: x.isdigit() or x == '+',
                   self.patient_mobile_phone))
        super(Patient, self).save(*args, **kwargs)

    def number_to_e164_format(self, number):
        # TODO dynamic phone number
        if number.startswith('+'):
            return number
        else:
            return '+1{}'.format(number)

    def __str__(self):
        return "{} - {}, {}".format(
            self.id, self.patient_last_name, self.patient_first_name)

    @property
    def patient_phone(self):
        return self.patient_mobile_phone or self.patient_home_phone

    @property
    def contact_display(self):
        return "mobile:{}\nhome:{}\nemail:{}".format(
            self.patient_mobile_phone,
            self.patient_home_phone,
            self.patient_email_address)

    @property
    def name(self):
        return "{}, {}".format(self.patient_last_name, self.patient_first_name)

    @property
    def age(self):
        today = timezone.now()
        born = self.patient_date_of_birth
        return (today.year
                - born.year
                - ((today.month, today.day) < (born.month, born.day)))
