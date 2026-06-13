from django.db.models.signals import post_save
from django.dispatch import receiver
from school.models import JobPosting
from teacher.job_alerts import notify_matching_job_alerts


@receiver(post_save, sender=JobPosting)
def notify_job_alerts_on_create(sender, instance, created, **kwargs):
    if created and instance.status == 'open':
        notify_matching_job_alerts(instance)
