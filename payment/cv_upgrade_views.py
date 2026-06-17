import stripe
from django.conf import settings
from rest_framework import status
from rest_framework.views import APIView
from teacher.models import Hire
from utils.response import create_message, create_response
from utils.utils import get_user_from_token, require_authentication, response_500
from .cv_upgrade import (
    build_share_url,
    complete_cv_upgrade_payment,
    get_cv_upgrade_amount,
    get_or_create_guest_order,
    get_or_create_pending_order,
    teacher_has_active_order,
)
from .models import CVUpgradeOrder
from .serializers import CVUpgradeOrderSerializer

stripe.api_key = settings.STRIPE_SECRET_KEY


def cv_upgrade_enabled():
    return bool(getattr(settings, 'CV_UPGRADE_STRIPE_PRICE_ID', ''))


def ensure_stripe_customer(user):
    if not user.stripe_subscription_id:
        customer = stripe.Customer.create(email=user.email)
        user.stripe_subscription_id = customer['id']
        user.save(update_fields=['stripe_subscription_id'])
        return customer['id']
    try:
        stripe.Customer.retrieve(user.stripe_subscription_id)
        return user.stripe_subscription_id
    except stripe.error.InvalidRequestError:
        customer = stripe.Customer.create(email=user.email)
        user.stripe_subscription_id = customer['id']
        user.save(update_fields=['stripe_subscription_id'])
        return customer['id']


def create_checkout_session(order):
    if not cv_upgrade_enabled():
        raise Exception("CV upgrade payments are not configured yet. Please contact support.")

    customer_id = None
    if order.teacher_id:
        customer_id = ensure_stripe_customer(order.teacher)

    params = {
        'payment_method_types': ['card'],
        'mode': 'payment',
        'line_items': [{'price': settings.CV_UPGRADE_STRIPE_PRICE_ID, 'quantity': 1}],
        'success_url': f"{settings.FRONTEND_URL.rstrip('/')}/cv-services/success?token={order.token}",
        'cancel_url': f"{settings.FRONTEND_URL.rstrip('/')}/cv-services/{order.token}",
        'metadata': {
            'type': 'cv_upgrade',
            'order_id': str(order.id),
        },
    }

    if customer_id:
        params['customer'] = customer_id
    elif order.candidate_email:
        params['customer_email'] = order.candidate_email

    session = stripe.checkout.Session.create(**params)
    order.stripe_session_id = session.id
    order.save(update_fields=['stripe_session_id'])
    return session.url


class CVUpgradeCreateLinkView(APIView):
    @require_authentication
    def post(self, request):
        try:
            if not cv_upgrade_enabled():
                raise Exception("CV upgrade service is not available yet.")

            user = get_user_from_token(request)
            hire_id = request.data.get('hire_id')

            if user.is_school and hire_id:
                hire = Hire.objects.select_related('teacher', 'school').get(pk=hire_id)
                if hire.school_id != user.id:
                    raise Exception("You can only create links for your own applicants.")
                teacher = hire.teacher
                if teacher_has_active_order(teacher):
                    raise Exception("This applicant already has a CV upgrade in progress.")
                order = get_or_create_pending_order(
                    teacher=teacher,
                    school=user.school,
                    candidate_email=teacher.email,
                    candidate_name=teacher.full_name,
                )
            elif user.is_teacher:
                if teacher_has_active_order(user.teacher):
                    raise Exception("You already have a CV upgrade in progress.")
                order = get_or_create_pending_order(teacher=user.teacher)
            else:
                raise Exception("Only teachers or schools can create CV upgrade links.")

            serializer = CVUpgradeOrderSerializer(order)
            return create_response(create_message(serializer.data, 1000), status.HTTP_201_CREATED)
        except Hire.DoesNotExist:
            return response_500("Applicant not found.")
        except Exception as e:
            return response_500(str(e))


class CVUpgradeStatusView(APIView):
    @require_authentication
    def get(self, request):
        try:
            user = get_user_from_token(request)
            if not user.is_teacher:
                raise Exception("Only teachers can view CV upgrade status.")

            order = CVUpgradeOrder.objects.filter(teacher=user.teacher).order_by('-created_at').first()
            if not order:
                return create_response(create_message(None, 1000), status.HTTP_200_OK)

            serializer = CVUpgradeOrderSerializer(order)
            return create_response(create_message(serializer.data, 1000), status.HTTP_200_OK)
        except Exception as e:
            return response_500(str(e))


class CVUpgradePublicView(APIView):
    def get(self, request, token):
        try:
            order = CVUpgradeOrder.objects.get(token=token)
            serializer = CVUpgradeOrderSerializer(order)
            data = serializer.data
            data['service_enabled'] = cv_upgrade_enabled()
            data['amount'] = float(order.amount)
            return create_response(create_message(data, 1000), status.HTTP_200_OK)
        except CVUpgradeOrder.DoesNotExist:
            return response_500("This CV upgrade link is invalid or has expired.")
        except Exception as e:
            return response_500(str(e))


class CVUpgradeCheckoutView(APIView):
    def get(self, request, token):
        try:
            order = CVUpgradeOrder.objects.get(token=token)
            if order.status != 'pending_payment':
                raise Exception("This link has already been paid or is no longer active.")
            redirect_url = create_checkout_session(order)
            return create_response(create_message({'redirectUrl': redirect_url}, 1000), status.HTTP_200_OK)
        except CVUpgradeOrder.DoesNotExist:
            return response_500("This CV upgrade link is invalid.")
        except Exception as e:
            return response_500(str(e))


class CVUpgradeGuestCheckoutView(APIView):
    def post(self, request):
        try:
            if not cv_upgrade_enabled():
                raise Exception("CV upgrade payments are not configured yet. Please contact support.")

            candidate_name = (request.data.get('candidate_name') or '').strip()
            candidate_email = (request.data.get('candidate_email') or '').strip()
            order = get_or_create_guest_order(candidate_email, candidate_name)
            redirect_url = create_checkout_session(order)
            return create_response(
                create_message({'redirectUrl': redirect_url, 'token': str(order.token)}, 1000),
                status.HTTP_200_OK,
            )
        except Exception as e:
            return response_500(str(e))


class CVUpgradeCheckoutAuthenticatedView(APIView):
    @require_authentication
    def get(self, request):
        try:
            user = get_user_from_token(request)
            if not user.is_teacher:
                raise Exception("Only teachers can purchase CV upgrade.")

            if teacher_has_active_order(user.teacher):
                raise Exception("You already have a CV upgrade in progress.")

            order = get_or_create_pending_order(teacher=user.teacher)
            redirect_url = create_checkout_session(order)
            return create_response(create_message({'redirectUrl': redirect_url}, 1000), status.HTTP_200_OK)
        except Exception as e:
            return response_500(str(e))
