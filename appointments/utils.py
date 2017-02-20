from contextlib import contextmanager
from django.utils import translation


@contextmanager
def language(lang):
    translation.activate(lang)
    yield
    translation.deactivate()


def t1_to_t8():
    """
    appointment_facility
    appointment_number
    account_number
    patient_first_name
    patient_last_name
    appointment_provider
    appointment_date
    appointment_scheduled_service
    appointment_status
    patient_type
    procedure_description
    scheduled_room
    scheduled_duration
    appointment_scheduled_dt

    TODO
    desired
        patient_mrn
        patient_home_phone
        patient_mobile_phone
        patient_email_address
    optional
        provider_specialty
        appointment_type
        appointment_class
        asa_rating
        modified_procedure_description
        asa_cd
        provider_id
        provider_npi_id
    """
    pass

def flatten_dict(dd, separator='__', prefix=''):
    # from http://stackoverflow.com/a/19647596/2365267
    return { prefix + separator + k if prefix else k : v
             for kk, vv in dd.items()
             for k, v in flatten_dict(vv, separator, kk).items()
             } if isinstance(dd, dict) else { prefix : dd }
