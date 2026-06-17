from django.conf import settings


def is_teacher_application_paywall_enabled():
    return getattr(settings, 'TEACHER_APPLICATION_PAYWALL_ENABLED', False)


def is_email_verification_enabled():
    return getattr(settings, 'EMAIL_VERIFICATION_ENABLED', True)


def get_application_notify_emails():
    raw = getattr(settings, 'APPLICATION_NOTIFY_EMAIL', 'connect@gulfteachers.com')
    if not raw:
        return ['connect@gulfteachers.com']
    return [email.strip() for email in str(raw).split(',') if email.strip()]
