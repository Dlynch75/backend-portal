import os
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.cache import cache
from utils.utils import send_notification_email


def get_frontend_url():
    return os.getenv('FRONTEND_URL', 'https://www.gulfteachers.com').rstrip('/')


def build_verification_link(user):
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    return f"{get_frontend_url()}/verify-email?uid={uid}&token={token}"


def get_user_display_name(user):
    if user.is_teacher and hasattr(user, 'teacher'):
        return user.teacher.full_name or user.username
    if user.is_school and hasattr(user, 'school'):
        return user.school.school_name or user.username
    return user.username


def send_user_verification_email(user):
    verification_link = build_verification_link(user)
    display_name = get_user_display_name(user)
    subject = "Verify Your Email - Gulf Teachers"
    message = f"""Hello {display_name},

Welcome to Gulf Teachers! Please verify your email address to activate your account.

Click the link below to verify your email:
{verification_link}

This link will expire in 24 hours.

If you didn't create an account, please ignore this email.

Best regards,
The Gulf Teachers Team
"""
    send_notification_email(subject, message, [user.email])


RESEND_VERIFY_CACHE_SECONDS = 60


def can_resend_verification(email):
    cache_key = f"resend_verify_{email.lower().strip()}"
    return cache.get(cache_key) is None


def mark_verification_resent(email):
    cache_key = f"resend_verify_{email.lower().strip()}"
    cache.set(cache_key, True, RESEND_VERIFY_CACHE_SECONDS)
