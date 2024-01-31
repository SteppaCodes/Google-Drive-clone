from django.urls import path

from .views import FileListCreateView

urlpatterns = [
    path('files/', FileListCreateView.as_view()),
]