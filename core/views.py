from django.db.models import Q
from django.shortcuts import render
# Create your views here.
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from utils.response import create_message, create_response
from utils.utils import  assign_user_to_package, get_user_from_token, require_authentication, response_500, send_notification_email
from .email_utils import send_user_verification_email, can_resend_verification, mark_verification_resent
from utils.feature_flags import is_teacher_application_paywall_enabled, is_email_verification_enabled
from .models import CustomUser, Package, School, Teacher
from .serializers import PackageSerializer, TeacherSerializer, SchoolSerializer
from utils.cloudinary_upload import upload_teacher_cv
from utils.cv_stream import fetch_cv_bytes, resolve_cv_view_url
import cloudinary.uploader
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
from django.http import HttpResponse
from school.models import JobPosting
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def parse_bool(value):
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip().lower() in ('true', '1', 'yes')
    return bool(value)


class UserSignupView(APIView):
    def post(self, request):
        try:
            is_school = parse_bool(request.data.get('is_school'))

            if request.data.get('is_school') is None and request.data.get('is_teacher') is None:
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
                    try:
                        send_user_verification_email(user)
                    except Exception as e:
                        print(f"Failed to send verification email: {str(e)}")
                    
                    return Response({'message': 'User created successfully!', 'data': serializer.data}, status=status.HTTP_201_CREATED)
                else:
                    raise Exception(serializer.errors)
            else:
                serializer = TeacherSerializer(data=request.data)
                if serializer.is_valid():
                    try:
                        cv = request.FILES.get('cv')
                        if cv:
                            try:
                                cloudinary_response = upload_teacher_cv(cv)
                                serializer.validated_data['cv_url'] = cloudinary_response.get('secure_url')
                            except Exception as upload_error:
                                raise Exception(f"CV upload failed: {str(upload_error)}")
                        user = serializer.save()
                        try:
                            send_user_verification_email(user)
                        except Exception as e:
                            print(f"Failed to send verification email: {str(e)}")
                        
                        return Response({'message': 'User created successfully!', 'data': serializer.data}, status=status.HTTP_201_CREATED)
                    except Exception as save_error:
                        import traceback
                        error_details = traceback.format_exc()
                        print(f"Error saving teacher: {str(save_error)}")
                        print(f"Traceback: {error_details}")
                        error_msg = str(save_error)
                        return create_response(create_message(error_msg, 1002), status.HTTP_500_INTERNAL_SERVER_ERROR)
                else:
                    error_list = []
                    for field, errors in serializer.errors.items():
                        if isinstance(errors, list):
                            for error in errors:
                                field_name = field.replace('_', ' ').title()
                                error_list.append(f"{field_name}: {error}")
                        else:
                            field_name = field.replace('_', ' ').title()
                            error_list.append(f"{field_name}: {errors}")
                    error_message = "; ".join(error_list) if error_list else "Validation failed. Please check all required fields."
                    return Response({
                        'message': error_message,
                        'data': error_message,
                        'errors': serializer.errors
                    }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Signup error: {str(e)}")
            print(f"Traceback: {error_details}")
            error_msg = str(e)
            return Response({
                'message': error_msg,
                'data': error_msg,
                'error': error_msg,
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
            
            # Check if email is verified (warn but don't block)
            email_verified = user.email_verified
            
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
                "email_verified": email_verified,
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
                teacher_data = {key: request.data.get(key) for key in request.data}
                if 'cv' in request.FILES:
                    cloudinary_response = upload_teacher_cv(request.FILES['cv'])
                    teacher_data['cv_url'] = cloudinary_response.get('secure_url')
                for key in ('cv', 'password', 'is_school', 'is_teacher', 'packages', 'is_subscribed', 'has_used_trial'):
                    teacher_data.pop(key, None)
                serializer = TeacherSerializer(user.teacher, data=teacher_data, partial=True)
            elif user.is_school:
                school_data = {key: request.data.get(key) for key in request.data}
                if 'school_logo' in request.FILES:
                    cloudinary_response = cloudinary.uploader.upload(request.FILES['school_logo'])
                    school_data['school_logo'] = cloudinary_response['secure_url']
                serializer = SchoolSerializer(user.school, data=school_data, partial=True)
            else:
                serializer = None

            if serializer is None:
                raise Exception("Invalid user role.")
            if not serializer.is_valid():
                raise Exception(serializer.errors)
            serializer.save()
            return create_response(create_message(serializer.data, 1000), status.HTTP_200_OK)
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


class TeacherCvView(APIView):
    @require_authentication
    def get(self, request):
        try:
            user = request.user
            if not user.is_teacher:
                raise Exception("Only teachers can access this CV.")
            cv_url = user.teacher.cv_url
            if not cv_url:
                raise Exception("No CV on file.")

            if request.query_params.get('format') == 'url':
                return create_response(
                    create_message({'url': resolve_cv_view_url(cv_url)}, 1000),
                    status.HTTP_200_OK,
                )

            content, content_type = fetch_cv_bytes(cv_url)
            http_response = HttpResponse(content, content_type=content_type)
            http_response['Content-Disposition'] = 'inline; filename="cv.pdf"'
            return http_response
        except Exception as e:
            logger.exception("Teacher CV view failed")
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
            frontend_url = "https://www.gulfteachers.com"  # Update with your frontend URL
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


class AppConfigView(APIView):
    def get(self, request):
        from django.conf import settings
        return create_response(
            create_message(
                {
                    "teacher_application_paywall_enabled": is_teacher_application_paywall_enabled(),
                    "email_verification_enabled": is_email_verification_enabled(),
                    "cv_upgrade_enabled": bool(getattr(settings, 'CV_UPGRADE_STRIPE_PRICE_ID', '')),
                    "cv_upgrade_amount": getattr(settings, 'CV_UPGRADE_AMOUNT', 19.99),
                },
                1000,
            ),
            status.HTTP_200_OK,
        )


class EmailResendVerificationView(APIView):
    """Resend email verification link"""
    def post(self, request):
        try:
            if not is_email_verification_enabled():
                return create_response(
                    create_message("Email verification is temporarily disabled. You can log in without verifying.", 1000),
                    status.HTTP_200_OK,
                )

            email = request.data.get('email', '').strip().lower()
            if not email:
                raise Exception("Email is required.")

            generic_message = "If an account exists with this email and is not yet verified, a verification link has been sent."

            try:
                user = CustomUser.objects.get(email__iexact=email)
            except CustomUser.DoesNotExist:
                return create_response(create_message(generic_message, 1000), status.HTTP_200_OK)

            if user.email_verified:
                return create_response(create_message("This email is already verified. You can log in.", 1000), status.HTTP_200_OK)

            if not can_resend_verification(email):
                return create_response(
                    create_message("A verification email was sent recently. Please wait a minute before requesting another.", 1002),
                    status.HTTP_429_TOO_MANY_REQUESTS
                )

            try:
                send_user_verification_email(user)
                mark_verification_resent(email)
                return create_response(create_message(generic_message, 1000), status.HTTP_200_OK)
            except Exception as e:
                logger.exception("Resend verification failed for %s", email)
                raise Exception(f"Failed to send email: {str(e)}")

        except Exception as e:
            return response_500(str(e))


class EmailVerificationView(APIView):
    """Verify user email with token"""
    def post(self, request):
        try:
            uid = request.data.get('uid')
            token = request.data.get('token')
            
            if not all([uid, token]):
                raise Exception("UID and token are required.")
            
            # Decode user ID
            try:
                user_id = force_str(urlsafe_base64_decode(uid))
                user = CustomUser.objects.get(pk=user_id)
            except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
                raise Exception("Invalid verification link.")
            
            # Verify token
            if not default_token_generator.check_token(user, token):
                raise Exception("Invalid or expired verification token.")
            
            # Mark email as verified
            user.email_verified = True
            user.save()
            
            return create_response(create_message("Email verified successfully. You can now log in.", 1000), status.HTTP_200_OK)
            
        except Exception as e:
            return response_500(str(e))


class ContactView(APIView):
    """Handle contact form submissions"""
    def post(self, request):
        try:
            name = request.data.get('name')
            email = request.data.get('email')
            subject = request.data.get('subject')
            message = request.data.get('message')
            
            if not all([name, email, subject, message]):
                raise Exception("All fields are required: name, email, subject, message.")
            
            # Send email to connect@gulfteachers.com
            email_subject = f"Contact Form: {subject}"
            email_message = f"""
You have received a new contact form submission from Gulf Teachers website.

Name: {name}
Email: {email}
Subject: {subject}

Message:
{message}

---
This email was sent from the contact form on www.gulfteachers.com
"""
            try:
                send_notification_email(email_subject, email_message, ['connect@gulfteachers.com'])
                return create_response(create_message("Thank you for contacting us! We'll get back to you soon.", 1000), status.HTTP_200_OK)
            except Exception as e:
                raise Exception(f"Failed to send email: {str(e)}")
                
        except Exception as e:
            return response_500(str(e))


class SitemapView(APIView):
    """Generate dynamic XML sitemap with all active job postings"""
    def get(self, request):
        try:
            # Get all active job postings
            active_jobs = JobPosting.objects.filter(status='open').order_by('-created_at')
            
            # Get current date for lastmod
            current_date = datetime.now().strftime('%Y-%m-%d')
            
            # Start building XML
            xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
            xml_content += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
            xml_content += '        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
            xml_content += '        xsi:schemaLocation="http://www.sitemaps.org/schemas/sitemap/0.9\n'
            xml_content += '        http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd">\n\n'
            
            # Homepage
            xml_content += '  <!-- Homepage -->\n'
            xml_content += '  <url>\n'
            xml_content += '    <loc>https://www.gulfteachers.com/</loc>\n'
            xml_content += f'    <lastmod>{current_date}</lastmod>\n'
            xml_content += '    <changefreq>daily</changefreq>\n'
            xml_content += '    <priority>1.0</priority>\n'
            xml_content += '  </url>\n\n'
            
            # Jobs Page
            xml_content += '  <!-- Jobs Page -->\n'
            xml_content += '  <url>\n'
            xml_content += '    <loc>https://www.gulfteachers.com/jobs</loc>\n'
            xml_content += f'    <lastmod>{current_date}</lastmod>\n'
            xml_content += '    <changefreq>daily</changefreq>\n'
            xml_content += '    <priority>0.9</priority>\n'
            xml_content += '  </url>\n\n'
            
            # Contact Page
            xml_content += '  <!-- Contact Page -->\n'
            xml_content += '  <url>\n'
            xml_content += '    <loc>https://www.gulfteachers.com/contact</loc>\n'
            xml_content += f'    <lastmod>{current_date}</lastmod>\n'
            xml_content += '    <changefreq>monthly</changefreq>\n'
            xml_content += '    <priority>0.7</priority>\n'
            xml_content += '  </url>\n\n'
            
            # Privacy Policy
            xml_content += '  <!-- Privacy Policy -->\n'
            xml_content += '  <url>\n'
            xml_content += '    <loc>https://www.gulfteachers.com/privacy-policy</loc>\n'
            xml_content += f'    <lastmod>{current_date}</lastmod>\n'
            xml_content += '    <changefreq>yearly</changefreq>\n'
            xml_content += '    <priority>0.5</priority>\n'
            xml_content += '  </url>\n\n'
            
            # Terms of Use
            xml_content += '  <!-- Terms of Use -->\n'
            xml_content += '  <url>\n'
            xml_content += '    <loc>https://www.gulfteachers.com/terms-of-use</loc>\n'
            xml_content += f'    <lastmod>{current_date}</lastmod>\n'
            xml_content += '    <changefreq>yearly</changefreq>\n'
            xml_content += '    <priority>0.5</priority>\n'
            xml_content += '  </url>\n\n'
            
            # Add all active job postings
            xml_content += '  <!-- Job Postings -->\n'
            for job in active_jobs:
                job_lastmod = job.created_at.strftime('%Y-%m-%d') if job.created_at else current_date
                xml_content += '  <url>\n'
                xml_content += f'    <loc>https://www.gulfteachers.com/jobs-description/{job.id}</loc>\n'
                xml_content += f'    <lastmod>{job_lastmod}</lastmod>\n'
                xml_content += '    <changefreq>weekly</changefreq>\n'
                xml_content += '    <priority>0.8</priority>\n'
                xml_content += '  </url>\n'
            
            # Close XML
            xml_content += '\n</urlset>'
            
            # Return XML response
            response = HttpResponse(xml_content, content_type='application/xml')
            response['Content-Type'] = 'application/xml; charset=utf-8'
            return response
            
        except Exception as e:
            return response_500(str(e))