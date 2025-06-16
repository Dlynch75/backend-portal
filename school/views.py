from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
import logging
from core.models import School
from core.serializers import SchoolSerializer
from school.helper import can_create_post
from utils.response import create_message, create_response
from utils.utils import auth_user, get_user_from_token, require_authentication, response_500
from .models import JobPosting, JobSave
from .serializers import JobPostingSerializer, JobSaveSerializer
from django.shortcuts import get_object_or_404
from rest_framework.pagination import LimitOffsetPagination
import pycountry


# Create your views here.
class JobPostingListCreateView(APIView):
    def get(self, request):
        try:
            # school = get_user_from_token(request)
            # Get query parameters
            location = request.query_params.get('location', None)
            experience = request.query_params.get('experience', None)
            title = request.query_params.get('title', None)
            salary = request.query_params.get('salary', None)
            job_status = request.query_params.get('status', None)
            school_id = request.query_params.get('school_id', None)

            # Build the query
            filters = Q()
            if location:
                filters &= Q(location__icontains=location)
            if experience:
                filters &= Q(experience__icontains=experience)
            if title:
                filters &= Q(title__icontains=title)
            if salary:
                filters &= Q(salary__icontains=salary)
            if job_status:
                filters &= Q(status__icontains=job_status)
            if school_id:
                filters &= Q(school_id=school_id)
            
            # Filter job postings based on query parameters
            job_postings = JobPosting.objects.filter(filters).order_by('-created_at')
            # Check for offset and limit in the request parameters
            offset = request.query_params.get('offset', None)
            limit = request.query_params.get('limit', None)

            # Apply pagination if offset or limit are provided
            if offset is not None or limit is not None:
                paginator = LimitOffsetPagination()
                paginator.offset = int(offset) if offset else 0
                paginator.limit = int(limit) if limit else paginator.default_limit

                result_page = paginator.paginate_queryset(job_postings, request)
                serializer = JobPostingSerializer(result_page, many=True)
                return create_response(create_message({"count":len(job_postings), "data":serializer.data}, 1000), 
                                       status.HTTP_200_OK)

            # Serialize and return the filtered data
            serializer = JobPostingSerializer(job_postings, many=True)
            return create_response(create_message(serializer.data, 1000), status.HTTP_200_OK)
        except Exception as e:
            return response_500(str(e))

    
    @require_authentication
    def post(self, request):
        try:
            school = get_user_from_token(request)
            if not school.is_school:
                raise Exception("Please login as school.")
            if not school.is_subscribed:
                raise Exception("Please add Subscription to Apply.")
            if not can_create_post(school):
                raise Exception("Post limit reached for your package this month.")
            
            serializer = JobPostingSerializer(data=request.data,  context={'user': school})
            if serializer.is_valid():
                serializer.save()
                # Increment the post count
                school.school.post_count += 1
                school.school.save()
                return create_response(create_message(serializer.data, 1000), status.HTTP_200_OK)
            
            raise Exception(serializer.errors)
        except Exception as e:
            return response_500(str(e))
    
class JobPostingDetailView(APIView):
    @require_authentication
    def get(self, request, pk):
        try:
            user = get_user_from_token(request)
            job_posting = get_object_or_404(JobPosting, pk=pk)
            serializer = JobPostingSerializer(job_posting, context={'user': user})
            return create_response(create_message(serializer.data, 1000), status.HTTP_200_OK)
        except Exception as e:
            return response_500(str(e))
        
    
    @require_authentication
    def put(self, request, pk):
        try:
            job_posting = get_object_or_404(JobPosting, pk=pk)
            serializer = JobPostingSerializer(job_posting, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return create_response(create_message(serializer.data, 1000), status.HTTP_200_OK)
            raise Exception(serializer.errors)
        except Exception as e:
            return response_500(str(e))
        
    @require_authentication
    def delete(self, request, pk):
        try:
            job_posting = get_object_or_404(JobPosting, pk=pk)
            job_posting.delete()
            return create_response(create_message("Deleted", 1000), status.HTTP_200_OK)
        except Exception as e:
            return response_500(str(e))
    

class JobSaveView(APIView):
    @require_authentication
    def post(self, request):
        try:
            user = get_user_from_token(request)
            # Ensure only teachers can save jobs
            if user.is_school:
                raise Exception("Login as a Teacher to Save Job.")

            # Extract the job_id from the request data
            job_id = request.data.get('job_id', None)

            if not job_id:
                raise Exception("Job ID is required to save the job.")

            # Check if this teacher has already saved this job
            if JobSave.objects.filter(job_id=job_id, teacher=user.teacher).exists():
                return create_response(create_message("You have already saved this job.", 1001), status.HTTP_200_OK)
            # Proceed with saving the job
            serializer = JobSaveSerializer(data=request.data)

            if serializer.is_valid():
                serializer.save()  
                return create_response(create_message(serializer.data, 1000), status.HTTP_201_CREATED)
            
            raise Exception(serializer.errors)

        except Exception as e:
            return response_500(str(e))
    
    @require_authentication
    def get(self, request):
        try:
            teacher = get_user_from_token(request)
            job_save = JobSave.objects.filter(teacher=teacher)
            serializer = JobSaveSerializer(job_save, many=True)
            return create_response(create_message(serializer.data, 1000), status.HTTP_200_OK)
        except Exception as e:
            return response_500(str(e))

    # Delete a specific JobSave instance (DELETE)
    @require_authentication
    def delete(self, request, pk):
        try:
            print(pk)
            job_save = get_object_or_404(JobSave, pk=pk)
            job_save.delete()
            return create_response(create_message("Deleted", 1000), status.HTTP_200_OK)
        except Exception as e:
            return response_500(str(e))

class SchoolView(APIView):
    def get(self, request):
        try:
            # Get query parameters
            school_name = request.query_params.get('school_name', None)
            is_subscribed = request.query_params.get('is_subscribed', None)
            city = request.query_params.get('city', None)

            # Build the query
            filters = Q()
            if school_name:
                filters &= Q(school_name__icontains=school_name)
            if is_subscribed:
                filters &= Q(is_subscribed=is_subscribed)
            if city:
                filters &= Q(city__icontains=city)
            
            school = School.objects.filter(filters)
            # Check for offset and limit in the request parameters
            offset = request.query_params.get('offset', None)
            limit = request.query_params.get('limit', None)

            # Apply pagination if offset or limit are provided
            if offset is not None or limit is not None:
                paginator = LimitOffsetPagination()
                paginator.offset = int(offset) if offset else 0
                paginator.limit = int(limit) if limit else paginator.default_limit

                result_page = paginator.paginate_queryset(school, request)
                serializer = SchoolSerializer(result_page, many=True)
                return create_response(create_message({"count":len(school), "data":serializer.data}, 1000), 
                                       status.HTTP_200_OK)

            # Serialize and return the filtered data
            serializer = SchoolSerializer(school, many=True)
            return create_response(create_message(serializer.data, 1000), status.HTTP_200_OK)
        except Exception as e:
            return response_500(str(e))


class CountryView(APIView):



    def get(self, request):
        try:
            IMPORTANT_COUNTRIES = [
                "United States", "United Kingdom", "Canada", "India", "Australia", "Germany", "France", "Japan",
                "China",
                "Brazil"
            ]

            search = request.query_params.get('search', None)

            if search:
                # Return all countries (optionally filtered by search)
                all_countries = [country.name for country in pycountry.countries]
                filtered = [name for name in all_countries if search in name.lower()]
                return  create_response(create_message({"countries": filtered}, 1000), status.HTTP_200_OK)
            else:
                return create_response(create_message({"countries": IMPORTANT_COUNTRIES}, 1000), status.HTTP_200_OK)
        except Exception as e:
            return response_500(str(e))