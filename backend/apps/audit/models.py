from django.conf import settings
from django.db import models


class AccessLog(models.Model):
    ACTION_CHOICES = [
        ("upload", "Upload"),
        ("view", "View"),
        ("download", "Download"),
        ("delete", "Delete"),
        ("reprocess", "Reprocess"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    document_id = models.UUIDField(null=True, blank=True)
    action = models.CharField(max_length=32, choices=ACTION_CHOICES)
    outcome = models.CharField(max_length=32, default="success")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["user", "created_at"], name="audit_user_created_idx")]
