from __future__ import unicode_literals

from django.db import models

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
    user = models.OneToOneField('auth.User')
    client = models.ForeignKey('Client')


class Client(models.Model):
    """
    For multi tenancy
    """
    name = models.CharField(max_length=255)
    active = models.BooleanField(default=True)


class Facility(models.Model):
    """
    Where patients are appointed to.
    """
    client = models.ForeignKey('Client', models.PROTECT)
    name = models.CharField(max_length=255)
    # TODO shortform for sms?
    address = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20)

    class Meta:
        verbose_name_plural = 'facilities'

    def __str__(self):
        return self.name


class Protocol(models.Model):
    """
    has messages
    """
    clients = models.ManyToManyField('Client')
    priority = models.IntegerField()  # higher 
    rule = models.CharField(max_length=255)


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
    # sample content: "{date}\n{content}"
    content = models.CharField(max_length=255)  # sms
    timedelta = models.DurationField()  # TODO durationfield
    protocol = models.ForeignKey('Protocol', models.PROTECT)


class Message(models.Model):
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
    TWILIO_STATUS_CHOICES = (
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
    template = models.ForeignKey('MessageTemplate', models.PROTECT)
    recipient = models.ForeignKey('Patient', models.PROTECT)
    appointment = models.ForeignKey('Appointment', models.PROTECT)
    twilio_status = models.CharField(
        max_length=64, blank=True, null=True, choices=TWILIO_STATUS_CHOICES)
    twilio_error = models.CharField(
        max_length=64, blank=True, null=True, choices=TWILIO_ERROR_CHOICES)

    def send(self):
        if self.template.message_type == 'text':
            body = self.template.content.format(**self.appointment.get_data())
        else:
            raise Exception("Email/Call not yet allowed.")


class Reply(models.Model):
    """
    Mobile Originating (MO) Message
    """
    message = models.ForeignKey('Message', models.PROTECT)
    content = models.TextField()
    date = models.DateTimeField(auto_now_add=True)


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
    APPOINTMENT_CONFIRM_CHOICES = (
        ('confirmed', 'Confirmed'),
        ('unconfirmed', 'Unconfirmed'),
    )
    PATIENT_TYPE_CHOICES = (
        ('inpatient', 'Inpatient'),
        ('outpatient', 'Outpatient'),
    )
    client = models.ForeignKey('Client', models.PROTECT)
    patient = models.ForeignKey('Patient', models.PROTECT)
    # TODO choices
    appointment_confirm_status = models.CharField(max_length=64)

    appointment_facility = models.ForeignKey('Facility', models.PROTECT)  #    facility name                   required    string  facility at which this appointment is scheduled or occured; required for organizations submitting data for more than one facility
    appointment_number = models.CharField(max_length=64)  #     appointment or procedure number required    string  uniquely identifies an appointment or procedure within the health system
    appointment_provider = models.CharField(max_length=255)  #   primary provider, surgeon       required    string  the primary care provider or surgeon of record for this appointment
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
    provider_id = models.CharField(max_length=64, null=True, blank=True)  #            physician id                    optional    string  employee number for the primary surgeon. must match to physician id in patient accounting system.
    provider_npi_id = models.CharField(max_length=64, null=True, blank=True)  #        physician npi id                optional    string  national provider identification for the primary provider.

    provider_specialty = models.CharField(max_length=64, null=True, blank=True)  #   surgeon specialty               optional    string  specialty of the primary provider or surgeon on the appointment or case

    # Patient stuff but changes per appointment
    patient_type = models.CharField(max_length=64, choices=PATIENT_TYPE_CHOICES)  #            patient type                    required    string  inpatient - surgery admit / outpatient status of patient
    asa_rating = models.CharField(max_length=64, null=True, blank=True)  #             asa rating                      optional    string  the american society of anesthesiologists acuity rating for this patient
    asa_cd = models.CharField(max_length=64, null=True, blank=True)  #                 asa code

    # def save(self, *args, **kwargs):
    #     if self.appointment_number
    #     super(Appointment, self).save(*args, **kwargs)
    def get_data(self):
        # return dict of data relevant to sms
        pass

class Patient(models.Model):
    # use as id?? TODO
    account_number = models.CharField(max_length=64)  #          patient account identifier      required    string  unique identifier assigned by the provider patient accounting system (pas) when a patient is admitted or seen for services
    patient_first_name = models.CharField(max_length=255)  #       patient first name              required    string  patient first name as in the clinical system
    patient_last_name = models.CharField(max_length=255)  #     patient last name               required    string  patient last name as in the clinical system
    patient_mrn = models.CharField(max_length=64, null=True, blank=True)  #            medical record number           desired     string  unique identifier assigned to an individual patient used to associate clinical records from one or more encounters
    patient_home_phone = models.CharField(max_length=64, null=True, blank=True)  #     patient home phone number       desired     string  patient home phone number as recorded on the system. if unavailable, leave blank
    patient_mobile_phone = models.CharField(max_length=64, null=True, blank=True)  #   patient cell or mobile phone number desired string  patient cell or mobile phone number as recorded on the system. if unavailable, leave blank
    patient_email_address = models.EmailField(null=True, blank=True)  #  patient email address           desired     string  patient email address as recorded on the system. if unavailable, leave blank
#     # strikes and stuff

# class Doctor(models.Model):
#     phone_1 = models.CharField(max_length=255)
