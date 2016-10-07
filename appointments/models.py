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


class Protocol(models.Model):
    """
    
    """
    priority = models.IntegerField()
    rule = models.CharField(max_length=255)



class Message(models.Model):
    message_type = models.CharField(max_length=255)
    execution_timedelta = models.IntegerField()
    protocol = models.ForeignKey('Protocol')
    script = models.CharField(max_length=255)  # sms


class Appointment(models.Model):
    status = models.CharField(max_length=255)
    patient = models.ForeignKey('Patient')
    appointment_type = models.CharField(max_length=255)
    procedure = models.CharField(max_length=255)
    datetime = models.DateTimeField()
    location = models.CharField(max_length=255)


class Patient(models.Model):
    patient_id = models.CharField(max_length=255, unique=True)
    mobile = models.CharField(max_length=255)
    landline = models.CharField(max_length=255)
    email = models.CharField(max_length=255)
    # strikes and stuff

class Doctor(models.Model):
    phone_1 = models.CharField(max_length=255)
