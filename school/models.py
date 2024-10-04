from django.db import models

from core.models import School

class JobPosting(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('close', 'Closed'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='open')
    title = models.CharField(max_length=100)
    description = models.TextField()
    school = models.ForeignKey(School, on_delete=models.CASCADE, null=True, blank=True)  
    required_qualifications = models.CharField(max_length=100)
    experience = models.CharField(max_length=100)
    benefits = models.TextField()
    responsibilities = models.TextField()
    location = models.CharField(max_length=100)
    deadline = models.DateTimeField()
    salary = models.CharField(max_length=50)
    applied_people = models.IntegerField(default= 0)
    viewd = models.IntegerField(default= 0)
    school_logo = models.ImageField(upload_to='images/', null=True, blank=True)

    def __str__(self):
        return self.title
