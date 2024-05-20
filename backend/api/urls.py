from api import views as api_views
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    # Authentication Endpoints
    path("user/token-refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path(
        "user/token/",
        api_views.MyTokenObtainPairView.as_view(),
        name="token_obtain_pair",
    ),
    path("user/register/", api_views.RegisterView.as_view(), name="register_user"),
    path(
        "user/password-reset/<str:email>/",
        api_views.PasswordResetEmailVerifyView.as_view(),
        name="password_reset_email_verify",
    ),
    path(
        "user/password-change/",
        api_views.PasswordChangeApiView.as_view(),
        name="password_change",
    ),
    # Core Endpoints
    path("course/category/", api_views.CategoryListAPIView.as_view()),
    path("course/course-list/", api_views.CourseListAPIView.as_view()),
    path("course/course-detail/<slug>/", api_views.CourseDetailAPIView.as_view()),
    path("course/cart/", api_views.CartAPIView.as_view()),
    path("course/cart-list/<cart_id>/", api_views.CartListAPIView.as_view()),
    path("cart/stats/<cart_id>/", api_views.CartStatsAPIView.as_view()),
    path(
        "course/cart-item-delete/<cart_id>/<item_id>/",
        api_views.CartItemDeleteAPIView.as_view(),
    ),
    path("order/create-order/", api_views.CreateOrderAPIView.as_view()),
    path("order/checkout/<oid>/", api_views.CheckoutAPIView.as_view()),
    path(
        "payment/stripe-checkout/<order_oid>/",
        api_views.StripeCheckoutAPIView.as_view(),
    ),
    path("payment/payment-sucess/", api_views.PaymentSuccessAPIView.as_view()),
]
