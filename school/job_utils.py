from django.db.models import Q, Case, When, Value, IntegerField
from django.utils import timezone


def active_featured_filter():
    now = timezone.now()
    return Q(is_featured=True) & (Q(featured_until__isnull=True) | Q(featured_until__gt=now))


def apply_job_sorting(queryset, sort='recent'):
    sort = (sort or 'recent').lower()
    featured_q = active_featured_filter()

    queryset = queryset.annotate(
        is_active_featured=Case(
            When(featured_q, then=Value(1)),
            default=Value(0),
            output_field=IntegerField(),
        )
    )

    if sort == 'featured':
        return queryset.filter(featured_q).order_by('-created_at')

    if sort == 'popular':
        return queryset.order_by('-is_active_featured', '-viewd', '-created_at')

    return queryset.order_by('-is_active_featured', '-created_at')


def is_job_featured(job):
    if not job.is_featured:
        return False
    if job.featured_until is None:
        return True
    return job.featured_until > timezone.now()
