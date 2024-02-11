from django.urls import path

from .views import (
    StarItemAPIView,
    UnstarItemAPIView,
    StarredItemsListAPIView,
    CreateShareLink,
    GetSharedItem,
    SearchDrive,
)

urlpatterns = [
    path("star-item/<id>/", StarItemAPIView.as_view()),
    path("unstar-item/<id>/", UnstarItemAPIView.as_view()),
    path("starred-items/", StarredItemsListAPIView.as_view()),
    path(
        "create-share-link/<id>/", CreateShareLink.as_view(), name="create-share-link"
    ),
    path(
        "get-shared-item/<type>/<id>", GetSharedItem.as_view(), name="get-shared-item"
    ),
    path("search-drive/", SearchDrive.as_view()),
]
