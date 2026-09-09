import logging

from django.conf import settings

from apps.processing.services import process_document

logger = logging.getLogger(__name__)


def enqueue_document_processing(document_id):
    """Boundary for async processing.

    TODO: replace sync fallback with background worker enqueue when worker infra is configured.
    """
    if settings.DOC_PROCESSING_ASYNC_ENABLED:
        logger.info("DOC_PROCESSING_ASYNC_ENABLED=true but no worker integration configured; using sync fallback")
    process_document(document_id)
