from . views import RegisteruserView, LoginUserView

from django.urls import path 

urlpatterns = [
    path('register/', RegisteruserView.as_view()),
    path('login/', LoginUserView.as_view()),
]