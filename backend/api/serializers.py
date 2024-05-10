from rest_framework import serializers
from rest_framework_simplejwt.tokens import Token
from userauths.models import User, Profile
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.password_validation import validate_password


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user) -> Token:
        token = super().get_token(user)
        token['full_name'] = user.full_name
        token['username'] = user.username
        token['email'] = user.email

        print(token)
        return token



class RegisterSerializer(serializers.ModelSerializer):
    password =  serializers.CharField(write_only=True,required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)


    class Meta:
        model = User
        fields = ['email', 'full_name', 'password', 'password2']


    def validate(self, attrs):
        print("Payload Before Validation:", attrs)
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({'password': "Password fields didnot match"}
                                              )   
        return attrs
    


    def create(self, validated_data):

        user = User.objects.create(full_name = validated_data['full_name'],email = validated_data['email'])
        email_username, _  = user.email.split("@")
        user.username = email_username
        user.set_password(validated_data['password']
                          )
        user.save()
        return user
       





class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model =User
        fields = '__all__'


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model =Profile
        fields = '__all__'        