from django.shortcuts import render
from rest_framework.views import APIView
import stripe
from django.conf import settings
from django.shortcuts import redirect
from django.http import JsonResponse
from core.models import CustomUser, Package, UserPackage
from payment.helper import get_price_id, handle_invoice_created, handle_invoice_payment_failed, handle_invoice_payment_succeeded, handle_subscription_deleted
from payment.models import Invoice
from school_project.settings import (
    STRIPE_SECRET_KEY,
    STRIPE_WEBHOOK_SECRET,
    FEATURED_JOB_STRIPE_PRICE_ID,
    FEATURED_JOB_DURATION_DAYS,
    FRONTEND_URL,
)
from school.models import JobPosting
from payment.featured_job import activate_job_feature
from payment.cv_upgrade import complete_cv_upgrade_payment
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
        else:
            try:
                stripe.Customer.retrieve(user.stripe_subscription_id)
            except stripe.error.InvalidRequestError as e:
                if 'No such customer' in str(e) or 'similar object exists in test mode' in str(e):
                    try:
                        customer = stripe.Customer.create(
                            email=user.email,
                        )
                        user.stripe_subscription_id = customer['id']
                        user.save()
                    except Exception as create_error:
                        return JsonResponse({'error': f"Customer creation failed: {str(create_error)}"})
                else:
                    return JsonResponse({'error': f"Stripe error: {str(e)}"})

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
                    # Normalize promo code (trim whitespace)
                    promo_code = promo_code.strip()
                    promo_code_upper = promo_code.upper()
                    
                    # Map of allowed codes (uppercase -> correct case for Stripe)
                    promo_code_map = {
                        'GULFTEACHERS26': 'GulfTeachers26',
                        'GT50': 'GT50',
                        'GT30': 'GT30'
                    }
                    
                    # Validate promo code against allowed codes
                    if promo_code_upper not in promo_code_map:
                        return create_response(create_message({'error': 'Invalid promo code'}, 1002), status.HTTP_400_BAD_REQUEST)
                    
                    # Get correct case for Stripe lookup
                    stripe_promo_code = promo_code_map[promo_code_upper]
                    
                    # Check if package is for teachers (promo codes are only for teacher packages)
                    if package.package_for != 'teacher':
                        return create_response(create_message({'error': 'This promo code is only valid for teacher packages'}, 1002), status.HTTP_400_BAD_REQUEST)
                    
                    # GT30 is only valid for gold_teacher package
                    if promo_code_upper == 'GT30' and package.package_type != 'gold_teacher':
                        return create_response(create_message({'error': 'GT30 promo code is only valid for Gold Teacher package'}, 1002), status.HTTP_400_BAD_REQUEST)
                    
                    # Retrieve the promotion code by code string from Stripe (use correct case)
                    promo_codes = stripe.PromotionCode.list(active=True, code=stripe_promo_code, limit=1)
                    if promo_codes.data:
                        checkout_params['discounts'] = [{'promotion_code': promo_codes.data[0].id}]
                        
                        # Check if discount is 100% - if so, skip payment method requirement
                        coupon = stripe.Coupon.retrieve(promo_codes.data[0].coupon.id)
                        if coupon.percent_off == 100:
                            checkout_params['payment_method_collection'] = 'if_required'
                    else:
                        return create_response(create_message({'error': 'Promo code not found in Stripe. Please contact support.'}, 1002), status.HTTP_400_BAD_REQUEST)
                except stripe.error.StripeError as e:
                    return create_response(create_message({'error': f'Promo code error: {str(e)}'}, 1002), status.HTTP_400_BAD_REQUEST)
            
            checkout_session = stripe.checkout.Session.create(**checkout_params)
            redirect_url = checkout_session.url  # Get the URL directly from the session object
            
            return create_response(create_message({'redirectUrl': redirect_url}, 1000), status.HTTP_200_OK)

        except Exception as e:
            return response_500(str(e))


class CreateFeaturedJobPaymentView(APIView):
    @require_authentication
    def get(self, request, job_id):
        try:
            user = get_user_from_token(request)
            if not user.is_school:
                raise Exception("Only schools can feature job listings.")

            if not FEATURED_JOB_STRIPE_PRICE_ID:
                raise Exception("Featured job payments are not configured yet. Please contact support.")

            job = JobPosting.objects.get(pk=job_id, school=user.school)
            if job.status != 'open':
                raise Exception("Only open jobs can be featured.")

            if not user.stripe_subscription_id:
                customer = stripe.Customer.create(email=user.email)
                user.stripe_subscription_id = customer['id']
                user.save()
            else:
                try:
                    stripe.Customer.retrieve(user.stripe_subscription_id)
                except stripe.error.InvalidRequestError:
                    customer = stripe.Customer.create(email=user.email)
                    user.stripe_subscription_id = customer['id']
                    user.save()

            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                mode='payment',
                line_items=[{'price': FEATURED_JOB_STRIPE_PRICE_ID, 'quantity': 1}],
                success_url=f"{FRONTEND_URL.rstrip('/')}/dashboard/success?featured_job={job_id}",
                cancel_url=f"{FRONTEND_URL.rstrip('/')}/dashboard/jobs",
                customer=user.stripe_subscription_id,
                metadata={
                    'type': 'featured_job',
                    'job_id': str(job_id),
                    'duration_days': str(FEATURED_JOB_DURATION_DAYS),
                },
            )

            return create_response(
                create_message({'redirectUrl': checkout_session.url}, 1000),
                status.HTTP_200_OK,
            )
        except JobPosting.DoesNotExist:
            return response_500("Job not found or you do not have permission.")
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

        if event['type'] == 'checkout.session.completed':
            session = data_object
            metadata = session.get('metadata') or {}
            if metadata.get('type') == 'featured_job' and metadata.get('job_id'):
                duration_days = int(metadata.get('duration_days', FEATURED_JOB_DURATION_DAYS))
                activate_job_feature(metadata['job_id'], duration_days)
                return JsonResponse({'status': 'success'})
            if metadata.get('type') == 'cv_upgrade' and metadata.get('order_id'):
                customer_details = session.get('customer_details') or {}
                complete_cv_upgrade_payment(
                    metadata['order_id'],
                    session.get('id'),
                    customer_email=customer_details.get('email'),
                    customer_name=customer_details.get('name'),
                )
                return JsonResponse({'status': 'success'})
            if session.get('mode') == 'payment':
                return JsonResponse({'status': 'success'})

        customer_id = data_object.get('customer')
        if not customer_id:
            return HttpResponse(status=400, content="Missing customer ID")

        try:
            user = CustomUser.objects.get(stripe_subscription_id=customer_id)
        except ObjectDoesNotExist:
            return HttpResponse(status=404, content="User not found ")

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