from django.core.validators import RegexValidator
from rest_framework import serializers
from .models import User
from django.core.exceptions import ValidationError


def validate_password_strength(password):
    if len(password) < 8:
        raise ValidationError("Password must be at least 8 characters long.")
    return password


class PhoneSerializer(serializers.Serializer):
    phone_number = serializers.CharField(
        max_length=17,
        validators=[RegexValidator(regex=r'^(?:\+98|0)?9\d{9}$')]
    )


class VerifyCodeSerializer(serializers.Serializer):
    phone_number = serializers.CharField(
        max_length=17,
        validators=[RegexValidator(regex=r'^(?:\+98|0)?9\d{9}$')]
    )
    code = serializers.CharField(max_length=6)


class LoginSerializer(serializers.Serializer):
    phone_number = serializers.CharField(
        max_length=17,
        validators=[RegexValidator(regex=r'^(?:\+98|0)?9\d{9}$')]
    )
    password = serializers.CharField()


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password_strength])

    class Meta:
        model = User
        fields = ['phone_number', 'email', 'first_name', 'last_name', 'password']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        user = User.objects.create_user(
            phone_number=validated_data['phone_number'],
            password=validated_data['password'],
            email=validated_data.get('email', None),
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        return user
