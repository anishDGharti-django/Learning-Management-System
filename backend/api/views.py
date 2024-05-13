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
from decimal import Decimal
from rest_framework import status
from api import serializers as api_serializers
from userauths.models import User
from api.utils import createOtp, sendMail
from api import models as api_models

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

            link = f"http://localhost:5173/create-new-password/?otp={user.otp}&uuidb64={uuidb64}&refresh_token={refresh_token}"
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
        print(otp, primary_key, password)
        try:
            user = User.objects.get(id=primary_key, otp=otp)
            print('user is ', user)
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



class CategoryListAPIView(generics.ListAPIView):
    queryset = api_models.Category.objects.filter(active=True)  
    serializer_class = api_serializers.CategorySerializer
    permission_classes = [AllowAny]



class CourseListAPIView(generics.ListAPIView):
    queryset = api_models.Course.objects.filter(platform_status="Published", teacher_course_status="Published")
    serializer_class = api_serializers.CourseSerializer
    permission_classes = [AllowAny]    




class CourseDetailAPIView(generics.RetrieveAPIView):
    serializer_class= api_serializers.CourseSerializer
    permission_classes = [AllowAny]
    queryset = api_models.Course.objects.filter(platform_status="Published", teacher_course_status="Published")


    def get_object(self):
        slug = self.kwargs['slug'] 
        course = api_models.Course.objects.get(slug=slug, platform_status="Published", teacher_course_status="Published")   
        return course
    

class CartAPIView(generics.CreateAPIView):
    queryset = api_models.Cart.objects.all()
    serializer_class = api_serializers.CartSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        course_id = request.data['course_id']  
        user_id = request.data['user_id']
        price = request.data['price']
        country_name = request.data['country_name']
        cart_id = request.data['cart_id']

        print("course_id ==========", course_id)

        course = api_models.Course.objects.filter(id=course_id).first()
        
        if user_id != "undefined":
            user = User.objects.filter(id=user_id).first()
        else:
            user = None

        try:
            country_object = api_models.Country.objects.filter(name=country_name).first()
            country = country_object.name
        except:
            country_object = None
            country = "United States"

        if country_object:
            tax_rate = country_object.tax_rate / 100
        else:
            tax_rate = 0

        cart = api_models.Cart.objects.filter(cart_id=cart_id, course=course).first()

        if cart:
            cart.course = course
            cart.user = user
            cart.price = price
            cart.tax_fee = Decimal(price) * Decimal(tax_rate)
            cart.country = country
            cart.cart_id = cart_id
            cart.total = Decimal(cart.price) + Decimal(cart.tax_fee)
            cart.save()

            return Response({"message": "Cart Updated Successfully"}, status=status.HTTP_200_OK)

        else:
            cart = api_models.Cart()

            cart.course = course
            cart.user = user
            cart.price = price
            cart.tax_fee = Decimal(price) * Decimal(tax_rate)
            cart.country = country
            cart.cart_id = cart_id
            cart.total = Decimal(cart.price) + Decimal(cart.tax_fee)
            cart.save()

            return Response({"message": "Cart Created Successfully"}, status=status.HTTP_201_CREATED)




class CartListAPIView(generics.ListAPIView):
    serializer_class = api_serializers.CartSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        cart_id = self.kwargs['cart_id']
        queryset = api_models.Cart.objects.filter(cart_id=cart_id)
        return queryset
    

class CartItemDeleteAPIView(generics.DestroyAPIView):
    serializer_class = api_serializers.CartSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        cart_id = self.kwargs['cart_id']
        item_id = self.kwargs['item_id']

        return api_models.Cart.objects.filter(cart_id=cart_id, id=item_id).first()



class CartStatsAPIView(generics.RetrieveAPIView):
    serializer_class = api_serializers.CartSerializer
    permission_classes = [AllowAny]
    lookup_field = 'cart_id'


    def get_queryset(self):
        cart_id =self.kwargs['cart_id']
        queryset = api_models.Cart.objects.filter(cart_id=cart_id)
        return queryset
    

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        total_price = 0.0
        toal_tax = 0.0
        total_toal = 0.0

        for cart_item in queryset:
            total_price += float(calculate_price(cart_item))
            total_tasx += round(float(calculate_tax(cart_item)), 2)
            total_toal += calculate_total(cart_item)


        data ={
            "price": total_price,
            "tax": total_toal,
            "total": total_toal,
        }

        def calculate_price(self, cart_item):
            return cart_item.price    
        
        def calculate_tax(self, cart_item):
            return cart_item.tax_fee
        def calculate_total(self, cart_item):
            return cart_item.total    