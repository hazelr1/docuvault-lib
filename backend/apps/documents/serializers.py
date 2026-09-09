import os

from django.conf import settings
from rest_framework import serializers

from apps.documents.models import Document, DocumentPermission
from apps.documents.services import checksum_sha256
from apps.rbac.models import Role


class DocumentSerializer(serializers.ModelSerializer):
    owner = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Document
        fields = [
            "id",
            "owner",
            "title",
            "description",
            "file",
            "mime_type",
            "file_size",
            "checksum_sha256",
            "status",
            "visibility",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "owner", "mime_type", "file_size", "checksum_sha256", "status", "created_at", "updated_at"]

    def validate_file(self, file_obj):
        ext = os.path.splitext(file_obj.name)[1].lower()
        if ext not in settings.ALLOWED_DOCUMENT_EXTENSIONS:
            raise serializers.ValidationError("Unsupported file extension")
        if file_obj.size > settings.MAX_DOCUMENT_UPLOAD_SIZE:
            raise serializers.ValidationError("File too large")
        content_type = getattr(file_obj, "content_type", "")
        if content_type and content_type not in settings.ALLOWED_DOCUMENT_MIME_TYPES:
            raise serializers.ValidationError("Unsupported MIME type")
        return file_obj

    def create(self, validated_data):
        file_obj = validated_data["file"]
        validated_data["mime_type"] = getattr(file_obj, "content_type", "") or "application/octet-stream"
        validated_data["file_size"] = file_obj.size
        validated_data["checksum_sha256"] = checksum_sha256(file_obj)
        validated_data["owner"] = self.context["request"].user
        return super().create(validated_data)


class DocumentPermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentPermission
        fields = ["id", "document", "user", "role", "permission", "granted_by", "created_at"]
        read_only_fields = ["id", "document", "granted_by", "created_at"]

    def validate(self, attrs):
        user = attrs.get("user")
        role = attrs.get("role")
        if bool(user) == bool(role):
            raise serializers.ValidationError("Provide exactly one of user or role")
        return attrs
