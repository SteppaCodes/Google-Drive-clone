from django.urls import path

from .views import StarItemAPIView, UnstarItemAPIView, StarredItemsListAPIView

urlpatterns = [
    path('star-item/<id>/', StarItemAPIView.as_view()),
    path('unstar-item/<id>/',  UnstarItemAPIView.as_view()),
    path('starred-items/', StarredItemsListAPIView.as_view()),
]