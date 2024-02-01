from django.urls import path

from .views import StarItemAPIView, UnstarItemAPIView

urlpatterns = [
    path('star-item/<id>/', StarItemAPIView.as_view()),
    path('unstar-item/<id>/',  UnstarItemAPIView.as_view())
]