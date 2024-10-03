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

def get_user_from_token(token):
    try:
        # Decode the token and verify its signature
        decoded_token = jwt.decode(
            token,
            settings.SECRET_KEY,  
            algorithms=["HS256"]  
        )
        user_id = decoded_token.get('user_id')  # Adjust based on your token structure
        user = CustomUser.objects.get(id=user_id)
        return user

    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None
    except CustomUser.DoesNotExist:
        return None
    
    
def response_500(e):
    if e:
        return Response(
            create_message(e, 1002), status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    return Response(create_message([], 1002), status.HTTP_500_INTERNAL_SERVER_ERROR)
