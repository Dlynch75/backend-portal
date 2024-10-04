from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
import logging
from utils.response import create_message, create_response
from utils.utils import auth_user, get_user_from_token, require_authentication, response_500
from .models import JobPosting
from .serializers import JobPostingSerializer
from django.shortcuts import get_object_or_404
from rest_framework.pagination import LimitOffsetPagination

logger = logging.getLogger(__name__)

# Create your views here.
class JobPostingListCreateView(APIView):
    @require_authentication
    def get(self, request):
        try:
            school = get_user_from_token(request)
            # Get query parameters
            location = request.query_params.get('location', None)
            experience = request.query_params.get('experience', None)
            title = request.query_params.get('title', None)
            salary = request.query_params.get('salary', None)
            status = request.query_params.get('status', None)
            current_school = request.query_params.get('current_school', None)

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
            if status:
                filters &= Q(status__icontains=status)
            if current_school:
                filters &= Q(school_id=school.id)

            # Filter job postings based on query parameters
            job_postings = JobPosting.objects.filter(filters)
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
            serializer = JobPostingSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return create_response(create_message(serializer.data, 1000), status.HTTP_200_OK)
            return create_response(create_message(serializer.errors, 00, "Missing Data !"),status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return response_500(str(e))
    
# Retrieve, Update, and Delete view
class JobPostingDetailView(APIView):
    @require_authentication
    def get(self, request, pk):
        try:
            job_posting = get_object_or_404(JobPosting, pk=pk)
            serializer = JobPostingSerializer(job_posting)
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
            return create_response(create_message(serializer.errors, 00, "Missing Data !"),status.HTTP_400_BAD_REQUEST)
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
    



