from __future__ import unicode_literals

from django.db import models

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
