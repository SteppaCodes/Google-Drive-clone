from django.urls import path

from .views import FolderDetailAPIView, FolderListCreateAPIView

urlpatterns = [
    path("folders/", FolderListCreateAPIView.as_view(), name="list-create-folder"),
    path("folders/<id>/", FolderDetailAPIView.as_view()),
]
