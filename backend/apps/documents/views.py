from django.http import FileResponse
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.models import AccessLog
from apps.documents.models import Document, DocumentPermission
from apps.documents.serializers import DocumentPermissionSerializer, DocumentSerializer
from apps.documents.services import (
    authorized_documents_queryset,
    can_download_document,
    can_manage_document,
    can_view_document,
)
from apps.processing.tasks import enqueue_document_processing


class DocumentViewSet(viewsets.ModelViewSet):
    serializer_class = DocumentSerializer

    def get_queryset(self):
        return authorized_documents_queryset(self.request.user).order_by("-created_at")

    def perform_create(self, serializer):
        document = serializer.save()
        AccessLog.objects.create(user=self.request.user, document_id=document.id, action="upload")
        enqueue_document_processing(document.id)

    def get_object(self):
        queryset = Document.objects.all()
        obj = self.get_queryset().filter(pk=self.kwargs["pk"]).first()
        if obj is None:
            target = queryset.filter(pk=self.kwargs["pk"]).first()
            if target and not can_view_document(self.request.user, target):
                raise NotFound()
            raise NotFound()
        return obj

    def partial_update(self, request, *args, **kwargs):
        document = self.get_object()
        if document.owner_id != request.user.id and not can_manage_document(request.user, document):
            raise PermissionDenied("Not allowed to update document")
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        document = self.get_object()
        if document.owner_id != request.user.id and not can_manage_document(request.user, document):
            raise PermissionDenied("Not allowed to delete document")
        AccessLog.objects.create(user=request.user, document_id=document.id, action="delete")
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=["get"], url_path="download")
    def download(self, request, pk=None):
        document = Document.objects.filter(pk=pk).first()
        if not document:
            raise NotFound()
        if not can_download_document(request.user, document):
            raise NotFound()
        AccessLog.objects.create(user=request.user, document_id=document.id, action="download")
        return FileResponse(document.file.open("rb"), as_attachment=True, filename=document.title)

    @action(detail=True, methods=["post"], url_path="reprocess")
    def reprocess(self, request, pk=None):
        document = self.get_object()
        if not can_manage_document(request.user, document):
            raise PermissionDenied("Not allowed to reprocess document")
        enqueue_document_processing(document.id)
        AccessLog.objects.create(user=request.user, document_id=document.id, action="reprocess")
        return Response({"status": "queued"}, status=status.HTTP_202_ACCEPTED)


class DocumentPermissionListCreateAPIView(APIView):
    def get_document(self, request, pk):
        document = Document.objects.filter(pk=pk).first()
        if not document or not can_view_document(request.user, document):
            raise NotFound()
        if not can_manage_document(request.user, document):
            raise PermissionDenied("Not allowed to manage permissions")
        return document

    def get(self, request, pk):
        document = self.get_document(request, pk)
        serializer = DocumentPermissionSerializer(document.permissions.all(), many=True)
        return Response(serializer.data)

    def post(self, request, pk):
        document = self.get_document(request, pk)
        serializer = DocumentPermissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(document=document, granted_by=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class DocumentPermissionDeleteAPIView(APIView):
    def delete(self, request, pk, permission_id):
        document = Document.objects.filter(pk=pk).first()
        if not document or not can_manage_document(request.user, document):
            raise NotFound()
        permission = DocumentPermission.objects.filter(id=permission_id, document=document).first()
        if not permission:
            raise NotFound()
        permission.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
