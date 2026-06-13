from django.conf import settings


def is_teacher_application_paywall_enabled():
    return getattr(settings, 'TEACHER_APPLICATION_PAYWALL_ENABLED', False)
