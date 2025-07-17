from datetime import date
from core.models import UserPackage

def can_create_post(school):
    # Reset post count if it's a new month
    today = date.today()
    user_package =  UserPackage.objects.get(school=school)

    # Check if it's a trial package
    if user_package.package.package_type == 'trial_teacher':
        # Check if 30 days have passed since created_at
        if (date.today() - user_package.created_at.date()).days > 30:
            return False  # Trial expired
        else:
            return True  # Trial still active
    
    if school.last_reset_date.month != today.month or school.last_reset_date.year != today.year:
        school.school.post_count = 0
        school.last_reset_date = today
        school.school.save()
    package_limit = user_package.package.offer.get("allow_application")
    if package_limit is None:
        return True  # Unlimited package

    return school.school.post_count < package_limit