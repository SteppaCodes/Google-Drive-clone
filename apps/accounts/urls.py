from . views import RegisteruserView, LoginUserView, LogoutUserAPIView
from rest_framework_simplejwt.views import TokenRefreshView

from django.urls import path 

urlpatterns = [
    path('register/', RegisteruserView.as_view()),
    path('login/', LoginUserView.as_view()),
    path("logout/", LogoutUserAPIView.as_view()),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]