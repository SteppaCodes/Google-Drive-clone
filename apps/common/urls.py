from django.urls import path

from .views import (
    StarItemAPIView,
    UnstarItemAPIView,
    StarredItemsListAPIView,
    CreateShareLinkAPIView,
    GetSharedItemAPIView,
    SearchDriveAPIView,
    UserSharedItemsListCreateAPIView,
    SharedItemDetailAPIView,
)

urlpatterns = [
    path("star-item/<id>/", StarItemAPIView.as_view()),
    path("unstar-item/<id>/", UnstarItemAPIView.as_view()),
    path("starred-items/", StarredItemsListAPIView.as_view()),
    path(
        "create-share-link/<id>/",
        CreateShareLinkAPIView.as_view(),
        name="create-share-link",
    ),
    path(
        "get-shared-item/<type>/<idb64>",
        GetSharedItemAPIView.as_view(),
        name="get-shared-item",
    ),
    path("search-drive/", SearchDriveAPIView.as_view()),
    path("user-shared-items", UserSharedItemsListCreateAPIView.as_view()),
    path(
        "user-shared-items/<id>/",
        SharedItemDetailAPIView.as_view(),
        name="get-user-shared-item",
    ),
]
