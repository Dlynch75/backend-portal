from rest_framework import serializers

from core.serializers import SchoolSerializer
from .models import JobPosting, JobSave

class JobPostingSerializer(serializers.ModelSerializer):
    school = SchoolSerializer(read_only=True)
    class Meta:
        model = JobPosting
        fields = '__all__'
        
class JobSaveSerializer(serializers.ModelSerializer):
    job = JobPostingSerializer(read_only=True)
    class Meta:
        model = JobSave
        fields = '__all__'
