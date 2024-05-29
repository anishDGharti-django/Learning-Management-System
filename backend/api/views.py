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

import requests


class MyTokenObtainPairView(TokenObtainPairView):
    """
    Obtain a pair of access and refresh tokens.
    """

    serializer_class = api_serializers.MyTokenObtainPairSerializer

    @swagger_auto_schema(
        operation_description="Obtain JWT tokens (access and refresh) using user credentials."
    )
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
        "email", openapi.IN_PATH, description="User email", type=openapi.TYPE_STRING
    )

    @swagger_auto_schema(
        operation_description="Send a password reset email to the user if the email exists.",
        manual_parameters=[email_param],
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
                mail_subject="Password Reset Email",
                email_template="emails/passwordResetEmail.html",
                link=link,
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
                "otp": openapi.Schema(
                    type=openapi.TYPE_STRING, description="One-Time Password"
                ),
                "uuidb64": openapi.Schema(
                    type=openapi.TYPE_STRING, description="User UUID in Base64"
                ),
                "password": openapi.Schema(
                    type=openapi.TYPE_STRING, description="New Password"
                ),
            },
        ),
        responses={
            201: openapi.Response(description="Password changed successfully."),
            404: openapi.Response(description="User does not exist."),
        },
    )
    def create(self, request, *args, **kwargs):
        otp = request.data.get("otp")
        primary_key = request.data.get("uuidb64")
        password = request.data.get("password")
        print(otp, primary_key, password)
        try:
            user = User.objects.get(id=primary_key, otp=otp)
            print("user is ", user)
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
    queryset = api_models.Course.objects.filter(
        platform_status="Published", teacher_course_status="Published"
    )
    serializer_class = api_serializers.CourseSerializer
    permission_classes = [AllowAny]


class CourseDetailAPIView(generics.RetrieveAPIView):
    serializer_class = api_serializers.CourseSerializer
    permission_classes = [AllowAny]
    queryset = api_models.Course.objects.filter(
        platform_status="Published", teacher_course_status="Published"
    )

    def get_object(self):
        slug = self.kwargs["slug"]
        course = api_models.Course.objects.get(
            slug=slug, platform_status="Published", teacher_course_status="Published"
        )
        return course


class CartAPIView(generics.CreateAPIView):
    queryset = api_models.Cart.objects.all()
    serializer_class = api_serializers.CartSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        course_id = request.data["course_id"]
        user_id = request.data["user_id"]
        price = request.data["price"]
        country_name = request.data["country_name"]
        cart_id = request.data["cart_id"]

        print("course_id ==========", course_id)

        course = api_models.Course.objects.filter(id=course_id).first()

        if user_id != "undefined":
            user = User.objects.filter(id=user_id).first()
        else:
            user = None

        try:
            country_object = api_models.Country.objects.filter(
                name=country_name
            ).first()
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

            return Response(
                {"message": "Cart Updated Successfully"}, status=status.HTTP_200_OK
            )

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

            return Response(
                {"message": "Cart Created Successfully"}, status=status.HTTP_201_CREATED
            )


class CartListAPIView(generics.ListAPIView):
    serializer_class = api_serializers.CartSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        cart_id = self.kwargs["cart_id"]
        queryset = api_models.Cart.objects.filter(cart_id=cart_id)
        return queryset


class CartItemDeleteAPIView(generics.DestroyAPIView):
    serializer_class = api_serializers.CartSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        cart_id = self.kwargs["cart_id"]
        item_id = self.kwargs["item_id"]

        return api_models.Cart.objects.filter(cart_id=cart_id, id=item_id).first()


class CartStatsAPIView(generics.RetrieveAPIView):
    serializer_class = api_serializers.CartSerializer
    permission_classes = [AllowAny]
    lookup_field = "cart_id"

    def get_queryset(self):
        cart_id = self.kwargs["cart_id"]
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

        data = {
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


class CreateOrderAPIView(generics.CreateAPIView):
    serializer_class = api_serializers.CartOrderSerializer
    permission_classes = [AllowAny]
    queryset = api_models.CartOrder.objects.all()

    def create(self, request, *args, **kwargs):
        full_name = request.data["full_name"]
        email = request.data["email"]
        country = request.data["country"]
        cart_id = request.data["cart_id"]
        user_id = request.data["user_id"]

        if not user_id:
            user = None
        else:
            user = User.objects.get(id=user_id)

        cart_items = api_models.Cart.objects.filter(cart_id=cart_id)

        total_price = Decimal(0.00)
        total_tax = Decimal(0.00)
        total_initial_total = Decimal(0.00)
        total_total = Decimal(0.00)

        order = api_models.CartOrder.objects.create(
            full_name=full_name, email=email, country=country, student=user
        )
        for c in cart_items:
            api_models.CartOrderItem.objects.create(
                order=order,
                course=c.course,
                price=c.price,
                tax_fee=c.tax_fee,
                total=c.total,
                initial_total=c.total,
                teacher=c.course.teacher,
            )

            total_price += Decimal(c.price)
            total_tax += Decimal(c.tax_fee)
            total_initial_total += Decimal(c.total)
            total_total += Decimal(c.total)

            order.teachers.add(c.course.teacher)

        order.sub_total = total_price
        order.tax_fee = total_tax
        order.initial_total = total_initial_total
        order.total = total_total
        order.save()

        return Response(
            {"message": "Order Created Successfully", "order_oid": order.oid},
            status=status.HTTP_201_CREATED,
        )


class CheckoutAPIView(generics.RetrieveAPIView):
    serializer_class = api_serializers.CartOrderSerializer
    permission_classes = [AllowAny]
    lookup_field = "oid"
    queryset = api_models.CartOrder.objects.all()


class CouponApplyAPIView(generics.CreateAPIView):
    serializer_class = api_serializers.CouponSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        order_oid = request.data["order_oid"]
        coupon_code = request.data["coupon_code"]

        order = api_models.CartOrder.objects.get(oid=order_oid)
        coupon = api_models.Coupon.objects.get(code=coupon_code)

        if coupon:
            order_items = api_models.CartOrderItem.objects.filter(
                order=order, teacher=coupon.teacher
            )
            for i in order_items:
                if not coupon in i.coupons.all():
                    discount = i.total * coupon.discount / 100
                    i.total -= discount
                    i.price -= discount
                    i.saved += discount
                    i.applied_coupon = True
                    i.coupons.add(coupon)

                    order.coupons.add(coupon)
                    order.total -= discount
                    order.sub_total -= discount
                    order.saved += discount

                    i.save()
                    order.save()
                    coupon.used_by.add(order.student)
                    return Response(
                        {"message": "Coupon Found and Activated", "icon": "success"},
                        status=status.HTTP_201_CREATED,
                    )
                else:
                    return Response(
                        {"message": "Coupon Already Applied", "icon": "warning"},
                        status=status.HTTP_200_OK,
                    )
        else:
            return Response(
                {"message": "Coupon Not Found", "icon": "error"},
                status=status.HTTP_404_NOT_FOUND,
            )


import stripe
from django.shortcuts import render, redirect
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth.hashers import check_password
from django.db import models
from django.db.models.functions import ExtractMonth
from django.core.files.uploadedfile import InMemoryUploadedFile


from api import serializers as api_serializer
from api import models as api_models
from userauths.models import User, Profile

from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import generics, status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from rest_framework.decorators import api_view


import random
from decimal import Decimal
import stripe
import requests
from datetime import datetime, timedelta
from distutils.util import strtobool


stripe.api_key = settings.STRIPE_SECRET_KEY
PAYPAL_CLIENT_ID = settings.PAYPAL_CLIENT_ID
PAYPAL_SECRET_ID = settings.PAYPAL_SECRET_ID


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = api_serializer.MyTokenObtainPairSerializer


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = api_serializer.RegisterSerializer


def generate_random_otp(length=7):
    otp = "".join([str(random.randint(0, 9)) for _ in range(length)])
    return otp


class PasswordResetEmailVerifyAPIView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]
    serializer_class = api_serializer.UserSerializer

    def get_object(self):
        email = self.kwargs["email"]  # api/v1/password-email-verify/desphixs@gmail.com/

        user = User.objects.filter(email=email).first()

        if user:
            uuidb64 = user.pk
            refresh = RefreshToken.for_user(user)
            refresh_token = str(refresh.access_token)

            user.refresh_token = refresh_token
            user.otp = generate_random_otp()
            user.save()

            link = f"http://localhost:5173/create-new-password/?otp={user.otp}&uuidb64={uuidb64}&refresh_token={refresh_token}"

            context = {"link": link, "username": user.username}

            subject = "Password Rest Email"
            text_body = render_to_string("email/password_reset.txt", context)
            html_body = render_to_string("email/password_reset.html", context)

            msg = EmailMultiAlternatives(
                subject=subject,
                from_email=settings.FROM_EMAIL,
                to=[user.email],
                body=text_body,
            )

            msg.attach_alternative(html_body, "text/html")
            msg.send()

            print("link ======", link)
        return user


class PasswordChangeAPIView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = api_serializer.UserSerializer

    def create(self, request, *args, **kwargs):
        otp = request.data["otp"]
        uuidb64 = request.data["uuidb64"]
        password = request.data["password"]

        user = User.objects.get(id=uuidb64, otp=otp)
        if user:
            user.set_password(password)
            # user.otp = ""
            user.save()

            return Response(
                {"message": "Password Changed Successfully"},
                status=status.HTTP_201_CREATED,
            )
        else:
            return Response(
                {"message": "User Does Not Exists"}, status=status.HTTP_404_NOT_FOUND
            )


class ChangePasswordAPIView(generics.CreateAPIView):
    serializer_class = api_serializer.UserSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        user_id = request.data["user_id"]
        old_password = request.data["old_password"]
        new_password = request.data["new_password"]

        user = User.objects.get(id=user_id)
        if user is not None:
            if check_password(old_password, user.password):
                user.set_password(new_password)
                user.save()
                return Response(
                    {"message": "Password changed successfully", "icon": "success"}
                )
            else:
                return Response(
                    {"message": "Old password is incorrect", "icon": "warning"}
                )
        else:
            return Response({"message": "User does not exists", "icon": "error"})


class ProfileAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = api_serializer.ProfileSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        user_id = self.kwargs["user_id"]
        user = User.objects.get(id=user_id)
        return Profile.objects.get(user=user)


class CategoryListAPIView(generics.ListAPIView):
    queryset = api_models.Category.objects.filter(active=True)
    serializer_class = api_serializer.CategorySerializer
    permission_classes = [AllowAny]


class CourseListAPIView(generics.ListAPIView):
    queryset = api_models.Course.objects.filter(
        platform_status="Published", teacher_course_status="Published"
    )
    serializer_class = api_serializer.CourseSerializer
    permission_classes = [AllowAny]


class CourseDetailAPIView(generics.RetrieveAPIView):
    serializer_class = api_serializer.CourseSerializer
    permission_classes = [AllowAny]
    queryset = api_models.Course.objects.filter(
        platform_status="Published", teacher_course_status="Published"
    )

    def get_object(self):
        slug = self.kwargs["slug"]
        course = api_models.Course.objects.get(
            slug=slug, platform_status="Published", teacher_course_status="Published"
        )
        return course


class CartAPIView(generics.CreateAPIView):
    queryset = api_models.Cart.objects.all()
    serializer_class = api_serializer.CartSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        course_id = request.data["course_id"]
        user_id = request.data["user_id"]
        price = request.data["price"]
        country_name = request.data["country_name"]
        cart_id = request.data["cart_id"]

        print("course_id ==========", course_id)

        course = api_models.Course.objects.filter(id=course_id).first()

        if user_id != "undefined":
            user = User.objects.filter(id=user_id).first()
        else:
            user = None

        try:
            country_object = api_models.Country.objects.filter(
                name=country_name
            ).first()
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

            return Response(
                {"message": "Cart Updated Successfully"}, status=status.HTTP_200_OK
            )

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

            return Response(
                {"message": "Cart Created Successfully"}, status=status.HTTP_201_CREATED
            )


class CartListAPIView(generics.ListAPIView):
    serializer_class = api_serializer.CartSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        cart_id = self.kwargs["cart_id"]
        queryset = api_models.Cart.objects.filter(cart_id=cart_id)
        return queryset


class CartItemDeleteAPIView(generics.DestroyAPIView):
    serializer_class = api_serializer.CartSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        cart_id = self.kwargs["cart_id"]
        item_id = self.kwargs["item_id"]

        return api_models.Cart.objects.filter(cart_id=cart_id, id=item_id).first()


class CartStatsAPIView(generics.RetrieveAPIView):
    serializer_class = api_serializer.CartSerializer
    permission_classes = [AllowAny]
    lookup_field = "cart_id"

    def get_queryset(self):
        cart_id = self.kwargs["cart_id"]
        queryset = api_models.Cart.objects.filter(cart_id=cart_id)
        return queryset

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        total_price = 0.00
        total_tax = 0.00
        total_total = 0.00

        for cart_item in queryset:
            total_price += float(self.calculate_price(cart_item))
            total_tax += float(self.calculate_tax(cart_item))
            total_total += round(float(self.calculate_total(cart_item)), 2)

        data = {
            "price": total_price,
            "tax": total_tax,
            "total": total_total,
        }

        return Response(data)

    def calculate_price(self, cart_item):
        return cart_item.price

    def calculate_tax(self, cart_item):
        return cart_item.tax_fee

    def calculate_total(self, cart_item):
        return cart_item.total


class CreateOrderAPIView(generics.CreateAPIView):
    serializer_class = api_serializer.CartOrderSerializer
    permission_classes = [AllowAny]
    queryset = api_models.CartOrder.objects.all()

    def create(self, request, *args, **kwargs):
        full_name = request.data["full_name"]
        email = request.data["email"]
        country = request.data["country"]
        cart_id = request.data["cart_id"]
        user_id = request.data["user_id"]

        if user_id != 0:
            user = User.objects.get(id=user_id)
        else:
            user = None

        cart_items = api_models.Cart.objects.filter(cart_id=cart_id)

        total_price = Decimal(0.00)
        total_tax = Decimal(0.00)
        total_initial_total = Decimal(0.00)
        total_total = Decimal(0.00)

        order = api_models.CartOrder.objects.create(
            full_name=full_name, email=email, country=country, student=user
        )

        for c in cart_items:
            api_models.CartOrderItem.objects.create(
                order=order,
                course=c.course,
                price=c.price,
                tax_fee=c.tax_fee,
                total=c.total,
                initial_total=c.total,
                teacher=c.course.teacher,
            )

            total_price += Decimal(c.price)
            total_tax += Decimal(c.tax_fee)
            total_initial_total += Decimal(c.total)
            total_total += Decimal(c.total)

            order.teachers.add(c.course.teacher)

        order.sub_total = total_price
        order.tax_fee = total_tax
        order.initial_total = total_initial_total
        order.total = total_total
        order.save()

        return Response(
            {"message": "Order Created Successfully", "order_oid": order.oid},
            status=status.HTTP_201_CREATED,
        )


class CheckoutAPIView(generics.RetrieveAPIView):
    serializer_class = api_serializer.CartOrderSerializer
    permission_classes = [AllowAny]
    queryset = api_models.CartOrder.objects.all()
    lookup_field = "oid"


class CouponApplyAPIView(generics.CreateAPIView):
    serializer_class = api_serializer.CouponSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        order_oid = request.data["order_oid"]
        coupon_code = request.data["coupon_code"]

        order = api_models.CartOrder.objects.get(oid=order_oid)
        coupon = api_models.Coupon.objects.get(code=coupon_code)

        if coupon:
            order_items = api_models.CartOrderItem.objects.filter(
                order=order, teacher=coupon.teacher
            )
            for i in order_items:
                if not coupon in i.coupons.all():
                    discount = i.total * coupon.discount / 100

                    i.total -= discount
                    i.price -= discount
                    i.saved += discount
                    i.applied_coupon = True
                    i.coupons.add(coupon)

                    order.coupons.add(coupon)
                    order.total -= discount
                    order.sub_total -= discount
                    order.saved += discount

                    i.save()
                    order.save()
                    coupon.used_by.add(order.student)
                    return Response(
                        {"message": "Coupon Found and Activated", "icon": "success"},
                        status=status.HTTP_201_CREATED,
                    )
                else:
                    return Response(
                        {"message": "Coupon Already Applied", "icon": "warning"},
                        status=status.HTTP_200_OK,
                    )
        else:
            return Response(
                {"message": "Coupon Not Found", "icon": "error"},
                status=status.HTTP_404_NOT_FOUND,
            )


class StripeCheckoutAPIView(generics.CreateAPIView):
    serializer_class = api_serializers.CartOrderSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):

        order_oid = self.kwargs["order_oid"]
        order = api_models.CartOrder.objects.get(oid=order_oid)

        if not order:
            return Response(
                {"message": "Order Not Found"}, status=status.HTTP_404_NOT_FOUND
            )

        try:
            checkout_session = stripe.checkout.Session.create(
                customer_email=order.email,
                payment_method_types=["card"],
                line_items=[
                    {
                        "price_data": {
                            "currency": "usd",
                            "product_data": {
                                "name": order.full_name,
                            },
                            "unit_amount": int(order.total * 100),
                        },
                        "quantity": 1,
                    }
                ],
                mode="payment",
                success_url=settings.FRONTEND_SITE_URL
                + "/payment-success/"
                + order.oid
                + "?session_id={CHECKOUT_SESSION_ID}",
                cancel_url=settings.FRONTEND_SITE_URL + "/payment-failed/",
            )
            print("checkout_session ====", checkout_session)
            order.stripe_session_id = checkout_session.id

            return redirect(checkout_session.url)
        except stripe.error.StripeError as e:
            return Response(
                {
                    "message": f"Something went wrong when trying to make payment. Error: {str(e)}"
                }
            )


def get_access_token(client_id, secret_key):
    token_url = "https://api.sandbox.paypal.com/v1/oauth2/token"
    data = {"grant_type": "client_credentials"}
    auth = (client_id, secret_key)
    response = requests.post(token_url, data=data, auth=auth)

    if response.status_code == 200:
        print("Access TOken ====", response.json()["access_token"])
        return response.json()["access_token"]
    else:
        raise Exception(
            f"Failed to get access token from paypal {response.status_code}"
        )


class PaymentSuccessAPIView(generics.CreateAPIView):
    serializer_class = api_serializers.CartOrderSerializer
    queryset = api_models.CartOrder.objects.all()

    def create(self, request, *args, **kwargs):
        order_oid = request.data["order_oid"]
        session_id = request.data["session_id"]
        paypal_order_id = request.data["paypal_order_id"]

        order = api_models.CartOrder.objects.get(oid=order_oid)
        order_items = api_models.CartOrderItem.objects.filter(order=order)

        # Paypal payment success
        if paypal_order_id != "null":
            paypal_api_url = (
                f"https://api-m.sandbox.paypal.com/v2/checkout/orders/{paypal_order_id}"
            )
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {get_access_token(PAYPAL_CLIENT_ID, PAYPAL_SECRET_ID)}",
            }
            response = requests.get(paypal_api_url, headers=headers)
            if response.status_code == 200:
                paypal_order_data = response.json()
                paypal_payment_status = paypal_order_data["status"]
                if paypal_payment_status == "COMPLETED":
                    if order.payment_status == "Processing":
                        order.payment_status = "Paid"
                        order.save()
                        api_models.Notification.objects.create(
                            user=order.student,
                            order=order,
                            type="Course Enrollment Completed",
                        )

                        for o in order_items:
                            api_models.Notification.objects.create(
                                teacher=o.teacher,
                                order=order,
                                order_item=o,
                                type="New Order",
                            )
                            api_models.EnrolledCourse.objects.create(
                                course=o.course,
                                user=order.student,
                                teacher=o.teacher,
                                order_item=o,
                            )

                        return Response({"message": "Payment Successfull"})
                    else:
                        return Response({"message": "Already Paid"})
                else:
                    return Response({"message": "Payment Failed"})
            else:
                return Response({"message": "PayPal Error Occured"})

        # Stripe payment success
        if session_id != "null":
            session = stripe.checkout.Session.retrieve(session_id)
            if session.payment_status == "paid":
                if order.payment_status == "Processing":
                    order.payment_status = "Paid"
                    order.save()

                    api_models.Notification.objects.create(
                        user=order.student,
                        order=order,
                        type="Course Enrollment Completed",
                    )
                    for o in order_items:
                        api_models.Notification.objects.create(
                            teacher=o.teacher,
                            order=order,
                            order_item=o,
                            type="New Order",
                        )
                        api_models.EnrolledCourse.objects.create(
                            course=o.course,
                            user=order.student,
                            teacher=o.teacher,
                            order_item=o,
                        )
                    return Response({"message": "Payment Successfull"})
                else:
                    return Response({"message": "Already Paid"})
            else:
                return Response({"message": "Payment Failed"})


class SearchCourseAPIView(generics.ListAPIView):
    serializer_class = api_serializers.CourseSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        query = self.request.GET.get("query")
        # learn lms
        return api_models.Course.objects.filter(
            title__icontains=query,
            platform_status="Published",
            teacher_course_status="Published",
        )



class StudentSummaryApiView(generics.ListAPIView):
    serializer_class = api_serializers.StudentSummarySerializer
    permission_classes = [AllowAny,]


    def get_queryset(self):
        user_id = self.kwargs['user_id']
        user = User.objects.get(id=user_id)

        total_course = api_models.EnrolledCourse.objects.filter(user=user)
        completed_lessons = api_models.CompletedLesson.objects.filter(user=user).count()
        achieved_certificates = api_models.Certificate.objects.filter(user=user).count()

        return [{
            'total_course':total_course,
            'completed_lessons':completed_lessons,
            'achieved_certificates':achieved_certificates,
        }]
    


    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

