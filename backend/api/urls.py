from api import views as  api_views
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
urlpatterns = [

    path('user-ko/refresh-token/', TokenRefreshView.as_view()),
    path('user-ko/token/', api_views.MyTokenObtainPairView.as_view()),
    path('register-user/', api_views.RegisterView.as_view(), name='register-user')
]