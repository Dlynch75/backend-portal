from django.db import models

# Create your models here.
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models

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
    is_teacher = models.BooleanField(default=False)
    is_school = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    objects = CustomUserManager()

    def __str__(self):
        return self.email

# Teacher model inheriting from CustomUser
class Teacher(CustomUser):
    full_name = models.CharField(max_length=100)
    experience_year = models.PositiveIntegerField()

    class Meta:
        verbose_name = 'Teacher'

# School model inheriting from CustomUser
class School(CustomUser):
    school_name = models.CharField(max_length=255)

    class Meta:
        verbose_name = 'School'
