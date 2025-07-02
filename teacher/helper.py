from datetime import date
from core.models import UserPackage

from datetime import date, timedelta


def can_create_post(teacher):
    today = date.today()

    try:
        user_package = UserPackage.objects.get(teacher=teacher)
    except UserPackage.DoesNotExist:
        return False  # No package, can't post

    # Check if it's a trial package
    if user_package.package.package_type == 'trial_teacher':
        # Check if 30 days have passed since created_at
        if (date.today() - user_package.created_at.date()).days > 30:
            return False  # Trial expired
        else:
            return True  # Trial still active

    # Reset post count if it's a new month (only for non-trial packages)
    if teacher.last_reset_date.month != today.month or teacher.last_reset_date.year != today.year:
        teacher.teacher.applied_count = 0
        teacher.last_reset_date = today
        teacher.teacher.save()

    # Get post limit from package
    package_limit = user_package.package.offer.get("allow_application")

    if package_limit is None:
        return True  # Unlimited posts

    return teacher.teacher.applied_count < package_limit

