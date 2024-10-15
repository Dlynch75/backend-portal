from django.db import models
from django.conf import settings
from core.models import School, Teacher

from school.models import JobPosting

class Hire(models.Model):
    STATUS_CHOICES = [
        ('submitted', 'Submitted'),
        ('selected', 'Selected'),
        ('rejected', 'Rejected'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='submitted')
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    job = models.ForeignKey(JobPosting, on_delete=models.CASCADE)
    cover_letter = models.TextField(default=None, null=True, blank=True)
    cv = models.URLField(max_length=500, null=True, blank=True) 
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)  


    def __str__(self):
        return f'Hire: {self.teacher} for Job: {self.job} - Status: {self.status}'
