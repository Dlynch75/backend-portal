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
            return '0'
        if isinstance(value, str) and value.endswith('+'):
            return '15'
        if isinstance(value, (int, float)):
            return str(int(value))
        return str(value)
    
    def validate_dob(self, value):
        """Handle dob in DD/MM/YYYY format"""
        if isinstance(value, str) and value:
            try:
                return datetime.strptime(value, '%d/%m/%Y').date()
            except ValueError:
                try:
                    return datetime.strptime(value, '%Y-%m-%d').date()
                except ValueError:
                    raise serializers.ValidationError("Date must be in DD/MM/YYYY or YYYY-MM-DD format.")
        return value

    def create(self, validated_data):
        exp_year = validated_data.get('experience_year', '0')
        if not exp_year or exp_year == '':
            validated_data['experience_year'] = 0
        elif isinstance(exp_year, str):
            if exp_year.endswith('+'):
                validated_data['experience_year'] = 15
            else:
                try:
                    validated_data['experience_year'] = int(exp_year)
                except (ValueError, TypeError):
                    validated_data['experience_year'] = 0
        else:
            try:
                validated_data['experience_year'] = int(exp_year)
            except (ValueError, TypeError):
                validated_data['experience_year'] = 0
        
        if 'city' not in validated_data or not validated_data.get('city'):
            validated_data['city'] = 'Not specified'
        
        if 'address' not in validated_data or not validated_data.get('address'):
            validated_data['address'] = 'Not specified'
        
        if 'full_name' not in validated_data or not validated_data.get('full_name'):
            validated_data['full_name'] = validated_data.get('username', 'User')
        
        validated_data['is_teacher'] = True
        validated_data['is_school'] = False
        
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
