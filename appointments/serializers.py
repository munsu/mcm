import logging
from collections import OrderedDict
from rest_framework import serializers
from rest_framework.fields import SkipField
from rest_framework.relations import PKOnlyObject
from .models import (
    Appointment, Patient, Facility, Client, Protocol, MessageTemplate, MessageAction,
    Constraint, Provider, DayAfterAppointment
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


class DayAfterAppointmentSerializer(serializers.Serializer):
    """
    Appointment_facility    Facility Name   required    string  Facility at which this appointment is scheduled or occured; required for organizations submitting data for more than one facility
    Appointment_Number  Appointment or Procedure Number required    string  Uniquely identifies an appointment or procedure within the health system
    Account_Number  Patient Account Identifier  required    string  Unique identifier assigned by the provider Patient Accounting System (PAS) when a patient is admitted or seen for services
    Patient_MRN Medical Record Number   desired string  Unique identifier assigned to an individual patient used to associate clinical records from one or more encounters
    Appointment_Date    Appointment or Procedure Date   required    yyyy-MM-dd hh:mm:ss Date of appointment.  The daily upload should include only cases with any activity for (t-1) 00:00 through 23:59
    Actual_Room Actual Operating Room or Procedure Room required    string  Procedure, Operating or Exam room into which this case or appointment actually occurred
    Appointment_Status  Actual appointment status   required    string  Status of the appointment - Arrived, Completed, Cancelled, In Progress
    Appointment_type    Appointment or Case Type    optional    string  Type of case (e.g., urgent, emergent, elective, etc.) or type of appointment (new visit, follow-up, etc.)
    Schedule_Type   Schedule Type Indicator required    string  Indicates whether a case or appointment was scheduled as an elective or an add-on (for all cases into the future usually only elective - for cases from yesterday - both elective and add-on)
    Delay_code  Delay Code  desired string  Code indicating reason for a delay of less than one day
    delay_reason    Delay Reason    desired string  Reason indicating why case was delayed
    cancel_code Cancellation Code   desired string  Code indicating reason for delay of one day or greater or case cancellation; could be a Boolean indicator simply indicating the case was cancelled
    cancel_reason   Cancellation Reason desired string  Reason indicating why case was cancelled
    cancel_dt   Cancellation Date   desired yyyy-MM-dd hh:mm:ss Date case was cancelled.  This is required if the record is a cancelled case.
    preop_start_tm  Patient Start In PreOp (Holding)    optional    yyyy-MM-dd hh:mm:ss Date and time that the patient starts to be prepared for surgery
    preop_end_tm    Patient Finished In PreOp (Holding) optional    yyyy-MM-dd hh:mm:ss Date and time that the patient is finished with prep for surgery
    anes_start_tm   Anesthesia Start    optional    yyyy-MM-dd hh:mm:ss Date and time when the anesthesiologist began monitoring the patient
    pat_in_tm   Patient In Room - Actual    required    yyyy-MM-dd hh:mm:ss Date and time when patient actually enters the operating room
    sched_pat_in_tm Patient In Room - Scheduled required    yyyy-MM-dd hh:mm:ss Date and time when patient was scheduled to enter the operating
    pat_out_tm  Patient Out Of Room - Actual    required    yyyy-MM-dd hh:mm:ss Date and time at which patient actually left the operating Room
    sched_pat_out_tm    Patient Out Of Room - Scheduled desired yyyy-MM-dd hh:mm:ss Date and time at which patient was scheduled to leave the operating room
    cut_tm  Cut Time - Actual   desired yyyy-MM-dd hh:mm:ss Date and time the procedure is actually begun ( i.e., incision)
    sched_cut_tm    Cut Time - Scheduled    optional    yyyy-MM-dd hh:mm:ss Date and time the procedure was scheduled to begin (i.e., incision)
    sched_close_tm  Procedure Finish (Close) - Scheduled    optional    yyyy-MM-dd hh:mm:ss Scheduled date and time when all instrument and sponge counts are completed and verified as correct; all post-op radiological studies to be done in the operating room are completed; all dressings and drains are secured; and the physician / surgeons have completed 
    close_tm    Procedure Finish (Close) - Actual   desired yyyy-MM-dd hh:mm:ss Actual date and time when all instrument and sponge counts are completed and verified as correct; all post-op radiological studies to be done in the operating room are completed; all dressings and drains are secured; and the physician / surgeons have completed all
    anes_stop_tm    Anesthesia Finish   optional    yyyy-MM-dd hh:mm:ss Date and time at which anesthesiologist turns over care of the patient to a post anesthesia care team (either PACU or ICU).
    pacu_in_tm  Arrival in PACU optional    yyyy-MM-dd hh:mm:ss Date and time of patient arrival in Post Anesthesia Care Unit
    pacu_ready_tm   Ready for Discharge from PACU   optional    yyyy-MM-dd hh:mm:ss Date and time at which the patient is medically ready for discharge from the Post Anesthesia Care Unit
    pacu_out_tm Discharge from PACU optional    yyyy-MM-dd hh:mm:ss Date and time patient is transported out of Post Anesthesia Care Unit
    cleanup_start_tm    Room Clean-Up Start optional    yyyy-MM-dd hh:mm:ss Date and time housekeeping begins cleanup of operating room
    cleanup_stop_tm Room Clean-Up Finished  optional    yyyy-MM-dd hh:mm:ss Date and time operating room is clean and ready for setup of supplies and equipment for the next case
    setup_start_tm  Room Set-Up Start   optional    yyyy-MM-dd hh:mm:ss Date and time when personnel begin setting-up, in the operating room, the supplies and equipment for the next case
    setup_stop_tm   Room Ready - Actual optional    yyyy-MM-dd hh:mm:ss Date and time when room was actually cleaned and ready for the beginning of the next case
    sched_case_dur  Case Duration - Scheduled   optional    integer Minutes allocated to the case during scheduling
    sched_setup_dur Set-Up Duration - Scheduled optional    integer Minutes allocated to case set-up during scheduling
    sched_cleanup_dur   Clean-Up Duration - Scheduled   optional    integer Minutes allocated to clean up during scheduling
    pacu_delay_reason   PACU delay reason   optional    string  Reason why patient was delay in leaving the PACU
    """
    appointment_facility = serializers.CharField()
    appointment_number = serializers.CharField()
    account_number = serializers.CharField()
    patient_mrn = serializers.CharField()
    appointment_date = serializers.DateTimeField()
    actual_room = serializers.CharField()
    appointment_status = serializers.CharField()
    appointment_type = serializers.CharField(allow_blank=True, required=False)
    schedule_type = serializers.CharField()
    delay_code = serializers.CharField(allow_blank=True, required=False)
    delay_reason = serializers.CharField(allow_blank=True, required=False)
    cancel_code = serializers.CharField(allow_blank=True, required=False)
    cancel_reason = serializers.CharField(allow_blank=True, required=False)
    cancel_dt = serializers.DateTimeField(required=False)
    preop_start_tm = serializers.DateTimeField(required=False)
    preop_end_tm = serializers.DateTimeField(required=False)
    anes_start_tm = serializers.DateTimeField(required=False)
    pat_in_tm = serializers.DateTimeField()
    sched_pat_in_tm = serializers.DateTimeField()
    pat_out_tm = serializers.DateTimeField()
    sched_pat_out_tm = serializers.DateTimeField(required=False)
    cut_tm = serializers.DateTimeField(required=False)
    sched_cut_tm = serializers.DateTimeField(required=False)
    sched_close_tm = serializers.DateTimeField(required=False)
    close_tm = serializers.DateTimeField(required=False)
    anes_stop_tm = serializers.DateTimeField(required=False)
    pacu_in_tm = serializers.DateTimeField(required=False)
    pacu_ready_tm = serializers.DateTimeField(required=False)
    pacu_out_tm = serializers.DateTimeField(required=False)
    cleanup_start_tm = serializers.DateTimeField(required=False)
    cleanup_stop_tm = serializers.DateTimeField(required=False)
    setup_start_tm = serializers.DateTimeField(required=False)
    setup_stop_tm = serializers.DateTimeField(required=False)
    sched_case_dur = serializers.IntegerField(required=False)
    sched_setup_dur = serializers.IntegerField(required=False)
    sched_cleanup_dur = serializers.IntegerField(required=False)
    pacu_delay_reason = serializers.CharField(allow_blank=True, required=False)

    def create(self, validated_data):
        logger.info("VALIDATED DATA {}".format(validated_data))
        try:
            appointment_number = validated_data.pop('appointment_number')
            user = self.context['request'].user
            appointment = Appointment.objects.filter(
                appointment_number=appointment_number,
                client=user.profile.client).first()
        except Appointment.DoesNotExist:
            raise serializers.ValidationError(
                'Appointment(appointment_number={}) does not exist'.format(appointment_number))

        day_after_appointment = DayAfterAppointment(appointment=appointment, data=validated_data)
        day_after_appointment.save()
        return day_after_appointment


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
