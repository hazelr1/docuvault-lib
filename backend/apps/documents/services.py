import hashlib

from django.db.models import Q

from apps.documents.models import Document, DocumentPermission
from apps.rbac.models import UserRole
from apps.rbac.services import is_administrator


def checksum_sha256(file_obj):
    file_obj.seek(0)
    digest = hashlib.sha256()
    for chunk in file_obj.chunks():
        digest.update(chunk)
    file_obj.seek(0)
    return digest.hexdigest()


def user_role_ids(user):
    if not user.is_authenticated:
        return []
    return list(UserRole.objects.filter(user=user).values_list("role_id", flat=True))


def can_view_document(user, document: Document) -> bool:
    if document.owner_id == user.id or is_administrator(user):
        return True
    role_ids = user_role_ids(user)
    return DocumentPermission.objects.filter(
        document=document,
    ).filter(
        Q(user=user) | Q(role_id__in=role_ids)
    ).filter(permission__in=[DocumentPermission.PERM_VIEW, DocumentPermission.PERM_DOWNLOAD, DocumentPermission.PERM_MANAGE]).exists()


def can_download_document(user, document: Document) -> bool:
    if document.owner_id == user.id or is_administrator(user):
        return True
    role_ids = user_role_ids(user)
    return DocumentPermission.objects.filter(
        document=document,
    ).filter(
        Q(user=user) | Q(role_id__in=role_ids)
    ).filter(permission__in=[DocumentPermission.PERM_DOWNLOAD, DocumentPermission.PERM_MANAGE]).exists()


def can_manage_document(user, document: Document) -> bool:
    if document.owner_id == user.id or is_administrator(user):
        return True
    role_ids = user_role_ids(user)
    return DocumentPermission.objects.filter(
        document=document,
    ).filter(
        Q(user=user) | Q(role_id__in=role_ids)
    ).filter(permission=DocumentPermission.PERM_MANAGE).exists()


def authorized_documents_queryset(user):
    if is_administrator(user):
        return Document.objects.all()
    role_ids = user_role_ids(user)
    return Document.objects.filter(
        Q(owner=user)
        | Q(permissions__user=user)
        | Q(permissions__role_id__in=role_ids)
    ).distinct()
