from django.db.models import Q
from django.shortcuts import render

# Create your views here.
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from utils.response import create_message, create_response
from utils.utils import  assign_user_to_package, get_user_from_token, require_authentication, response_500
from .models import CustomUser, Package, School, Teacher
from .serializers import PackageSerializer, TeacherSerializer, SchoolSerializer

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
                serializer = SchoolSerializer(data=request.data)
            else:
                serializer = TeacherSerializer(data=request.data)
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
                raise Exception("Email or Passowrd Invalied")
            
            # Generate tokens
            refresh = RefreshToken.for_user(user)
            role = 'teacher' if user.is_teacher else 'school'
            user_data = {}
            
            if user.is_teacher:
                teacher = Teacher.objects.get(id=user.id)
                user_data = TeacherSerializer(teacher,many=False)
            elif user.is_school:
                school = School.objects.get(id=user.id)
                user_data = SchoolSerializer(school,many=False)
            
            return create_response(create_message({
                "user": user_data.data,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            }, 1000), status.HTTP_200_OK)


        except Exception as e:
            return response_500(str(e))

class UserProfileView(APIView):
    @require_authentication
    def put(self, request):
        try:
            # Get the user from the token
            user = get_user_from_token(request)

            # Use the appropriate serializer based on `is_school` or `is_teacher`
            if user.is_teacher:
                serializer = TeacherSerializer(user.teacher, data=request.data, partial=True)
            elif user.is_school:
                serializer = SchoolSerializer(user.school, data=request.data, partial=True)
            else:
                serializer = None
            
            if serializer is not None and serializer.is_valid():
                serializer.save()
                return create_response(create_message(serializer.data, 1000), status.HTTP_200_OK)
            else:
                raise Exception(serializer.errors if serializer else "Invalid user role.")
        except Exception as e:
            return response_500(str(e))
        
    @require_authentication
    def delete(self, request):
        try:
            # Get the user from the token
            user = get_user_from_token(request)

            # Delete the user
            user.delete()
            return create_response(create_message("User profile deleted successfully.", 1000), status.HTTP_200_OK)
        except Exception as e:
            return response_500(str(e))
class PackageListView(APIView):
    @require_authentication
    def get(self, request):
        try:
            user = get_user_from_token(request)
            if user.is_teacher:
                packages = Package.objects.filter(package_for='teacher')
            elif user.is_school:
                packages = Package.objects.filter(package_for='school')
            else:
                raise Exception("Invalid User")
            
            serializer = PackageSerializer(packages, many=True)
            return create_response(create_message(serializer.data, 1000), status.HTTP_200_OK)
        except Exception as e:
            return response_500(str(e))
        
class ApplyPackageView(APIView): 
    @require_authentication
    def post(self, request, pk):
        try:
            user = get_user_from_token(request)
            # Assign package to the user and remove previous subscription if any
            user_package = assign_user_to_package(user, pk)
            return create_response(create_message("Package Applied", 1000), status.HTTP_200_OK)
        except Exception as e:
            return response_500(str(e))