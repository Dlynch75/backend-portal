from django.shortcuts import render
from rest_framework.views import APIView
import stripe
from django.conf import settings
from django.shortcuts import redirect
from django.http import JsonResponse
from core.models import CustomUser, Package, UserPackage
from payment.helper import get_price_id, handle_invoice_created, handle_invoice_payment_failed, handle_invoice_payment_succeeded, handle_subscription_deleted
from payment.models import Invoice
from school_project.settings import STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET
from utils.response import create_message, create_response
from utils.utils import get_user_from_token, require_authentication, response_500
import stripe
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from django.core.exceptions import ObjectDoesNotExist

stripe.api_key = STRIPE_SECRET_KEY


class CreatePaymentSessionView(APIView):
    @require_authentication
    def get(self, request, pk):
        user = get_user_from_token(request)
        domain_url = "https://teacher-portal-omega.vercel.app"  # Your domain URL
        package_id = pk
        package = Package.objects.get(id=package_id)
        price_id = get_price_id(package.package_type)
        
        # Get promo code from query parameters
        promo_code = request.query_params.get('promo_code', None)

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
            # Build checkout session parameters
            checkout_params = {
                'payment_method_types': ['card'],
                'mode': 'subscription',
                'line_items': [
                    {
                        'price': price_id,
                        'quantity': 1,
                    },
                ],
                'success_url': domain_url + f'/dashboard/success',
                'cancel_url': domain_url + 'failure/',
                'customer': user.stripe_subscription_id,
            }
            
            # Add promo code if provided
            if promo_code:
                try:
                    # Retrieve the promotion code by code string
                    promo_codes = stripe.PromotionCode.list(active=True, code=promo_code, limit=1)
                    if promo_codes.data:
                        checkout_params['discounts'] = [{'promotion_code': promo_codes.data[0].id}]
                        
                        # Check if discount is 100% - if so, skip payment method requirement
                        coupon = stripe.Coupon.retrieve(promo_codes.data[0].coupon.id)
                        if coupon.percent_off == 100:
                            checkout_params['payment_method_collection'] = 'if_required'
                    else:
                        return create_response(create_message({'error': 'Invalid promo code'}, 1002), status.HTTP_400_BAD_REQUEST)
                except stripe.error.StripeError as e:
                    return create_response(create_message({'error': f'Promo code error: {str(e)}'}, 1002), status.HTTP_400_BAD_REQUEST)
            
            checkout_session = stripe.checkout.Session.create(**checkout_params)
            redirect_url = checkout_session.url  # Get the URL directly from the session object
            
            return create_response(create_message({'redirectUrl': redirect_url}, 1000), status.HTTP_200_OK)

        except Exception as e:
            return response_500(str(e))


@csrf_exempt
def stripe_webhook(request):
    if request.method != 'POST':
        return HttpResponse(status=405)  # Method not allowed

    if not request.body:
        return HttpResponse(status=400, content="No payload provided")

    try:
        payload = request.body.decode('utf-8')
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        
        if not sig_header:
            return HttpResponse(status=400, content="Missing Stripe signature")

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, STRIPE_WEBHOOK_SECRET
            )
        except ValueError:
            return HttpResponse(status=400, content="Invalid payload")
        except stripe.error.SignatureVerificationError:
            return HttpResponse(status=400, content="Invalid signature")

        data_object = event.get('data', {}).get('object')
        if not data_object:
            return HttpResponse(status=400, content="Missing event data")

        customer_id = data_object.get('customer')
        if not customer_id:
            return HttpResponse(status=400, content="Missing customer ID")

        try:
            user = CustomUser.objects.get(stripe_subscription_id=customer_id)
        except ObjectDoesNotExist:
            return HttpResponse(status=404, content="User not found ")
        
        
        # Process based on event type
        if event['type'] == 'invoice.created':
            handle_invoice_created(user, data_object)

        elif event['type'] == 'invoice.payment_succeeded':
            handle_invoice_payment_succeeded(user, data_object)

        elif event['type'] == 'invoice.payment_failed':
            handle_invoice_payment_failed(user, data_object)

        elif event['type'] == 'customer.subscription.deleted':
            handle_subscription_deleted(user, data_object)

        return JsonResponse({'status': 'success'})

    except Exception as e:
        return HttpResponse(status=500, content=e)