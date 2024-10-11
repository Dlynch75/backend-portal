from rest_framework import serializers
from .models import Teacher, School, UserPackage, Package
from django.contrib.auth import authenticate

class PackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Package
        fields = ('id', 'title', 'package_type', 'description', 'offer', 'created_at')


class TeacherSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    packages = serializers.SerializerMethodField()

    class Meta:
        model = Teacher
        fields = ('id', 'email', 'username', 'city', 'address', 'full_name', 'experience_year', 
                  'is_school', 'is_teacher', 'packages', 'is_subscribed', 'password')

    def get_packages(self, obj):
        user_packages = UserPackage.objects.filter(teacher=obj)
        if user_packages.exists():
            return PackageSerializer([user_package.package for user_package in user_packages], many=True).data
        return None

    def create(self, validated_data):
        return Teacher.objects.create_user(**validated_data)


class SchoolSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    packages = serializers.SerializerMethodField()
    school_logo = serializers.ImageField(required=False, allow_null=True)
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
