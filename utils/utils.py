from datetime import date
from rest_framework.response import Response
from core.models import CustomUser, Teacher, School, Package, UserPackage
from school_project import settings
from utils.response import create_message
from rest_framework import status
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework import status
from rest_framework.response import Response
import jwt
from rest_framework.exceptions import AuthenticationFailed
from functools import wraps
from django.core.exceptions import ObjectDoesNotExist

def get_user_from_token(request):
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        raise AuthenticationFailed("Authentication credentials were not provided.")

    token = auth_header.split(' ')[1]

    try:
        decoded_token = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id = decoded_token.get('user_id')  # Adjust based on your token structure
        user = CustomUser.objects.get(id=user_id)
        return user

    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None
    except CustomUser.DoesNotExist:
        return None
    
def auth_user(request):
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        raise AuthenticationFailed("Authentication credentials were not provided.")

    token = auth_header.split(' ')[1]

    # Check if token is valid and decode it
    try:
        decoded_token = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id = decoded_token.get('user_id')  # Adjust based on your token structure
        user = CustomUser.objects.get(id=user_id)

        # Optionally check for user status (active, etc.)
        if not user.is_active:
            raise AuthenticationFailed("User is inactive.")

        return user  # Return the authenticated user
    
    except jwt.ExpiredSignatureError:
        raise AuthenticationFailed("Invalid or expired token.")
    except jwt.InvalidTokenError:
        raise AuthenticationFailed("Invalid or expired token.")
    except CustomUser.DoesNotExist:
        raise AuthenticationFailed("User not found.")

        
def response_500(e):
    if e:
        return Response(
            create_message(e, 1002), status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    return Response(create_message([], 1002), status.HTTP_500_INTERNAL_SERVER_ERROR)

def require_authentication(view_func):
    @wraps(view_func)
    def wrapped_view(self, request, *args, **kwargs):
        try:
            user = auth_user(request)  # Extract the authenticated user
            request.user = user  # Attach the user to the request object
        except AuthenticationFailed as e:
            return Response(
                create_message(str(e), 1002),
                status=status.HTTP_401_UNAUTHORIZED
            )
        return view_func(self, request, *args, **kwargs)

    return wrapped_view

def assign_user_to_package(user, package_id):
    """
    Assign a teacher or school to a package. If the user already has a package, it will be removed.
    
    Args:
        user: The user to be assigned, either a Teacher or School instance.
        package_id: The ID of the package to assign the user to.
    
    Returns:
        UserPackage instance if successfully assigned.
    
    Raises:
        ValueError: If an invalid user type or package is provided.
    """
    try:
        package = Package.objects.get(id=package_id)
    except ObjectDoesNotExist:
        raise Exception("Package does not exist.")
    # Remove any previous subscription for the user
    if user.is_teacher:
        UserPackage.objects.filter(teacher=user.teacher).delete()
        user_package = UserPackage.objects.create(teacher=user.teacher, package=package)
        # set user to be subscribed , set apply count rest, and date reset
        user.last_reset_date = date.today()
        user.teacher.applied_count = 0
        user.teacher.save()
        # Mark trial flag if assigning a trial
        if package.package_type == "trial_teacher":
            user.has_used_trial = True
        user.save()
    elif user.is_school:
        UserPackage.objects.filter(school=user.school).delete()
        user_package = UserPackage.objects.create(school=user.school, package=package)
        # set user to be subscribed , set apply count rest, and date reset
        user.school.post_count = 0
        user.last_reset_date = date.today()
        user.school.save()
        # Mark trial flag if assigning a trial
        if package.package_type == "trial_teacher":
            user.has_used_trial = True
        user.save()
    else:
        raise Exception("Invalid user type. Must be a Teacher or School.")

    return user_package


# utils/email.py
import logging
from django.conf import settings
from django.core.mail import EmailMessage

logger = logging.getLogger(__name__)


def friendly_email_send_error(exc):
    message = str(exc)
    lowered = message.lower()
    if '535' in message or 'authentication rejected' in lowered or 'smtpauthenticationerror' in lowered:
        return (
            "We could not send the email right now. Please try again later or contact connect@gulfteachers.com."
        )
    return f"Failed to send email: {message}"


def _get_from_email():
    return (
        getattr(settings, 'DEFAULT_FROM_EMAIL', None)
        or getattr(settings, 'EMAIL_HOST_USER', None)
        or 'connect@gulfteachers.com'
    )


def send_notification_email(subject, message, recipients, cv_url=None):
    from_email = _get_from_email()
    email = EmailMessage(
        subject=subject,
        body=message,
        from_email=from_email,
        to=recipients,
    )

    if cv_url and cv_url != "N/A":
        try:
            from utils.cv_stream import fetch_cv_bytes
            content, _content_type = fetch_cv_bytes(cv_url)
            filename = cv_url.split("/")[-1].split("?")[0] or "cv.pdf"
            email.attach(filename, content, "application/pdf")
        except Exception as e:
            logger.warning("Failed to attach CV from %s: %s", cv_url, e)

    try:
        email.send(fail_silently=False)
        logger.info("Email sent to %s | Subject: %s", recipients, subject)
    except Exception as e:
        logger.exception("Error sending email to %s", recipients)
        raise