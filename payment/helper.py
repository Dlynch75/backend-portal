from django.conf import settings

def get_price_id(subscription_type):
    price_id_map = {
        'single_teacher': settings.SINGLE_PACKAGE_PRICE_ID,
        'bronze_teacher': settings.BRONZE_TEACHER_PACKAGE_PRICE_ID,
        'silver_teacher': settings.SILVER_TEACHER_PACKAGE_PRICE_ID,
        'gold_teacher': settings.GOLD_TEACHER_PACKAGE_PRICE_ID,
        'bronze_school': settings.BRONZE_SCHOOL_PACKAGE_PRICE_ID,
        'silver_school': settings.SILVER_SCHOOL_PACKAGE_PRICE_ID,
        'gold_school': settings.GOLD_SCHOOL_PACKAGE_PRICE_ID,
        'test': settings.TEST_PRICE_ID,
    }

    # Return the price ID if the subscription type matches
    return price_id_map.get(subscription_type, None)  # Returns None if no match is found
