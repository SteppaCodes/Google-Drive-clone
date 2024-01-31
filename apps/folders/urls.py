from  django.urls import path

from .views import FolderListCreateAPIView

urlpatterns = [
    path('folders/',  FolderListCreateAPIView.as_view(), name='list-create-folder'),
]