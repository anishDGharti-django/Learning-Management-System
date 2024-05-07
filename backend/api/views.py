from django.shortcuts import render
from rest_framework_simplejwt.views import TokenObtainPairView
from api import serializers as api_serializers
# Create your views here.



class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = api_serializers.MyTokenObtainPairSerializer