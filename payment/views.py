from django.shortcuts import render
from rest_framework.views import APIView
import stripe
from django.conf import settings
from django.shortcuts import redirect
from django.http import JsonResponse
from core.models import CustomUser, Package, UserPackage
from payment.helper import get_price_id
from payment.models import Invoice
from school_project.settings import STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET
from utils.response import create_message, create_response
from utils.utils import get_user_from_token, require_authentication, response_500
import stripe
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
stripe.api_key = STRIPE_SECRET_KEY
from rest_framework import status

# Create your views here.

class CreatePaymentSessionView(APIView):
    @require_authentication
    def get(self, request, pk):
        user = get_user_from_token(request)
        domain_url = "http://localhost:3000/"  # Your domain URL
        package_id = pk
        package = Package.objects.get(id=package_id)
        price_id = get_price_id(package.package_type)

        if not user or not user.stripe_subscription_id:
            try:
                customer = stripe.Customer.create(
                    email=user.email,
                )
                user.stripe_subscription_id = customer['id']
                user.save()
            except Exception as e:
                return JsonResponse({'error': f"Customer creation failed: {str(e)}"})

        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                mode='subscription',
                line_items=[
                    {
                        'price': price_id,
                        'quantity': 1,
                    },
                ],
                success_url=domain_url + 'success/',
                cancel_url=domain_url + 'cancel/',
                customer=user.stripe_subscription_id,
            )
            redirect_url = checkout_session.url  # Get the URL directly from the session object
            
            return create_response(create_message({'redirectUrl': redirect_url}, 1000), status.HTTP_200_OK)

        except Exception as e:
            return response_500(str(e))


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except ValueError as e:
        return HttpResponse(status=400)  # Invalid payload
    except stripe.error.SignatureVerificationError as e:
        return HttpResponse(status=400)  # Invalid signature

    data_object = event['data']['object']
    customer_id = data_object.get('customer')
    user = CustomUser.objects.get(stripe_customer_id=customer_id)  # Adjust based on your user model

    if event['type'] == 'invoice.created':
        # Handle invoice creation
        invoice = data_object
        Invoice.objects.create(
            user=user,
            invoice_id=invoice['id'],
            amount=invoice['amount_due'] / 100,  # Convert cents to dollars
            currency=invoice['currency'],
            status=invoice['status'],
            created_at=invoice['created'],
        )

    elif event['type'] == 'invoice.payment_succeeded':
        invoice = data_object
        Invoice.objects.filter(invoice_id=invoice['id']).update(
            status='paid',
            payment_date=invoice['paid_at'],
        )
        user.is_subscribed = True
        user.save()

    elif event['type'] == 'invoice.payment_failed':
        invoice = data_object
        Invoice.objects.filter(invoice_id=invoice['id']).update(
            status='failed',
            canceled_at=invoice['attempted']  # Assuming this field is relevant
        )
        user.is_subscribed = False
        user.save()

    elif event['type'] == 'customer.subscription.deleted':
        subscription = data_object
        user.is_subscribed = False
        user.save()
        # delete subscribtion
        UserPackage.objects.filter(user=user).delete() if UserPackage.objects.filter(user=user).exists() else None

    return JsonResponse({'status': 'success'})