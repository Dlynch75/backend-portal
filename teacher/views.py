from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from school.models import JobPosting
from teacher.helper import can_create_post
from teacher.models import Hire, JobAlert
from school.serializers import JobPostingSerializer
from utils.cloudinary_upload import upload_teacher_cv
from utils.response import create_message, create_response
from utils.utils import get_user_from_token, require_authentication, response_500, send_notification_email
from utils.feature_flags import is_teacher_application_paywall_enabled
from .serializers import HireSerializer, JobAlertSerializer
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q
from rest_framework.pagination import LimitOffsetPagination
import cloudinary.uploader
from django.db import transaction
import logging
import requests

logger = logging.getLogger(__name__)


class HireListCreateView(APIView):    
    def get(self, request):
        try:
            # Get query parameters
            school_id = request.query_params.get('school_id', None)
            teacher_id = request.query_params.get('teacher_id', None)
            job_id = request.query_params.get('job_id', None)
            hire_status = request.query_params.get('status', None)
            # Build query filters
            filters = Q()
            if school_id:
                filters &= Q(school_id=school_id)
            if teacher_id:
                filters &= Q(teacher_id=teacher_id)
            if job_id:
                filters &= Q(job_id=job_id)
            if hire_status:
                filters &= Q(status__icontains=hire_status)
            # Filter hire requests based on query parameters
            hires = Hire.objects.filter(filters).order_by('-created_at') if filters else Hire.objects.all().order_by('-created_at')
            # Check for offset and limit in the request parameters
            offset = request.query_params.get('offset', None)
            limit = request.query_params.get('limit', None)

            # Apply pagination if offset or limit are provided
            if offset is not None or limit is not None:
                paginator = LimitOffsetPagination()
                paginator.offset = int(offset) if offset else 0
                paginator.limit = int(limit) if limit else paginator.default_limit

                result_page = paginator.paginate_queryset(hires, request)
                serializer = HireSerializer(result_page, many=True)
                return create_response(create_message({"count":len(hires), "data":serializer.data}, 1000), 
                                       status.HTTP_200_OK)
                
            # Serialize and return the filtered data
            serializer = HireSerializer(hires, many=True)
            return create_response(create_message(serializer.data, 1000), status.HTTP_200_OK)
        except Exception as e:
            return response_500(str(e))
        
    @require_authentication
    def post(self, request):
        try:
            teacher = get_user_from_token(request)

            if not teacher.is_teacher:
                raise Exception("Login as a Teacher")

            # Get job
            job_id = request.query_params.get('job_id', None)
            job = get_object_or_404(JobPosting, id=job_id)

            if is_teacher_application_paywall_enabled():
                if not teacher.is_subscribed:
                    raise Exception("Please add Subscription to Apply.")
                if not can_create_post(teacher):
                    raise Exception("Post limit reached for your package this month.")
            if Hire.objects.filter(teacher=teacher, job=job).exists():
                raise Exception("You have already applied to this job.")
            if job.status != "open":
                raise Exception("Job is Closed")

            data = request.data.copy()
            data['job_id'] = job.id
            data['school_id'] = job.school.id
            data['teacher_id'] = teacher.id

            use_profile_cv = str(request.data.get('use_profile_cv', '')).lower() in ('true', '1', 'yes')

            if 'cv' in request.FILES:
                cloudinary_response = upload_teacher_cv(request.FILES['cv'])
                data['cv'] = cloudinary_response['secure_url']
            elif use_profile_cv and teacher.teacher.cv_url:
                data['cv'] = teacher.teacher.cv_url
            else:
                raise Exception("Please upload a CV or save a default CV on your profile.")

            serializer = HireSerializer(data=data)
            serializer.is_valid(raise_exception=True)

            with transaction.atomic():
                serializer.save()
                teacher.teacher.applied_count += 1
                teacher.teacher.save()

            subject_line = f"New Teacher Application - {teacher.username}"
            cv_url = data.get('cv', 'N/A')
            cover_letter = data.get('cover_letter', 'N/A')
            message = (
                f"A new teacher has applied for the job: {job.title}\n\n"
                f"Teacher Name: {teacher.username}\n"
                f"Email: {teacher.email}\n"
                f"Phone: {teacher.teacher.phone or 'N/A'}\n"
                f"Experience: {teacher.teacher.experience_year} years\n"
                f"School: {job.school.school_name}\n\n"
                f"Cover Letter:\n{cover_letter}\n\n"
                f"CV Download Link: {cv_url}\n"
            )
            try:
                send_notification_email(
                    subject_line,
                    message,
                    ['connect@gulfteachers.com', job.school.email],
                    cv_url,
                )
            except Exception as mail_error:
                logger.warning("Application saved but notification email failed: %s", mail_error)

            return create_response(create_message(serializer.data, 1000), status.HTTP_200_OK)

        except Exception as e:
            return response_500(str(e))

class RecommendedJobsView(APIView):
    @require_authentication
    def get(self, request):
        try:
            user = get_user_from_token(request)
            if not user.is_teacher:
                raise Exception("Only teachers can view recommended jobs.")

            teacher = user.teacher
            filters = Q(status='open')
            profile_filters = Q()

            if teacher.teaching_subject:
                subject = teacher.teaching_subject.strip()
                profile_filters |= (
                    Q(subject__icontains=subject)
                    | Q(title__icontains=subject)
                    | Q(description__icontains=subject)
                )
            if teacher.address and teacher.address.strip().lower() not in ('not specified', ''):
                profile_filters |= Q(location__icontains=teacher.address.strip())
            if teacher.city and teacher.city.strip().lower() not in ('not specified', ''):
                profile_filters |= Q(location__icontains=teacher.city.strip())

            queryset = JobPosting.objects.filter(filters)
            if profile_filters:
                queryset = queryset.filter(profile_filters)

            jobs = list(queryset.order_by('-created_at')[:12])
            if not jobs:
                jobs = list(JobPosting.objects.filter(status='open').order_by('-created_at')[:12])

            serializer = JobPostingSerializer(jobs, many=True, context={'user': user})
            return create_response(create_message(serializer.data, 1000), status.HTTP_200_OK)
        except Exception as e:
            return response_500(str(e))


class JobAlertListCreateView(APIView):
    @require_authentication
    def get(self, request):
        try:
            user = get_user_from_token(request)
            if not user.is_teacher:
                raise Exception("Only teachers can manage job alerts.")
            alerts = JobAlert.objects.filter(teacher=user.teacher, is_active=True).order_by('-created_at')
            serializer = JobAlertSerializer(alerts, many=True)
            return create_response(create_message(serializer.data, 1000), status.HTTP_200_OK)
        except Exception as e:
            return response_500(str(e))

    @require_authentication
    def post(self, request):
        try:
            user = get_user_from_token(request)
            if not user.is_teacher:
                raise Exception("Only teachers can create job alerts.")

            data = request.data.copy()
            has_criteria = any(data.get(field, '').strip() for field in ['title', 'position', 'subject', 'location'])
            if not has_criteria:
                raise Exception("Add at least one search filter for your job alert.")

            serializer = JobAlertSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save(teacher=user.teacher)
            return create_response(create_message(serializer.data, 1000), status.HTTP_201_CREATED)
        except Exception as e:
            return response_500(str(e))


class JobAlertDetailView(APIView):
    @require_authentication
    def delete(self, request, alert_id):
        try:
            user = get_user_from_token(request)
            if not user.is_teacher:
                raise Exception("Only teachers can delete job alerts.")
            alert = get_object_or_404(JobAlert, pk=alert_id, teacher=user.teacher)
            alert.is_active = False
            alert.save(update_fields=['is_active'])
            return create_response(create_message("Job alert removed.", 1000), status.HTTP_200_OK)
        except Exception as e:
            return response_500(str(e))


class HireCvView(APIView):
    @require_authentication
    def get(self, request, hire_id):
        try:
            from django.http import HttpResponse
            user = get_user_from_token(request)
            hire = get_object_or_404(Hire, id=hire_id)
            if user.is_school:
                if hire.school_id != user.id:
                    raise Exception("You can only view applicants for your own jobs.")
            elif user.is_teacher:
                if hire.teacher_id != user.id:
                    raise Exception("You can only view your own application CV.")
            else:
                raise Exception("Not allowed.")
            if not hire.cv:
                raise Exception("No CV attached to this application.")
            response = requests.get(hire.cv, timeout=30)
            response.raise_for_status()
            content_type = response.headers.get('Content-Type', 'application/pdf')
            http_response = HttpResponse(response.content, content_type=content_type)
            http_response['Content-Disposition'] = 'inline; filename="cv.pdf"'
            return http_response
        except Exception as e:
            return response_500(str(e))


SCHOOL_UPDATABLE_STATUSES = {
    'submitted', 'under_review', 'shortlisted', 'interview',
    'not_selected', 'hired', 'rejected', 'selected',
}


class HireDetailView(APIView):
    @require_authentication
    def get(self, request, hire_id):
        try:
            hire = get_object_or_404(Hire, id=hire_id)
            serializer = HireSerializer(hire)
            return create_response(create_message(serializer.data, 1000), status.HTTP_200_OK)
        except Exception as e:
            return response_500(str(e))

    @require_authentication
    def patch(self, request, hire_id):
        try:
            user = get_user_from_token(request)
            if not user.is_school:
                raise Exception("Only schools can update application status.")

            hire = get_object_or_404(Hire, id=hire_id)
            if hire.school_id != user.id:
                raise Exception("You can only update applicants for your own jobs.")

            data = {}
            if 'status' in request.data:
                status_value = request.data.get('status')
                if status_value not in SCHOOL_UPDATABLE_STATUSES:
                    raise Exception("Invalid application status.")
                data['status'] = status_value
            if 'school_note' in request.data:
                data['school_note'] = request.data.get('school_note') or ''

            if not data:
                raise Exception("Provide status and/or school_note to update.")

            serializer = HireSerializer(hire, data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return create_response(create_message(serializer.data, 1000), status.HTTP_200_OK)
        except Exception as e:
            return response_500(str(e))

    @require_authentication
    def put(self, request, hire_id):
        # Update a specific hire
        hire = get_object_or_404(Hire, id=hire_id)
        old_cv_url = hire.cv  # Store the old CV URL for deletion if needed
        data = request.data.copy()

        # Handle CV upload if present
        if 'cv' in request.FILES:
            cloudinary_response = upload_teacher_cv(request.FILES['cv'])
            cv_url = cloudinary_response['secure_url']
            data['cv'] = cv_url  # Update the CV URL

            # delete the old CV from Cloudinary
            if old_cv_url:
                public_id = old_cv_url.split('/')[-1].split('.')[0]  # Extract public ID
                cloudinary.uploader.destroy(public_id, resource_type='raw')

        serializer = HireSerializer(hire, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @require_authentication
    def delete(self, request, hire_id):
        try:
            # Delete a specific hire
            hire = get_object_or_404(Hire, id=hire_id)

            # Delete the CV from Cloudinary if it exists
            if hire.cv:
                public_id = hire.cv.split('/')[-1].split('.')[0]  # Extract public ID
                cloudinary.uploader.destroy(public_id, resource_type='raw')

            hire.delete()
            return create_response(create_message("Deleted", 1000), status.HTTP_200_OK)
        except Exception as e:
            return response_500(str(e))

