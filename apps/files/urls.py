from django.urls import path

from .views import FileListCreateView, FileUpdateDestroyView, DownloadFileAPIView

urlpatterns = [
    path('files/', FileListCreateView.as_view()),
    path('files/<id>/', FileUpdateDestroyView.as_view()),
    path('files/<file_id>/download/', DownloadFileAPIView.as_view())
]