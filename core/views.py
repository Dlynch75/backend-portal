from django.db.models import Q
from django.shortcuts import render
# Create your views here.
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from utils.response import create_message, create_response
from utils.utils import  assign_user_to_package, get_user_from_token, require_authentication, response_500, send_notification_email
from .models import CustomUser, Package, School, Teacher
from .serializers import PackageSerializer, TeacherSerializer, SchoolSerializer
import cloudinary.uploader
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings


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
                raise Exception("A user with this email or username already exists.")

            # Use the appropriate serializer based on `is_school`
            if is_school:
                serializer = SchoolSerializer(data=request.data)
                if serializer.is_valid():
                    logo = request.FILES.get('school_logo')
                    if logo:
                        cloudinary_response = cloudinary.uploader.upload(logo)
                        # Get the URL of the uploaded logo
                        image_url = cloudinary_response['secure_url']
                        # Save the logo URL to the serializer's validated data
                        serializer.validated_data['school_logo'] = image_url
                    
                    user = serializer.save()
                    # Send welcome email
                    try:
                        welcome_subject = "Welcome to Gulf Teachers!"
                        welcome_message = f"""
Hello {user.school.school_name if hasattr(user, 'school') else user.username},

Welcome to Gulf Teachers! We're excited to have you join our platform.

Your account has been successfully created. You can now:
- Browse and post job opportunities
- Connect with talented teachers
- Access exclusive resources

If you have any questions, feel free to reach out to us at connect@gulfteachers.com.

Best regards,
The Gulf Teachers Team
"""
                        send_notification_email(welcome_subject, welcome_message, [user.email])
                    except Exception as e:
                        print(f"Failed to send welcome email: {str(e)}")
                    
                    return Response({'message': 'User created successfully!', 'data': serializer.data}, status=status.HTTP_201_CREATED)
                else:
                    raise Exception(serializer.errors)
            else:
                serializer = TeacherSerializer(data=request.data)
                if serializer.is_valid():
                    try:
                        user = serializer.save()
                        try:
                            welcome_subject = "Welcome to Gulf Teachers!"
                            welcome_message = f"""
Hello {user.teacher.full_name if hasattr(user, 'teacher') else user.username},

Welcome to Gulf Teachers! We're excited to have you join our platform.

Your account has been successfully created. You can now:
- Browse and apply to teaching positions
- Create your professional profile
- Connect with schools across the Gulf region

If you have any questions, feel free to reach out to us at connect@gulfteachers.com.

Best regards,
The Gulf Teachers Team
"""
                            send_notification_email(welcome_subject, welcome_message, [user.email])
                        except Exception as e:
                            print(f"Failed to send welcome email: {str(e)}")
                        
                        return Response({'message': 'User created successfully!', 'data': serializer.data}, status=status.HTTP_201_CREATED)
                    except Exception as save_error:
                        import traceback
                        error_details = traceback.format_exc()
                        print(f"Error saving teacher: {str(save_error)}")
                        print(f"Traceback: {error_details}")
                        return Response({'error': f'Failed to create user: {str(save_error)}', 'details': str(save_error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                else:
                    return Response({'error': 'Validation failed', 'details': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Signup error: {str(e)}")
            print(f"Traceback: {error_details}")
            return Response({'error': str(e), 'details': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LoginView(APIView):
    def post(self, request):
        try:
            email = request.data.get('email')
            password = request.data.get('password')
            # Retrieve user by email
            user = CustomUser.objects.filter(email=email).first()
            # Check if user exists and password is correct
            if user is None or not user.check_password(password):
                raise Exception("Email or Password Invalid")
            
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
                print(user_data.data)
            
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

                # Handle logo upload if present
                if 'school_logo' in request.FILES:
                    file = request.FILES['school_logo']
                    cloudinary_response = cloudinary.uploader.upload(file)
                    image_url = cloudinary_response['secure_url']
                    request.data['school_logo'] = image_url 

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
    def get(self, request):
        try:
            # Get the user from the token
            user = get_user_from_token(request)

            # Use the appropriate serializer based on `is_school` or `is_teacher`
            if user.is_teacher:
                serializer = TeacherSerializer(user.teacher, many=False)
            elif user.is_school:
                serializer = SchoolSerializer(user.school, many=False)
            else:
                serializer = None
                
            return create_response(create_message(serializer.data, 1000), status.HTTP_200_OK)
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


class PasswordResetRequestView(APIView):
    """Request password reset - sends email with reset link"""
    def post(self, request):
        try:
            email = request.data.get('email')
            if not email:
                raise Exception("Email is required.")
            
            try:
                user = CustomUser.objects.get(email=email)
            except CustomUser.DoesNotExist:
                # Don't reveal if email exists for security
                return create_response(create_message("If an account exists with this email, a password reset link has been sent.", 1000), status.HTTP_200_OK)
            
            # Generate token
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            # Create reset link
            frontend_url = "https://teacher-portal-omega.vercel.app"  # Update with your frontend URL
            reset_link = f"{frontend_url}/reset-password?uid={uid}&token={token}"
            
            # Send email
            subject = "Password Reset Request - Gulf Teachers"
            message = f"""
Hello {user.username},

You requested to reset your password for your Gulf Teachers account.

Click the link below to reset your password:
{reset_link}

This link will expire in 24 hours.

If you didn't request this password reset, please ignore this email.

Best regards,
The Gulf Teachers Team
"""
            try:
                send_notification_email(subject, message, [user.email])
                return create_response(create_message("Password reset link has been sent to your email.", 1000), status.HTTP_200_OK)
            except Exception as e:
                raise Exception(f"Failed to send email: {str(e)}")
                
        except Exception as e:
            return response_500(str(e))


class PasswordResetConfirmView(APIView):
    """Confirm password reset with token"""
    def post(self, request):
        try:
            uid = request.data.get('uid')
            token = request.data.get('token')
            new_password = request.data.get('new_password')
            
            if not all([uid, token, new_password]):
                raise Exception("UID, token, and new_password are required.")
            
            # Decode user ID
            try:
                user_id = force_str(urlsafe_base64_decode(uid))
                user = CustomUser.objects.get(pk=user_id)
            except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
                raise Exception("Invalid reset link.")
            
            # Verify token
            if not default_token_generator.check_token(user, token):
                raise Exception("Invalid or expired reset token.")
            
            # Set new password
            user.set_password(new_password)
            user.save()
            
            return create_response(create_message("Password has been reset successfully.", 1000), status.HTTP_200_OK)
            
        except Exception as e:
            return response_500(str(e))