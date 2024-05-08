from django.shortcuts import render
from rest_framework import generics
from api.utils import createOtp, sendMail
from rest_framework.response import Response
from userauths.models import User
from rest_framework.status import HTTP_201_CREATED, HTTP_404_NOT_FOUND
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.exceptions import NotFound
from api import serializers as api_serializers
from rest_framework_simplejwt.tokens import RefreshToken

# Create your views here.


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = api_serializers.MyTokenObtainPairSerializer


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [
        AllowAny,
    ]
    serializer_class = api_serializers.RegisterSerializer


class PasswordResetEmailVerifyView(generics.RetrieveAPIView):
    permission_classes = [
        AllowAny,
    ]
    serializer_class = api_serializers.UserSerializer

    queryset = User.objects.all()

    def get_object(self):
        email = self.kwargs[
            "email"
        ]  # api/v1/password-email-verify/anishgharti10@gmail.com/

        user = User.objects.filter(email=email).first()

        if user:
            uuidb64 = user.pk
            refresh_token_for_user = RefreshToken.for_user(user=user)
            refresh_token = str(refresh_token_for_user.access_token)
            user.refresh_token = refresh_token
            user.otp = createOtp()
            user.save()

            link = f"http://localhost:5173/create-new-password/?otp={user.otp}&uuid={uuidb64}&refresh_token={refresh_token}"

            sendMail(user=user, mail_subject='Password Reset Email',email_template='emails/passwordResetEmail.html', link=link)

            return user
        else:
            raise NotFound


class PasswordChangeApiView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = api_serializers.UserSerializer

    def create(self, request, *args, **kwargs):
        otp = request.data["otp"]
        primary_key = request.data["uuidb64"]
        password = request.data["password"]

        user = User.objects.get(id=primary_key, otp=otp)
        if user:
            user.set_password(password)
            user.otp = ""
            user.save()
            return Response(
                {
                    "message": "password changed successfully",
                },
                status=HTTP_201_CREATED,
            )

        else:
            return Response(
                {
                    "message": "User doesnot exist",
                },
                status=HTTP_404_NOT_FOUND,
            )
