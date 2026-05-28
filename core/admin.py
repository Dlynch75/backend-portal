from django.contrib import admin
from .models import CustomUser, Teacher, School, UserPackage, Package


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "full_name",
        "email",
        "username",
        "experience_year",
        "teaching_subject",
        "highest_qualification",
        "phone",
        "linkedin_url",
        "cv_url",
    )
    search_fields = ("full_name", "email", "username", "phone", "linkedin_url")


admin.site.register(CustomUser)
admin.site.register(School)
admin.site.register(UserPackage)
admin.site.register(Package)
