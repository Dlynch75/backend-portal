from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from school.models import JobPosting
from teacher.models import Hire
from utils.response import create_message, create_response
from utils.utils import get_user_from_token, response_500
from .serializers import HireSerializer
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q
from rest_framework.pagination import LimitOffsetPagination


class HireListCreateView(APIView):
    def get(self, request):
        try:
            # Get query parameters
            school_id = request.query_params.get('school_id', None)
            teacher_id = request.query_params.get('teacher_id', None)
            job_id = request.query_params.get('job_id', None)
            
            # Build query filters
            filters = Q()
            if school_id:
                filters &= Q(school_id=school_id)
            if teacher_id:
                filters &= Q(teacher_id=teacher_id)
            if job_id:
                filters &= Q(job_id=job_id)
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

    def post(self, request):
        try:
            teacher = get_user_from_token(request)
            if teacher.is_teacher:
                # Create a new hire for a specific job
                job_id = request.query_params.get('job_id', None)
                job = get_object_or_404(JobPosting, id=job_id)
                data = request.data.copy()
                data['job_id'] = job.id
                data['school_id'] = job.school.id
                data['teacher_id'] = teacher.id 

                serializer = HireSerializer(data=data)
                if serializer.is_valid():
                    serializer.save()
                    return create_response(create_message(serializer.data, 1000), status.HTTP_200_OK)
                return create_response(create_message(serializer.errors, 00, "Missing Data !"),status.HTTP_400_BAD_REQUEST)
            else:
                return create_response(create_message("Login as Teacher !", 00, "Login as Teacher !"),status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return response_500(str(e))



class HireDetailView(APIView):

    def get(self, request, hire_id):
        # Get details of a specific hire
        hire = get_object_or_404(Hire, id=hire_id)
        serializer = HireSerializer(hire)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, hire_id):
        # Update a specific hire
        hire = get_object_or_404(Hire, id=hire_id)
        serializer = HireSerializer(hire, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, hire_id):
        try:
            # Delete a specific hire
            hire = get_object_or_404(Hire, id=hire_id)
            hire.delete()
            return create_response(create_message("Deleted", 1000), status.HTTP_200_OK)
        except Exception as e:
            return response_500(str(e))

