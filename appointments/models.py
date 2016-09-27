from __future__ import unicode_literals

from django.db import models

# Create your models here.
class UserProfile(models.Model):
    user = models.OneToOneField('auth.User')
    company = models.ForeignKey('Company')


class Company(models.Model):
    name = models.CharField(max_length=255)


class Protocol(models.Model):
    rule = models.CharField(max_length=255)


class Message(models.Model):
    message_type = models.CharField()
    execution_timedelta = models.IntegerField()
    protocol = models.ForeignKey('Protocol')
    script = models.CharField()  # sms


class Appointment(models.Model):
    status = models.CharField()
    patient = models.ForeignKey('Patient')
    appointment_type = models.CharField()
    procedure = models.CharField()
    datetime = models.DateTimeField()
    location = models.CharField()


class Patient(models.Model):
    patient_id = models.CharField(unique=True)
    phone_1 = models.CharField()
    phone_2 = models.CharField()
    email = models.CharField()
    # strikes and stuff

class Doctor(models.Model):
    phone_1 = models.CharField()
