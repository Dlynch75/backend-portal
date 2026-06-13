from django.conf import settings


def is_teacher_application_paywall_enabled():
    return getattr(settings, 'TEACHER_APPLICATION_PAYWALL_ENABLED', False)


def is_email_verification_enabled():
    return getattr(settings, 'EMAIL_VERIFICATION_ENABLED', True)
