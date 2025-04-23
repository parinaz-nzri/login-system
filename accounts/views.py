from rest_framework.views import APIView
from rest_framework.response import Response
from django.core.cache import cache
from .models import User
from .serializers import PhoneSerializer, VerifyCodeSerializer, LoginSerializer, UserSerializer
from .utils import get_client_ip, incr_attempts, generate_otp, is_blocked, verify_otp
from django.contrib.auth import authenticate


class SendCodeView(APIView):
    def post(self, request):
        serializer = PhoneSerializer(data=request.data)
        if serializer.is_valid():
            phone_number = serializer.validated_data["phone_number"]
            ip = get_client_ip(request)

            if is_blocked(ip, phone_number=phone_number, prefix="verify_attempts"):
                return Response(
                    {"error": "You are temporarily blocked. Please try again later."},
                    status=403
                )

            if User.objects.filter(phone_number=phone_number).exists():
                return Response(
                    {"message": "User already exists. Please login with your password."},
                    status=200
                )

            generate_otp(phone_number)

            incr_attempts(f"send_attempts_user_{phone_number}")
            incr_attempts(f"send_attempts_ip_{ip}")

            return Response({"message": "Verification code sent."}, status=200)

        return Response(serializer.errors, status=400)


class VerifyCodeView(APIView):
    def post(self, request):
        serializer = VerifyCodeSerializer(data=request.data)
        if serializer.is_valid():
            phone_number = serializer.validated_data["phone_number"]
            code = serializer.validated_data["code"]
            ip = get_client_ip(request)

            if is_blocked(ip, phone_number=phone_number, prefix="verify_attempts"):
                return Response({"error": "You are temporarily blocked. Please try again later."}, status=403)

            verification = verify_otp(phone_number, code, ip)
            if verification:
                return Response({"message": "OTP verified successfully. Now complete your registration."}, status=200)

            else:
                incr_attempts(f"verify_attempts_user_{phone_number}")
                incr_attempts(f"verify_attempts_ip_{ip}")
                return Response({"error": "Incorrect verification code."}, status=400)

        return Response(serializer.errors, status=400)


class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            phone = serializer.validated_data["phone_number"]
            password = serializer.validated_data["password"]
            ip = get_client_ip(request)

            # Check if the IP or phone number has been blocked based on attempts
            if is_blocked(ip, phone_number=serializer["phone_number"].value, prefix="verify_attempts"):
                return Response(
                    {"error": "You are temporarily blocked. Please try again later."},
                    status=403
                )

            if is_blocked(ip, phone_number=phone, prefix="login_attempts"):
                return Response(
                    {"error": "You are temporarily blocked. Please try again later."},
                    status=403
                )

            user = authenticate(phone_number=phone, password=password)

            if user is not None:
                cache.delete(f"login_attempts_ip_{ip}")
                cache.delete(f"login_attempts_user_{phone}")
                return Response({"message": "Login successful."}, status=200)

            incr_attempts(f"login_attempts_ip_{ip}")
            incr_attempts(f"login_attempts_user_{phone}")
            return Response({"error": "Incorrect username or password."}, status=401)

        return Response(serializer.errors, status=400)


class RegisterView(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        ip = get_client_ip(request)

        if serializer.is_valid():
            phone = serializer.validated_data["phone_number"]

            if not cache.get(f"verified_{phone}"):
                return Response(
                    {"error": "Phone number not verified."},
                    status=400
                )

            if is_blocked(ip, phone_number=phone, prefix="verify_attempts"):
                return Response(
                    {"error": "You are temporarily blocked. Please try again later."},
                    status=403
                )

            serializer.save()
            cache.delete(f"verified_{phone}")
            return Response({"message": "Registration successful."}, status=201)

        return Response(serializer.errors, status=400)
