from datetime import timedelta
from django.utils import timezone
from school.models import JobPosting


def activate_job_feature(job_id, duration_days=30):
    job = JobPosting.objects.get(pk=job_id)
    job.is_featured = True
    job.featured_until = timezone.now() + timedelta(days=duration_days)
    job.save(update_fields=['is_featured', 'featured_until'])
    return job
