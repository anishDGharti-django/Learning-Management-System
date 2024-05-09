from api import views as api_views
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('user/token-refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('user/token/', api_views.MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('user/register/', api_views.RegisterView.as_view(), name='register_user'),
    path('user/password-reset-email/<str:email>/', api_views.PasswordResetEmailVerifyView.as_view(), name='password_reset_email_verify'),
    path('user/password-change/', api_views.PasswordChangeApiView.as_view(), name='password_change'),
]
