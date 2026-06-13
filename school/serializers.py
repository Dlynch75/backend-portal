from rest_framework import serializers

from core.models import Teacher
from core.serializers import SchoolSerializer, TeacherSerializer
from teacher.models import Hire
from .models import JobPosting, JobSave
from .job_utils import is_job_featured

class JobPostingSerializer(serializers.ModelSerializer):
    school = SchoolSerializer(read_only=True)
    is_saved = serializers.SerializerMethodField()
    is_applied = serializers.SerializerMethodField()
    is_featured_active = serializers.SerializerMethodField()

    class Meta:
        model = JobPosting
        fields = '__all__'

    def get_is_featured_active(self, obj):
        return is_job_featured(obj)

    def get_is_saved(self, obj):
        user = self.context.get('user')
        if not user or not hasattr(user, 'teacher'):
            return False
        return JobSave.objects.filter(job=obj, teacher=user.teacher).exists()

    def get_is_applied(self, obj):
        user = self.context.get('user')
        if not user or not hasattr(user, 'teacher'):
            return False
        return Hire.objects.filter(job=obj, teacher=user).exists()

    def create(self, validated_data):
        user = self.context['user']
        validated_data['school'] = user.school
        return super().create(validated_data)

        
class JobSaveSerializer(serializers.ModelSerializer):
    job_id = serializers.PrimaryKeyRelatedField(source='job', queryset=JobPosting.objects.all(), write_only=True)
    teacher_id = serializers.PrimaryKeyRelatedField(source='teacher', queryset=Teacher.objects.all(), write_only=True)
    job = JobPostingSerializer(read_only=True)  
    teacher = TeacherSerializer(read_only=True)  
    
    class Meta:
        model = JobSave
        fields = '__all__'

