from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from school.models import JobPosting
from teacher.helper import can_create_post
from teacher.models import Hire
from utils.response import create_message, create_response
from utils.utils import get_user_from_token, require_authentication, response_500, send_notification_email
from .serializers import HireSerializer
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q
from rest_framework.pagination import LimitOffsetPagination
import cloudinary.uploader


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
            hires = Hire.objects.filter(filters) if filters else Hire.objects.all()
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
            if teacher.is_teacher:
                # Create a new hire for a specific job
                job_id = request.query_params.get('job_id', None)
                job = get_object_or_404(JobPosting, id=job_id)
                
                if not teacher.is_subscribed:
                    raise Exception("Please add Subscription to Apply.")
                if not can_create_post(teacher):
                    raise Exception("Post limit reached for your package this month.")
                
                # Check if the teacher has already applied to this job
                existing_hire = Hire.objects.filter(teacher=teacher, job=job).first()
                if existing_hire:
                    raise Exception("You have already applied to this job.")
                
                if job.status == "open":
                    data = request.data.copy()
                    data['job_id'] = job.id
                    data['school_id'] = job.school.id
                    data['teacher_id'] = teacher.id 
                    
                    # Handle CV upload if present
                    if 'cv' in request.FILES:
                        cv_file = request.FILES['cv']
                        cloudinary_response = cloudinary.uploader.upload(cv_file, resource_type='raw', flags="attachment")
                        cv_url = cloudinary_response['secure_url']
                        data['cv'] = cv_url  # Save the URL to the request data

                    serializer = HireSerializer(data=data)
                    if serializer.is_valid():
                        serializer.save()
                        # Increment the applied count
                        teacher.teacher.applied_count += 1
                        teacher.teacher.save()

                        # Email sent
                        subject = f"New Teacher Application - {teacher.username}"
                        message = (
                            f"A new teacher has applied for the job: {job.title}\n\n"
                            f"Teacher Name: {teacher.username}\n"
                            f"Email: {teacher.email}\n"
                            f"Phone: {teacher.teacher.phone or 'N/A'}\n"
                            f"Experience: {teacher.teacher.experience_year} years\n"
                            f"School: {job.school.school_name}\n"
                            f"Cover Letter:\n{data.get('cover_letter', 'N/A')}"
                        )

                        recipients = ['connect@gulfteachers.com', job.school.email]
                        send_notification_email(subject, message, recipients)

                        return create_response(create_message(serializer.data, 1000), status.HTTP_200_OK)
                    else:
                        raise Exception(serializer.errors)
                else:
                    raise Exception("Job is Closed")
            else:
                raise Exception("Login as a Teacher")
        except Exception as e:
            return response_500(str(e))

class HireDetailView(APIView):
    @require_authentication
    def get(self, request, hire_id):
        # Get details of a specific hire
        hire = get_object_or_404(Hire, id=hire_id)
        serializer = HireSerializer(hire)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @require_authentication
    def put(self, request, hire_id):
        # Update a specific hire
        hire = get_object_or_404(Hire, id=hire_id)
        old_cv_url = hire.cv  # Store the old CV URL for deletion if needed
        data = request.data.copy()

        # Handle CV upload if present
        if 'cv' in request.FILES:
            cv_file = request.FILES['cv']
            cloudinary_response = cloudinary.uploader.upload(cv_file, resource_type='raw')
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

