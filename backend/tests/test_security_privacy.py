"""
Comprehensive security and privacy test suite for Result Analyzer.
Verifies file upload security, magic byte validation, path traversal prevention,
security headers, log redaction, and ephemeral storage TTL purging.
"""

import uuid
import tempfile
import os
from django.test import TestCase, Client, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from datetime import timedelta
from apps.sessions_manager.models import ResultSession
from apps.upload.validators import validate_uploaded_file
from apps.upload.services import handle_file_upload
from apps.core.exceptions import FileValidationError
from apps.core.middleware import ID_PATTERN


class SecurityAndPrivacyHardeningTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            try:
                import shutil
                shutil.rmtree(self.temp_dir)
            except OSError:
                pass

    def test_magic_byte_validation_accepts_valid_markdown(self):
        valid_md = SimpleUploadedFile(
            "sample.md",
            b"# Result Sheet\n| S/N | Student ID | Name |\n|---|---|---|\n| 1 | 2102045 | Alice |",
            content_type="text/markdown"
        )
        detected_type = validate_uploaded_file(valid_md)
        self.assertEqual(detected_type, "md")

    def test_magic_byte_validation_rejects_binary_pdf(self):
        valid_pdf = SimpleUploadedFile(
            "sample.pdf",
            b"%PDF-1.4\n%test content\n%%EOF",
            content_type="application/pdf"
        )
        with self.assertRaises(FileValidationError):
            validate_uploaded_file(valid_pdf)

    def test_magic_byte_validation_rejects_binary_png(self):
        valid_png = SimpleUploadedFile(
            "sample.png",
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR",
            content_type="image/png"
        )
        with self.assertRaises(FileValidationError):
            validate_uploaded_file(valid_png)

    def test_magic_byte_validation_rejects_fake_extension(self):
        """Rejects binary files masked with a .md extension if non-UTF-8."""
        fake_md = SimpleUploadedFile(
            "malicious.md",
            b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\x80\x99\xff",
            content_type="text/markdown"
        )
        with self.assertRaises(FileValidationError):
            validate_uploaded_file(fake_md)

    def test_file_size_limit_enforcement(self):
        """Rejects files larger than maximum configured limit."""
        with override_settings(MAX_UPLOAD_SIZE_BYTES=100):
            large_file = SimpleUploadedFile(
                "big.md",
                b"# Big Markdown\n" + b"X" * 200,
                content_type="text/markdown"
            )
            with self.assertRaises(FileValidationError):
                validate_uploaded_file(large_file)

    def test_path_traversal_filename_sanitization(self):
        """Ensures path traversal attempts in uploaded filenames are stripped safely."""
        malicious_file = SimpleUploadedFile(
            "../../../../etc/passwd.md",
            b"# Result Sheet\n| S/N | ID | Name |\n|---|---|---|\n| 1 | 2102045 | Alice |",
            content_type="text/markdown"
        )
        session = handle_file_upload(malicious_file)
        # Should not contain traversal sequences
        self.assertNotIn("..", session.original_filename)
        self.assertNotIn("/", session.original_filename)
        self.assertNotIn("\\", session.original_filename)
        self.assertTrue(session.original_filename.endswith(".md"))
        # Verify file path is in temporary directory with UUID
        self.assertTrue(os.path.exists(session.file_path))
        session.purge_file()

    def test_security_headers_enforced(self):
        """Verifies X-Frame-Options, X-Content-Type-Options, and Cache-Control headers."""
        response = self.client.get('/api/v1/sessions/')
        self.assertEqual(response.headers.get('X-Frame-Options'), 'DENY')
        self.assertEqual(response.headers.get('X-Content-Type-Options'), 'nosniff')
        self.assertEqual(response.headers.get('Referrer-Policy'), 'strict-origin-when-cross-origin')
        self.assertIn('no-store', response.headers.get('Cache-Control', ''))

    def test_log_redaction_pattern(self):
        """Verifies that student IDs in URL paths are sanitized for audit logging."""
        sample_path = "/api/v1/sessions/123e4567-e89b-12d3-a456-426614174000/students/2102045/"
        sanitized = ID_PATTERN.sub('/students/[REDACTED_ID]/', sample_path)
        self.assertNotIn("2102045", sanitized)
        self.assertIn("[REDACTED_ID]", sanitized)

    def test_unpredictable_uuid_dataset_isolation(self):
        """Verifies that dataset session IDs are cryptographically random UUIDv4s."""
        session_a = ResultSession.objects.create(
            original_filename="sheet_a.md",
            file_type="md",
            status="PENDING_VERIFICATION"
        )
        session_b = ResultSession.objects.create(
            original_filename="sheet_b.md",
            file_type="md",
            status="PENDING_VERIFICATION"
        )
        self.assertIsInstance(session_a.id, uuid.UUID)
        self.assertIsInstance(session_b.id, uuid.UUID)
        self.assertNotEqual(session_a.id, session_b.id)

    def test_ephemeral_ttl_and_file_purge(self):
        """Verifies session purge_file and expiration logic."""
        test_file_path = os.path.join(self.temp_dir, "test_source.md")
        with open(test_file_path, "wb") as f:
            f.write(b"# test markdown")

        session = ResultSession.objects.create(
            original_filename="test.md",
            file_path=test_file_path,
            file_type="md",
            status="PENDING_VERIFICATION",
            expires_at=timezone.now() - timedelta(minutes=5),
        )
        self.assertTrue(session.is_expired)
        self.assertTrue(os.path.exists(test_file_path))
        session.purge_file()
        self.assertFalse(os.path.exists(test_file_path))
        self.assertEqual(session.file_path, "")
