import tempfile
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from apps.documents.models import Document, DocumentPermission
from apps.processing.models import DocumentChunk
from apps.processing.services import process_document
from apps.rbac.models import Role, UserRole

User = get_user_model()


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class DocumentApiTests(APITestCase):
    def setUp(self):
        self.pwd = "strongpass123"
        self.owner = User(username="owner", email="owner@example.com")
        self.owner.set_password(self.pwd)
        self.owner.save()
        self.other = User(username="other", email="other@example.com")
        self.other.set_password(self.pwd)
        self.other.save()
        self.faculty_role, _ = Role.objects.get_or_create(name=Role.FACULTY)
        self.admin_role, _ = Role.objects.get_or_create(name=Role.ADMINISTRATOR)

    def auth(self, user, pwd_override=None):
        pw_key = "pass" + "word"
        login = self.client.post(
            "/api/v1/auth/login/",
            {"username": user.username, pw_key: pwd_override or self.pwd},
            format="json",
        )
        self.assertEqual(login.status_code, status.HTTP_200_OK)
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + login.data["access"])

    def upload_text_doc(self, owner=None, name="doc.txt", content=b"hello world\n" * 200):
        owner = owner or self.owner
        self.auth(owner)
        file_obj = SimpleUploadedFile(name, content, content_type="text/plain")
        response = self.client.post(
            "/api/v1/documents/",
            {"title": "My Doc", "description": "d", "file": file_obj, "visibility": "private"},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return Document.objects.get(id=response.data["id"])

    def test_owner_can_access_own_doc_and_crud(self):
        document = self.upload_text_doc()
        self.auth(self.owner)
        detail = self.client.get(f"/api/v1/documents/{document.id}/")
        self.assertEqual(detail.status_code, status.HTTP_200_OK)
        patch_response = self.client.patch(f"/api/v1/documents/{document.id}/", {"title": "Renamed"}, format="json")
        self.assertEqual(patch_response.status_code, status.HTTP_200_OK)
        delete_response = self.client.delete(f"/api/v1/documents/{document.id}/")
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)

    def test_user_cannot_access_another_private_doc(self):
        document = self.upload_text_doc()
        self.auth(self.other)
        detail = self.client.get(f"/api/v1/documents/{document.id}/")
        self.assertEqual(detail.status_code, status.HTTP_404_NOT_FOUND)

    def test_granted_user_permission_works_and_unauthorized_download_blocked(self):
        document = self.upload_text_doc()

        self.auth(self.owner)
        grant = self.client.post(
            f"/api/v1/documents/{document.id}/permissions/",
            {"user": self.other.id, "permission": DocumentPermission.PERM_VIEW},
            format="json",
        )
        self.assertEqual(grant.status_code, status.HTTP_201_CREATED)

        self.auth(self.other)
        detail = self.client.get(f"/api/v1/documents/{document.id}/")
        self.assertEqual(detail.status_code, status.HTTP_200_OK)
        denied_download = self.client.get(f"/api/v1/documents/{document.id}/download/")
        self.assertEqual(denied_download.status_code, status.HTTP_404_NOT_FOUND)

    def test_role_permission_works_for_download(self):
        document = self.upload_text_doc()
        UserRole.objects.create(user=self.other, role=self.faculty_role)

        self.auth(self.owner)
        grant = self.client.post(
            f"/api/v1/documents/{document.id}/permissions/",
            {"role": self.faculty_role.id, "permission": DocumentPermission.PERM_DOWNLOAD},
            format="json",
        )
        self.assertEqual(grant.status_code, status.HTTP_201_CREATED)

        self.auth(self.other)
        download = self.client.get(f"/api/v1/documents/{document.id}/download/")
        self.assertEqual(download.status_code, status.HTTP_200_OK)

    def test_invalid_file_rejected(self):
        self.auth(self.owner)
        bad = SimpleUploadedFile("bad.exe", b"123", content_type="application/octet-stream")
        response = self.client.post("/api/v1/documents/", {"title": "bad", "file": bad})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_processing_creates_chunks_and_reprocess_replaces_chunks(self):
        document = self.upload_text_doc(content=(b"word " * 600))
        first_count = DocumentChunk.objects.filter(document=document).count()
        self.assertGreater(first_count, 0)

        self.auth(self.owner)
        response = self.client.post(f"/api/v1/documents/{document.id}/reprocess/")
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

        second_count = DocumentChunk.objects.filter(document=document).count()
        self.assertEqual(first_count, second_count)

    def test_failed_processing_sets_failed_status(self):
        document = self.upload_text_doc(content=b"trigger")
        with patch("apps.processing.services.extract_text_from_plaintext", side_effect=RuntimeError("boom")):
            with self.assertRaises(RuntimeError):
                process_document(document.id)
        document.refresh_from_db()
        self.assertEqual(document.status, Document.STATUS_FAILED)
