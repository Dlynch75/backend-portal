from django.db import models

# Create your models here.
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models
from django.forms import JSONField
from datetime import datetime

# Custom user manager to handle both types of users
class CustomUserManager(BaseUserManager):
    def create_user(self, email, username, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, username, password, **extra_fields)

# Abstract user model to share common fields
class CustomUser(AbstractBaseUser):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=50)
    city = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    is_subscribed = models.BooleanField(default=False)
    is_teacher = models.BooleanField(default=False)
    is_school = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    stripe_subscription_id = models.CharField(max_length=255, null=True, blank=True)
    last_reset_date = models.DateField(default=datetime.now)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    objects = CustomUserManager()

    def __str__(self):
        return self.email

# Teacher model inheriting from CustomUser
class Teacher(CustomUser):
    full_name = models.CharField(max_length=100)
    experience_year = models.PositiveIntegerField()
    applied_count= models.IntegerField(default=0)


    class Meta:
        verbose_name = 'Teacher'

# School model inheriting from CustomUser
class School(CustomUser):
    school_name = models.CharField(max_length=255)
    school_logo = models.ImageField(upload_to='images/', null=True, blank=True)
    post_count= models.IntegerField(default=0)

    class Meta:
        verbose_name = 'School'
        


        
class Package(models.Model):
    PACKAGE_FOR_CHOICES = (
        ('teacher', 'Teacher'),
        ('school', 'School'),
    )
    title = models.CharField(max_length=100)
    package_type = models.CharField(max_length=50)
    description = models.TextField()
    amount = models.FloatField(default=0.0)
    offer = models.JSONField(default=None)  
    package_for = models.CharField(max_length=10, choices=PACKAGE_FOR_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.package_for})"

    class Meta:
        verbose_name = 'Package'
        verbose_name_plural = 'Packages'
        
        

class UserPackage(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, null=True, blank=True, related_name='packages')
    package = models.ForeignKey(Package, on_delete=models.CASCADE)
    school = models.ForeignKey(School, on_delete=models.CASCADE, null=True, blank=True, related_name='packages')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.package} ({self.school}) ({self.teacher})"

    class Meta:
        verbose_name = 'UserPackage'