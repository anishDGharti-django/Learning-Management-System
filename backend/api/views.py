from django.shortcuts import render
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.status import HTTP_201_CREATED, HTTP_404_NOT_FOUND
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import NotFound
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from api import serializers as api_serializers
from userauths.models import User
from api.utils import createOtp, sendMail

class MyTokenObtainPairView(TokenObtainPairView):
    """
    Obtain a pair of access and refresh tokens.
    """
    serializer_class = api_serializers.MyTokenObtainPairSerializer

    @swagger_auto_schema(operation_description="Obtain JWT tokens (access and refresh) using user credentials.")
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

class RegisterView(generics.CreateAPIView):
    """
    Register a new user.
    """
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = api_serializers.RegisterSerializer

    @swagger_auto_schema(operation_description="Register a new user with email and password.")
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

class PasswordResetEmailVerifyView(generics.RetrieveAPIView):
    """
    Send password reset email if the user exists.
    """
    permission_classes = [AllowAny]
    serializer_class = api_serializers.UserSerializer
    queryset = User.objects.all()

    email_param = openapi.Parameter(
        'email', openapi.IN_PATH, description="User email", type=openapi.TYPE_STRING
    )

    @swagger_auto_schema(
        operation_description="Send a password reset email to the user if the email exists.",
        manual_parameters=[email_param]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_object(self):
        email = self.kwargs["email"]
        user = User.objects.filter(email=email).first()

        if user:
            uuidb64 = user.pk
            refresh_token_for_user = RefreshToken.for_user(user=user)
            refresh_token = str(refresh_token_for_user.access_token)
            user.refresh_token = refresh_token
            user.otp = createOtp()
            user.save()

            link = f"http://localhost:5173/create-new-password/?otp={user.otp}&uuid={uuidb64}&refresh_token={refresh_token}"
            sendMail(
                user=user,
                mail_subject='Password Reset Email',
                email_template='emails/passwordResetEmail.html',
                link=link
            )

            return user
        else:
            raise NotFound("User with this email does not exist.")

class PasswordChangeApiView(generics.CreateAPIView):
    """
    Change user's password using OTP and UUID.
    """
    permission_classes = [AllowAny]
    serializer_class = api_serializers.UserSerializer

    @swagger_auto_schema(
        operation_description="Change the user's password using OTP and UUID.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'otp': openapi.Schema(type=openapi.TYPE_STRING, description='One-Time Password'),
                'uuidb64': openapi.Schema(type=openapi.TYPE_STRING, description='User UUID in Base64'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='New Password'),
            }
        ),
        responses={
            201: openapi.Response(description="Password changed successfully."),
            404: openapi.Response(description="User does not exist.")
        }
    )
    def create(self, request, *args, **kwargs):
        otp = request.data.get("otp")
        primary_key = request.data.get("uuidb64")
        password = request.data.get("password")

        try:
            user = User.objects.get(id=primary_key, otp=otp)
            user.set_password(password)
            user.otp = ""
            user.save()
            return Response(
                {
                    "message": "Password changed successfully.",
                },
                status=HTTP_201_CREATED,
            )
        except User.DoesNotExist:
            return Response(
                {
                    "message": "User does not exist.",
                },
                status=HTTP_404_NOT_FOUND,
            )
