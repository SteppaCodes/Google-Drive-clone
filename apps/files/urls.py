from django.urls import path

from .views import FileListCreateView, FileUpdateDestroyView

urlpatterns = [
    path('files/', FileListCreateView.as_view()),
    path('files/<id>/', FileUpdateDestroyView.as_view()),
]