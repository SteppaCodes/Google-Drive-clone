from .views import (
    RegisterUserAPIView, 
    LoginUserAPIView, 
    LogoutUserAPIView,
    ResetPasswordRequestAPIView,
    ResetPasswordConfirm,
    SetNewPasswordAPIView
    )
from rest_framework_simplejwt.views import token_refresh

from django.urls import path 

urlpatterns = [
    path('register/', RegisterUserAPIView.as_view()),
    path('login/', LoginUserAPIView.as_view(), name="login"),
    path("logout/", LogoutUserAPIView.as_view(),  name='logout'),
    path('reset-password-request/', ResetPasswordRequestAPIView.as_view()),
    path('reset-password-confirm/<uidb64>/<token>/', ResetPasswordConfirm.as_view(), name='reset-password-confirm'),
    path('set-new-password/', SetNewPasswordAPIView.as_view()),

    path('token/refresh/', token_refresh, name='token_refresh'),
]