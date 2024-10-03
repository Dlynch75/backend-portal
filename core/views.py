from django.db.models import Q
from django.shortcuts import render

# Create your views here.
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from utils.response import create_message, create_response
from utils.utils import  get_user_from_token, response_500
from .models import CustomUser
from .serializers import TeacherSignupSerializer, SchoolSignupSerializer

class UserSignupView(APIView):
    def post(self, request):
        try:
            is_school = request.data.get('is_school')

            if is_school is None:
                raise Exception("The 'is_school' field is required.")

            # Check if email or username already exists
            email = request.data.get('email')
            username = request.data.get('username')
            if CustomUser.objects.filter(Q(email=email) | Q(username=username)).exists():
                raise Exception(
                    "A user with this email or username already exists.")

            # Use the appropriate serializer based on `is_school`
            if is_school:
                serializer = SchoolSignupSerializer(data=request.data)
            else:
                serializer = TeacherSignupSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return create_response(create_message(serializer.data, 1000), status.HTTP_200_OK)
            else:
                raise Exception(serializer.errors)
        except Exception as e:
            return response_500(str(e))


class LoginView(APIView):
    def post(self, request):
        try:
            email = request.data.get('email')
            password = request.data.get('password')

            # Retrieve user by email
            user = CustomUser.objects.filter(email=email).first()

            # Check if user exists and password is correct
            if user is None or not user.check_password(password):
                return Response({
                    "status": 1002,
                    "message": "Invalid email or password.",
                    "data": None
                }, status=status.HTTP_400_BAD_REQUEST)

            # Generate tokens
            refresh = RefreshToken.for_user(user)

            role = 'teacher' if user.is_teacher else 'school'
            user_data = {
                "email": user.email,
                "username": user.username,
                "city": user.city,
                "address": user.address,
                "role": role
            }

            if user.is_teacher:
                user_data["full_name"] = user.teacher.full_name
                user_data["experience_year"] = user.teacher.experience_year
            elif user.is_school:
                user_data["school_name"] = user.school.school_name

            return create_response(create_message({
                "user": user_data,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            }, 1000), status.HTTP_200_OK)


        except Exception as e:
            return response_500(str(e))
