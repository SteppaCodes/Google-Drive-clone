from django.urls import path

from .views import CommentOnFile, DownloadFileAPIView, FileListCreateView, FileUpdateDestroyView, GetFileComments

urlpatterns = [
    path('files/', FileListCreateView.as_view()),
    path('files/<id>/', FileUpdateDestroyView.as_view()),
    path('files/<file_id>/download/', DownloadFileAPIView.as_view()),
    path('files/add-comment/<id>/', CommentOnFile.as_view()),
    path('files/<id>/get-comments/', GetFileComments.as_view()),
]
