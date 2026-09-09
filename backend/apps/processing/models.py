import uuid

from django.db import models

from apps.documents.models import Document


class DocumentChunk(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="chunks")
    chunk_index = models.PositiveIntegerField()
    content = models.TextField()
    token_count = models.PositiveIntegerField()
    char_start = models.PositiveIntegerField(default=0)
    char_end = models.PositiveIntegerField(default=0)
    page_number = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["chunk_index"]
        indexes = [
            models.Index(fields=["document", "chunk_index"], name="chunk_doc_idx"),
        ]
        constraints = [
            models.UniqueConstraint(fields=["document", "chunk_index"], name="uniq_doc_chunk_index"),
        ]
