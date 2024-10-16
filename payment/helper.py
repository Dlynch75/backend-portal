from django.conf import settings
from django.shortcuts import render
from rest_framework.views import APIView
import stripe
from django.conf import settings
from django.shortcuts import redirect
from core.models import  UserPackage
from payment.models import Invoice
from school_project.settings import STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET
from utils.response import create_message, create_response
from utils.utils import get_user_from_token, require_authentication, response_500
import stripe
stripe.api_key = STRIPE_SECRET_KEY


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

# Separate functions for handling events

def handle_invoice_created(user, invoice):
    Invoice.objects.create(
        user=user,
        invoice_id=invoice['id'],
        amount=invoice['amount_due'] / 100,  # Convert cents to dollars
        currency=invoice['currency'],
        status=invoice['status'],
        created_at=invoice['created'],
    )

def handle_invoice_payment_succeeded(user, invoice):
    Invoice.objects.filter(invoice_id=invoice['id']).update(
        status='paid',
        payment_date=invoice.get('paid_at'),
    )
    user.is_subscribed = True
    user.save()

def handle_invoice_payment_failed(user, invoice):
    Invoice.objects.filter(invoice_id=invoice['id']).update(
        status='failed',
        canceled_at=invoice.get('attempted'),
    )
    if user.stripe_subscription_id:
        stripe_subscription_id = user.stripe_subscription_id
        # Cancel the Stripe subscription
        stripe.Subscription.delete(stripe_subscription_id)

        # Optional: Update user record in your database
        user.stripe_subscription_id = None
        
    user.is_subscribed = False
    user.save()
    

def handle_subscription_deleted(user, subscription):
    user.is_subscribed = False
    user.save()
    UserPackage.objects.filter(user=user).delete() if UserPackage.objects.filter(user=user).exists() else None
