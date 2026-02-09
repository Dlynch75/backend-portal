from rest_framework import serializers
from .models import Teacher, School, UserPackage, Package
from django.contrib.auth import authenticate
from datetime import datetime

class PackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Package
        fields = ('id', 'title', 'package_type', 'description', 'offer', 'created_at', 'amount')


class TeacherSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    packages = serializers.SerializerMethodField()
    password = serializers.CharField(write_only=True) 
    experience_year = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    
    class Meta:
        model = Teacher
        fields = ('id', 'email', 'username', 'city', 'address', 'full_name', 'experience_year', 
                  'is_school', 'is_teacher', 'packages', 'is_subscribed', 'password', 'teaching_subject', 'highest_qualification',
                  'phone','dob', 'has_used_trial')

    def get_packages(self, obj):
        user_packages = UserPackage.objects.filter(teacher=obj)
        if user_packages.exists():
            return PackageSerializer([user_package.package for user_package in user_packages], many=True).data
        return None

    def validate_experience_year(self, value):
        """Convert string experience year to integer, handling '15+' case"""
        if not value or value == '':
            return None
        # Handle '15+' case
        if isinstance(value, str) and value.endswith('+'):
            return 15
        try:
            # Try to convert to int
            return int(value)
        except (ValueError, TypeError):
            # If conversion fails, return None or raise validation error
            raise serializers.ValidationError("Invalid experience year format.")
    
    def validate_dob(self, value):
        """Handle dob in DD/MM/YYYY format"""
        if isinstance(value, str) and value:
            try:
                # Try to parse DD/MM/YYYY format
                return datetime.strptime(value, '%d/%m/%Y').date()
            except ValueError:
                # If that fails, try standard format
                try:
                    return datetime.strptime(value, '%Y-%m-%d').date()
                except ValueError:
                    raise serializers.ValidationError("Date must be in DD/MM/YYYY or YYYY-MM-DD format.")
        return value

    def create(self, validated_data):
        # Convert experience_year if it's a string
        if 'experience_year' in validated_data and isinstance(validated_data['experience_year'], str):
            exp = validated_data['experience_year']
            if exp.endswith('+'):
                validated_data['experience_year'] = 15
            else:
                try:
                    validated_data['experience_year'] = int(exp)
                except ValueError:
                    validated_data['experience_year'] = 0
        
        return Teacher.objects.create_user(**validated_data)


class SchoolSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    packages = serializers.SerializerMethodField()
    password = serializers.CharField(write_only=True) 
    class Meta:
        model = School
        fields = ('id', 'email', 'username', 'city', 'address', 'school_name', 
                  'is_school', 'is_teacher', 'packages', 'is_subscribed', 'password', 'school_logo')

    def get_packages(self, obj):
        user_packages = UserPackage.objects.filter(school=obj)
        if user_packages.exists():
            return PackageSerializer([user_package.package for user_package in user_packages], many=True).data
        return None

    def create(self, validated_data):
        return School.objects.create_user(**validated_data)
    
    
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        # Authenticate user
        user = authenticate(email=email, password=password)
        if user is None:
            raise serializers.ValidationError("Invalid email or password.")
        
        return user
