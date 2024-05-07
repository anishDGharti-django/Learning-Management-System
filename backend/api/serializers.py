from rest_framework import serializers
from rest_framework_simplejwt.tokens import Token
from userauths.models import User, Profile
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user) -> Token:
        token = super().get_token(user)
        token['full_name'] = user.full_name
        token['username'] = user.username
        token['email'] = user.email


        return token


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model =User
        fields = '__all__'


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model =Profile
        fields = '__all__'        