import os
import uuid

from django.conf import settings
from django.db import models

from apps.rbac.models import Role


def document_upload_path(instance, filename):
    ext = os.path.splitext(filename)[1].lower()
    return f"documents/{instance.owner_id}/{uuid.uuid4().hex}{ext}"


class Document(models.Model):
    STATUS_PENDING = "pending"
    STATUS_PROCESSING = "processing"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_PROCESSING, "Processing"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_FAILED, "Failed"),
    ]

    VISIBILITY_PRIVATE = "private"
    VISIBILITY_RESTRICTED = "restricted"
    VISIBILITY_CHOICES = [
        (VISIBILITY_PRIVATE, "Private"),
        (VISIBILITY_RESTRICTED, "Restricted"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="documents")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to=document_upload_path)
    mime_type = models.CharField(max_length=100)
    file_size = models.BigIntegerField()
    checksum_sha256 = models.CharField(max_length=64, blank=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING)
    visibility = models.CharField(max_length=16, choices=VISIBILITY_CHOICES, default=VISIBILITY_PRIVATE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["owner", "status", "created_at"], name="doc_owner_status_created_idx"),
        ]


class DocumentPermission(models.Model):
    PERM_VIEW = "view"
    PERM_DOWNLOAD = "download"
    PERM_MANAGE = "manage"

    PERMISSION_CHOICES = [
        (PERM_VIEW, "View"),
        (PERM_DOWNLOAD, "Download"),
        (PERM_MANAGE, "Manage"),
    ]

    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="permissions")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="document_permissions",
        null=True,
        blank=True,
    )
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="document_permissions", null=True, blank=True)
    permission = models.CharField(max_length=16, choices=PERMISSION_CHOICES)
    granted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="granted_document_permissions")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["document", "permission"], name="doc_perm_doc_perm_idx"),
            models.Index(fields=["user", "permission"], name="doc_perm_user_perm_idx"),
            models.Index(fields=["role", "permission"], name="doc_perm_role_perm_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                check=(models.Q(user__isnull=False, role__isnull=True) | models.Q(user__isnull=True, role__isnull=False)),
                name="doc_perm_exactly_one_subject",
            ),
            models.UniqueConstraint(
                fields=["document", "user", "permission"],
                condition=models.Q(user__isnull=False),
                name="uniq_doc_user_permission",
            ),
            models.UniqueConstraint(
                fields=["document", "role", "permission"],
                condition=models.Q(role__isnull=False),
                name="uniq_doc_role_permission",
            ),
        ]
