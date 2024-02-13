from django.urls import path

from .views import (
    StarItemAPIView,
    UnstarItemAPIView,
    StarredItemsListAPIView,
    CreateShareLinkAPIview,
    GetSharedItemAPIview,
    SearchDriveAPIview,
    UserSharedItemsListCreateAPIview,
    SharedItemDetailAPIView,
)

urlpatterns = [
    path("star-item/<id>/", StarItemAPIView.as_view()),
    path("unstar-item/<id>/", UnstarItemAPIView.as_view()),
    path("starred-items/", StarredItemsListAPIView.as_view()),
    path(
        "create-share-link/<id>/",
        CreateShareLinkAPIview.as_view(),
        name="create-share-link",
    ),
    path(
        "get-shared-item/<type>/<id>",
        GetSharedItemAPIview.as_view(),
        name="get-shared-item",
    ),
    path("search-drive/", SearchDriveAPIview.as_view()),
    path("user-shared-items", UserSharedItemsListCreateAPIview.as_view()),
    path(
        "user-shared-items/<id>/",
        SharedItemDetailAPIView.as_view(),
        name="get-user-shared-item",
    ),
]
