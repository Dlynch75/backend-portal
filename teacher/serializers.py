from rest_framework import serializers
from core.serializers import SchoolSerializer, TeacherSerializer

from school.serializers import JobPostingSerializer
from .models import Hire, Teacher, School, JobPosting



class HireSerializer(serializers.ModelSerializer):
    teacher = TeacherSerializer(read_only=True)
    school = SchoolSerializer(read_only=True)
    job = JobPostingSerializer(read_only=True)

    teacher_id = serializers.PrimaryKeyRelatedField(queryset=Teacher.objects.all(), source='teacher', write_only=True)
    school_id = serializers.PrimaryKeyRelatedField(queryset=School.objects.all(), source='school', write_only=True)
    job_id = serializers.PrimaryKeyRelatedField(queryset=JobPosting.objects.all(), source='job', write_only=True)

    class Meta:
        model = Hire
        fields = ['id', 'status', 'teacher', 'school', 'job', 'teacher_id', 'school_id', 'job_id', 'cv']
