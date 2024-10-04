from rest_framework.response import Response
from core.models import CustomUser
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