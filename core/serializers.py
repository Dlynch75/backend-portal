from rest_framework import serializers
from .models import Teacher, School
from django.contrib.auth import authenticate
# Replace with actual email and password used during signup
email = '123@example.com'
password = '123'  # Use the same password you set when creating the user

user = authenticate(email=email, password=password)
if user is not None:
    print("Authentication successful:", user)
else:
    print("Authentication failed.")
    
    
class TeacherSignupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Teacher
        fields = ('email', 'username', 'city', 'address', 'password', 'full_name', 'experience_year')

    def create(self, validated_data):
        return Teacher.objects.create_user(**validated_data)

class SchoolSignupSerializer(serializers.ModelSerializer):
    class Meta:
        model = School
        fields = ('email', 'username', 'city', 'address', 'password', 'school_name')

    def create(self, validated_data):
        return School.objects.create_user(**validated_data)

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        # Authenticate user
        user = authenticate(username=email, password=password)
        if user is None:
            raise serializers.ValidationError("Invalid email or password.")
        
        return user