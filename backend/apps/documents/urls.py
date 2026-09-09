from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.documents.views import (
    DocumentPermissionDeleteAPIView,
    DocumentPermissionListCreateAPIView,
    DocumentViewSet,
)

router = DefaultRouter()
router.register("", DocumentViewSet, basename="documents")

urlpatterns = [
    path("", include(router.urls)),
    path("<uuid:pk>/permissions/", DocumentPermissionListCreateAPIView.as_view(), name="document-permissions"),
    path(
        "<uuid:pk>/permissions/<int:permission_id>/",
        DocumentPermissionDeleteAPIView.as_view(),
        name="document-permission-delete",
    ),
]
