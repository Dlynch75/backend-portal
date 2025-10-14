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
import smtplib
from email.mime.text import MIMEText
from django.core.mail import EmailMessage
import requests

import requests
from django.core.mail import EmailMessage


def send_notification_email(subject, message, recipients, cv_url=None):
    """
    Send a notification email with optional CV attachment.
    Logs all events and errors for better traceability.
    """
    try:
        print(f"Preparing email to {recipients} | Subject: {subject}")

        email = EmailMessage(
            subject=subject,
            body=message,
            from_email="connect@gulfteachers.com",  # same as login user
            to=recipients,
        )

        # ✅ Try to download and attach CV file if provided
        if cv_url and cv_url != "N/A":
            try:
                print(f"Attempting to attach CV from URL: {cv_url}")
                response = requests.get(cv_url, timeout=10)
                response.raise_for_status()  # raise error for bad responses

                filename = cv_url.split("/")[-1]
                email.attach(filename, response.content, "application/pdf")
                print(f"CV '{filename}' attached successfully.")
            except requests.exceptions.RequestException as e:
                print(f"Failed to download CV from {cv_url}: {str(e)}")

        # ✅ Send the email
        email.send(fail_silently=False)
        print(f"Email successfully sent to: {', '.join(recipients)}")

    except Exception as e:
        print(f"Error sending email to {recipients}: {str(e)}", exc_info=True)