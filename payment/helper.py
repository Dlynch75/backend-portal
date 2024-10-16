from django.conf import settings
from django.shortcuts import render
from rest_framework.views import APIView
import stripe
from django.conf import settings
from django.shortcuts import redirect
from core.models import  Package, UserPackage
from payment.models import Invoice
from school_project.settings import STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET
from utils.response import create_message, create_response
from utils.utils import assign_user_to_package, get_user_from_token, require_authentication, response_500
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
    return price_id_map.get(subscription_type, None) 

def get_package_by_price_id(subscription_type):
    price_id_map = {
         settings.SINGLE_PACKAGE_PRICE_ID: 'single_teacher',
         settings.BRONZE_TEACHER_PACKAGE_PRICE_ID: 'bronze_teacher',
         settings.SILVER_TEACHER_PACKAGE_PRICE_ID: 'silver_teacher',
         settings.GOLD_TEACHER_PACKAGE_PRICE_ID: 'gold_teacher',
         settings.BRONZE_SCHOOL_PACKAGE_PRICE_ID: 'bronze_school',
         settings.SILVER_SCHOOL_PACKAGE_PRICE_ID: 'silver_school',
         settings.GOLD_SCHOOL_PACKAGE_PRICE_ID: 'gold_school',
         settings.TEST_PRICE_ID:  'test'
    }

    # Return the price ID if the subscription type matches
    return price_id_map.get(subscription_type, None) 

# Separate functions for handling events

def handle_invoice_created(user, invoice):
    
    # Extract the Stripe plan ID from the invoice
    price_id = invoice['lines']['data'][0]['plan']['id']
    # Get the corresponding package
    package_type = get_package_by_price_id(price_id)
    package = Package.objects.get(package_type=package_type)
    assign_user_to_package(user, package.id)
    
    Invoice.objects.create(
        user=user,
        invoice_id=invoice['id'],
        amount=invoice['amount_due'] / 100,  # Stripe uses cents
        currency=invoice['currency'],
        status="created",  
        created_at=invoice['created'],
        pdf_url=invoice.get('invoice_pdf', ''), 
        package_type=package_type
    )
    user.is_subscribed = True
    user.save()


def handle_invoice_payment_succeeded(user, invoice):
    # Extract the Stripe plan ID from the invoice
    price_id = invoice['lines']['data'][0]['plan']['id']
    # Get the corresponding package
    package_type = get_package_by_price_id(price_id)
    # Create a new invoice record for a successful payment (different from invoice created)
    Invoice.objects.create(
        user=user,
        invoice_id=invoice['id'],
        amount=invoice['amount_paid'] / 100,  # Stripe uses cents
        currency=invoice['currency'],
        status='paid',
        payment_date=invoice.get('created'),  # Use Stripe's timestamp for payment success
        pdf_url=invoice.get('invoice_pdf', ''),
        package_type=package_type
    )
    user.is_subscribed = True
    user.save()


def handle_invoice_payment_failed(user, invoice):
    # Extract the Stripe plan ID from the invoice
    price_id = invoice['lines']['data'][0]['plan']['id']
    # Get the corresponding package
    package_type = get_package_by_price_id(price_id)
    # Create a new invoice record for a failed payment (different from invoice created)
    Invoice.objects.create(
        user=user,
        invoice_id=invoice['id'],
        amount=invoice['amount_due'] / 100,  # Stripe uses cents
        currency=invoice['currency'],
        status='failed',
        canceled_at=invoice.get('attempted'),  # Use Stripe's attempt timestamp
        pdf_url=invoice.get('invoice_pdf', ''),
        package_type=package_type
    )
    if user.stripe_subscription_id:
        stripe_subscription_id = user.stripe_subscription_id
        # Cancel the Stripe subscription
        stripe.Subscription.delete(stripe_subscription_id)

        # Optional: Update user record in your database
        user.stripe_subscription_id = None
        
    user.is_subscribed = False
    user.save()
