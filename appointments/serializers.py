from rest_framework import serializers


class AppointmentSerializer(serializers.Serializer):
    appointment_facility
    appointment_number
    account_number
    patient_first_name
    patient_last_name
    appointment_provider
    appointment_scheduled_service
    appointment_status
    patient_type
    procedure_description
    scheduled_room
    scheduled_duration
    appointment_date
    appointment_scheduled_dt
    provider_specialty
    appointment_type
    appointment_class
    asa_rating
    modified_procedure_description
    asa_cd
    provider_id
    provider_npi_id
    patient_mrn
    patient_home_phone
    patient_mobile_phone
    patient_email_address

    appointment_facility
    appointment_number
    account_number
    patient_first_name
    patient_last_name
    appointment_provider
    appointment_scheduled_service
    appointment_status
    patient_type
    procedure_description
    scheduled_room
    scheduled_duration
    appointment_date
    appointment_scheduled_dt
    provider_specialty
    appointment_type
    appointment_class
    asa_rating
    modified_procedure_description
    asa_cd
    provider_id
    provider_npi_id
    patient_mrn
    patient_home_phone
    patient_mobile_phone
    patient_email_address

    def create(self, validated_data):
        obj, created = Appointment.objects.update_or_create(**validated_data)
        if created:
            # fire send sms
            pass