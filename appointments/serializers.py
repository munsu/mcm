import logging
from collections import OrderedDict
from rest_framework import serializers
from rest_framework.fields import SkipField
from rest_framework.relations import PKOnlyObject
from .models import (
    Appointment, Patient, Facility, Client, Protocol, MessageTemplate, MessageAction,
    Constraint, Provider
)


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


class AppointmentSerializer(serializers.Serializer):
    appointment_facility = serializers.CharField()
    appointment_number = serializers.CharField()
    account_number = serializers.CharField()
    appointment_provider = serializers.CharField()
    appointment_scheduled_service = serializers.CharField()
    appointment_status = serializers.CharField()
    procedure_description = serializers.CharField()
    scheduled_room = serializers.CharField()
    scheduled_duration = serializers.CharField()
    appointment_date = serializers.DateTimeField()
    appointment_scheduled_dt = serializers.DateTimeField()
    provider_specialty = serializers.CharField(required=False)
    appointment_type = serializers.CharField(allow_blank=True, required=False)
    appointment_class = serializers.CharField(allow_blank=True, required=False)
    # modified_procedure_description = serializers.CharField(required=False)
    provider_id = serializers.CharField(allow_blank=True, required=False)
    provider_npi_id = serializers.CharField(allow_blank=True, required=False)
    patient_type = serializers.CharField()
    asa_rating = serializers.CharField(allow_blank=True, required=False)
    asa_cd = serializers.CharField(allow_blank=True, required=False)

    patient_first_name = serializers.CharField()
    patient_last_name = serializers.CharField()
    patient_mrn = serializers.CharField(required=False)
    patient_home_phone = serializers.CharField(required=False)
    patient_mobile_phone = serializers.CharField()
    patient_email_address = serializers.EmailField()
    patient_date_of_birth = serializers.DateField()

    def create(self, validated_data):
        """
        TODO map this to the things
        will create Appointment, Patient, and Facility
        """
        logger.info("VALIDATED DATA {}".format(validated_data))
        patient_fields = [f.name for f in Patient._meta.local_fields]
        # logger.info("PATIENT OB {}".format(Patient._meta.local_fields))
        # logger.info("PATIENT FIELDS {}".format(patient_fields))
        patient_data = {k: validated_data.get(k)
                        for k in patient_fields
                        if validated_data.get(k)}
        patient, _ = Patient.objects.update_or_create(**patient_data)
        facility, _ = Facility.objects.get_or_create(
            client=validated_data.get('client'),
            name=validated_data.get("appointment_facility"))

        # hotfix for provider name. this should be somewhere else.
        validated_data['name'] = validated_data['appointment_provider']
        provider_fields = [f.name for f in Provider._meta.local_fields]
        provider_data = {k: validated_data.get(k)
                         for k in provider_fields
                         if validated_data.get(k)}
        provider, _ = Provider.objects.update_or_create(
            provider_npi_id=provider_data.pop('provider_npi_id'),
            defaults=provider_data)

        appointment_fields = [f.name for f in Appointment._meta.local_fields]
        appointment_data = {k: validated_data.get(k)
                            for k in appointment_fields
                            if validated_data.get(k)}
        appointment_data['patient'] = patient
        appointment_data['appointment_facility'] = facility
        appointment_data['appointment_provider'] = provider

        # relocate
        appointment_updatable_fields = [
            'appointment_date',
            'appointment_confirm_status',
            'appointment_status']
        defaults = {k: appointment_data.pop(k)
                    for k in appointment_updatable_fields
                    if appointment_data.get(k)}
        appointment, created = Appointment.objects.update_or_create(
            defaults=defaults, **appointment_data)
        if created:
            # fire send sms
            logger.info("Created {} {}".format(appointment, created))

        return appointment


    def to_representation(self, instance):
        """
        Object instance -> Dict of primitive datatypes.
        """
        ret = OrderedDict()
        short_fields = ['appointment_facility', 'procedure_description', 'appointment_date']
        # for field in fields:
        #     ret[field] = field.to_representation(instance)
        # return ret
        fields = self._readable_fields
        for field in fields:
            if field.field_name not in short_fields:
                continue
            try:
                attribute = field.get_attribute(instance)
            except SkipField:
                continue

            # We skip `to_representation` for `None` values so that fields do
            # not have to explicitly deal with that case.
            #
            # For related fields with `use_pk_only_optimization` we need to
            # resolve the pk value.
            check_for_none = attribute.pk if isinstance(attribute, PKOnlyObject) else attribute
            if check_for_none is None:
                ret[field.field_name] = None
            else:
                ret[field.field_name] = field.to_representation(attribute)

        return ret


class MessageActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageAction
        fields = (
            'id', 'keyword', 'action'
        )


class MessageTemplateSerializer(serializers.ModelSerializer):
    actions = MessageActionSerializer(many=True)

    class Meta:
        model = MessageTemplate
        depth = 1
        fields = (
            'message_type',
            'content',
            'daydelta',
            'time',
            'actions'
        )

    def create(self, validated_data):
        actions_data = validated_data.pop('actions')
        template = MessageTemplate.objects.create(**validated_data)
        for action_data in actions_data:
            MessageAction.objects.create(template=template, **action_data)
        return template


class ConstraintSerializer(serializers.ModelSerializer):
    class Meta:
        model = Constraint
        fields = (
            'field',
            'lookup_type',
            'value'
        )


class ProtocolSerializer(serializers.ModelSerializer):
    templates = MessageTemplateSerializer(many=True)
    constraints = ConstraintSerializer(many=True)

    class Meta:
        model = Protocol
        depth = 1
        fields = (
            'id', 'name', 'priority', 'constraints', 'templates'
        )
        # fields = ('id', 'account_name', 'users', 'created')

    def create(self, validated_data):
        templates_data = validated_data.pop('templates')
        protocol = Protocol.objects.create(**validated_data)
        for template_data in templates_data:
            MessageTemplate.objects.create(protocol=protocol, **template_data)
        return protocol
