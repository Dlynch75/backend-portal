from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import JobPosting, JobSave


# Register the custom user models
admin.site.register(JobPosting)
admin.site.register(JobSave)
