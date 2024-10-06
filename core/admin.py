from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Teacher, School, UserPackage, Package


# Register the custom user models
admin.site.register(CustomUser)
admin.site.register(Teacher)
admin.site.register(School)
admin.site.register(UserPackage)
admin.site.register(Package)
