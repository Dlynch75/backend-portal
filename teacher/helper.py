from datetime import date
from core.models import UserPackage

def can_create_post(teacher):
    # Reset post count if it's a new month
    today = date.today()
    user_package =  UserPackage.objects.get(teacher=teacher)
    if teacher.last_reset_date.month != today.month or teacher.last_reset_date.year != today.year:
        teacher.teacher.applied_count = 0
        teacher.last_reset_date = today
        teacher.teacher.save()
    package_limit = user_package.package.offer.get("allow_application")
    if package_limit is None:
        return True  # Unlimited package

    return teacher.teacher.applied_count < package_limit

