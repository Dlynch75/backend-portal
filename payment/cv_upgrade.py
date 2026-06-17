import uuid
from django.conf import settings
from django.utils import timezone
from utils.utils import send_notification_email
from .models import CVUpgradeOrder


def get_cv_upgrade_amount():
    return getattr(settings, 'CV_UPGRADE_AMOUNT', 19.99)


def build_share_url(token):
    base = settings.FRONTEND_URL.rstrip('/')
    return f"{base}/cv-services/{token}"


def teacher_has_active_order(teacher):
    return CVUpgradeOrder.objects.filter(
        teacher=teacher,
        status__in=['paid', 'in_progress'],
    ).exists()


def get_or_create_pending_order(teacher=None, school=None, candidate_email='', candidate_name=''):
    if teacher and teacher_has_active_order(teacher):
        raise Exception("This teacher already has a CV upgrade in progress.")

    if teacher:
        pending = CVUpgradeOrder.objects.filter(teacher=teacher, status='pending_payment').order_by('-created_at').first()
        if pending:
            return pending

    return CVUpgradeOrder.objects.create(
        teacher=teacher,
        created_by_school=school,
        candidate_email=candidate_email or (teacher.email if teacher else ''),
        candidate_name=candidate_name or (getattr(teacher, 'full_name', '') if teacher else ''),
        amount=get_cv_upgrade_amount(),
        currency='USD',
    )


def get_or_create_guest_order(candidate_email='', candidate_name=''):
    email = candidate_email.strip().lower()
    if not email:
        raise Exception("Please enter your email address.")

    pending = CVUpgradeOrder.objects.filter(
        teacher__isnull=True,
        candidate_email__iexact=email,
        status='pending_payment',
    ).order_by('-created_at').first()
    if pending:
        if candidate_name and not pending.candidate_name:
            pending.candidate_name = candidate_name.strip()
            pending.save(update_fields=['candidate_name'])
        return pending

    return CVUpgradeOrder.objects.create(
        teacher=None,
        candidate_email=email,
        candidate_name=candidate_name.strip(),
        amount=get_cv_upgrade_amount(),
        currency='USD',
    )


def complete_cv_upgrade_payment(order_id, stripe_session_id=None, customer_email=None, customer_name=None):
    order = CVUpgradeOrder.objects.select_related('teacher').get(pk=order_id)
    if order.status == 'paid':
        return order

    if customer_email and not order.candidate_email:
        order.candidate_email = customer_email
    if customer_name and not order.candidate_name:
        order.candidate_name = customer_name

    order.status = 'paid'
    order.paid_at = timezone.now()
    if stripe_session_id:
        order.stripe_session_id = stripe_session_id
    order.save(update_fields=['status', 'paid_at', 'stripe_session_id'])

    send_cv_upgrade_payment_emails(order)
    return order


def send_cv_upgrade_payment_emails(order):
    name = order.candidate_name or 'Candidate'
    email = order.candidate_email
    cv_url = order.teacher.cv_url if order.teacher and order.teacher.cv_url else None

    client_message = (
        f"A new CV Upgrade payment has been received.\n\n"
        f"Candidate: {name}\n"
        f"Email: {email}\n"
        f"Order ID: {order.id}\n"
        f"Amount: ${order.amount} {order.currency}\n\n"
        f"Please review the candidate's CV and complete the professional upgrade."
    )
    send_notification_email(
        "New CV Upgrade order – action required",
        client_message,
        ['connect@gulfteachers.com'],
        cv_url,
    )

    if email:
        teacher_message = (
            f"Hi {name},\n\n"
            f"Thank you for purchasing the Gulf Teachers CV Upgrade service ($19.99).\n\n"
            f"Our team will professionally review and upgrade your CV. "
            f"You will hear from us within 3–5 business days.\n\n"
            f"Questions? Reply to connect@gulfteachers.com"
        )
        send_notification_email(
            "Your CV Upgrade payment is confirmed",
            teacher_message,
            [email],
        )
