from django.db.models import Q
from django.utils import timezone
from utils.utils import send_notification_email
from core.email_utils import get_frontend_url
from .models import JobAlert


def job_matches_alert(job, alert):
    if alert.title and alert.title.strip():
        if alert.title.lower() not in job.title.lower():
            return False
    if alert.position and alert.position.strip():
        blob = f"{job.title} {job.description}".lower()
        if alert.position.lower() not in blob:
            return False
    if alert.subject and alert.subject.strip():
        subject_blob = f"{job.subject or ''} {job.title} {job.description} {job.required_qualifications}".lower()
        if alert.subject.lower() not in subject_blob:
            return False
    if alert.location and alert.location.strip():
        if alert.location.lower() not in (job.location or '').lower():
            return False
    return True


def notify_matching_job_alerts(job):
    alerts = JobAlert.objects.filter(is_active=True).select_related('teacher')
    frontend_url = get_frontend_url()

    for alert in alerts:
        if not job_matches_alert(job, alert):
            continue

        teacher = alert.teacher
        subject = f"New job match: {job.title}"
        message = f"""Hello {teacher.full_name or teacher.username},

A new job matching your saved alert is now live on Gulf Teachers.

Job: {job.title}
School: {job.school.school_name if job.school else 'School'}
Location: {job.location}
Subject: {job.subject or 'Not specified'}

View job: {frontend_url}/jobs-description/{job.id}

Best regards,
The Gulf Teachers Team
"""
        try:
            send_notification_email(subject, message, [teacher.email])
            alert.last_notified_at = timezone.now()
            alert.save(update_fields=['last_notified_at'])
        except Exception as e:
            print(f"Failed to send job alert to {teacher.email}: {e}")
