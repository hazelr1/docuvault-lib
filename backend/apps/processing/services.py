import logging
from django.db import transaction

from apps.documents.models import Document
from apps.processing.chunkers.simple_chunker import chunk_text
from apps.processing.cleaners.text_cleaner import clean_text
from apps.processing.extractors.pdf_extractor import extract_text_from_pdf
from apps.processing.extractors.text_extractor import extract_text_from_plaintext
from apps.processing.models import DocumentChunk

logger = logging.getLogger(__name__)


def _estimate_tokens(text: str) -> int:
    return max(1, len(text.split()))


def process_document(document_id):
    document = Document.objects.get(pk=document_id)
    document.status = Document.STATUS_PROCESSING
    document.save(update_fields=["status", "updated_at"])

    try:
        filename = (document.file.name or "").lower()
        if document.mime_type == "application/pdf" or filename.endswith(".pdf"):
            pages = extract_text_from_pdf(document.file)
        else:
            pages = extract_text_from_plaintext(document.file)

        chunks_to_create = []
        chunk_index = 0
        for page in pages:
            cleaned = clean_text(page["text"])
            for part in chunk_text(cleaned):
                chunks_to_create.append(
                    DocumentChunk(
                        document=document,
                        chunk_index=chunk_index,
                        content=part["content"],
                        token_count=_estimate_tokens(part["content"]),
                        char_start=part["char_start"],
                        char_end=part["char_end"],
                        page_number=page["page_number"],
                    )
                )
                chunk_index += 1

        with transaction.atomic():
            DocumentChunk.objects.filter(document=document).delete()
            if chunks_to_create:
                DocumentChunk.objects.bulk_create(chunks_to_create)

        document.status = Document.STATUS_COMPLETED
        document.save(update_fields=["status", "updated_at"])
    except Exception:
        logger.exception("Document processing failed for document_id=%s", document.id)
        document.status = Document.STATUS_FAILED
        document.save(update_fields=["status", "updated_at"])
        raise
