from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework import status
from apps.sessions_manager.models import ResultSession
from apps.dataset.models import ResultSheet

SAMPLE_MD = """# Academic Result Sheet
- **Institution**: Jagannath University
- **Department**: Department of Computer Science & Engineering
- **Semester**: BSc 1st Year 2nd Semester Examination 2023
- **Session / Batch**: Session: 2022-23

### Course List:
- CSE-1201: Object Oriented Programming-I (Credit: 3.00)
- CSE-1203: Data structure (Credit: 3.00)

| S/N | Student ID | Student Name | CSE-1201 GP | CSE-1201 LG | CSE-1203 GP | CSE-1203 LG | GPA | CGPA | Result |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 2202001 | ALICE | 4.00 | A+ | 3.75 | A | 3.88 | 3.88 | PASSED |
| 2 | 2202002 | BOB | 3.75 | A | 3.50 | A- | 3.63 | 3.63 | PASSED |
"""

class UploadAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_health_check(self):
        response = self.client.get('/api/health/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['status'], 'healthy')

    def test_upload_valid_markdown_file(self):
        md_file = SimpleUploadedFile("results.md", SAMPLE_MD.encode('utf-8'), content_type="text/markdown")

        response = self.client.post('/api/v1/upload/', {'file': md_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('id', data['data'])
        self.assertEqual(data['data']['file_type'], 'md')

        # Check DB entries exist in both ResultSession and ResultSheet
        session = ResultSession.objects.get(id=data['data']['id'])
        sheet = ResultSheet.objects.get(id=data['data']['id'])
        self.assertEqual(session.status, 'PENDING_VERIFICATION')
        self.assertEqual(sheet.status, ResultSheet.ProcessingStatus.PENDING)
        self.assertEqual(len(session.parsed_dataset.get("students", [])), 2)
        self.assertEqual(len(session.parsed_dataset.get("courses", [])), 2)

    def test_reject_binary_pdf_file(self):
        # Fake PDF with proper magic bytes %PDF-1.4
        pdf_content = b"%PDF-1.4\n%Fake PDF content for test\n%%EOF"
        pdf_file = SimpleUploadedFile("results.pdf", pdf_content, content_type="application/pdf")

        response = self.client.post('/api/v1/upload/', {'file': pdf_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertEqual(data['error_code'], 'file_validation_error')
        self.assertIn("exclusively accepts", data['message'])

    def test_reject_binary_png_image(self):
        # PNG magic bytes
        png_content = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        png_file = SimpleUploadedFile("results.png", png_content, content_type="image/png")

        response = self.client.post('/api/v1/upload/', {'file': png_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertEqual(data['error_code'], 'file_validation_error')

    def test_reject_binary_jpeg_image(self):
        # JPEG magic bytes
        jpeg_content = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00"
        jpeg_file = SimpleUploadedFile("results.jpg", jpeg_content, content_type="image/jpeg")

        response = self.client.post('/api/v1/upload/', {'file': jpeg_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertEqual(data['error_code'], 'file_validation_error')

    def test_reject_empty_file(self):
        empty_file = SimpleUploadedFile("empty.md", b"", content_type="text/markdown")
        response = self.client.post('/api/v1/upload/', {'file': empty_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_upload_process_and_delete_lifecycle(self):
        # 1. Upload Markdown File
        md_file = SimpleUploadedFile("sheet.md", SAMPLE_MD.encode('utf-8'), content_type="text/markdown")
        upload_res = self.client.post('/api/v1/upload/', {'file': md_file}, format='multipart')
        session_id = upload_res.json()['data']['id']

        # 2. Check Status
        status_res = self.client.get(f'/api/v1/sessions/{session_id}/status/')
        self.assertEqual(status_res.status_code, status.HTTP_200_OK)
        self.assertEqual(status_res.json()['data']['status'], 'PENDING_VERIFICATION')

        # 3. Confirm verification
        confirm_res = self.client.post(f'/api/v1/sessions/{session_id}/verification/confirm/')
        self.assertEqual(confirm_res.status_code, status.HTTP_200_OK)
        self.assertEqual(confirm_res.json()['data']['status'], 'VERIFIED')

        # 4. Delete Dataset
        delete_res = self.client.delete(f'/api/v1/sessions/{session_id}/')
        self.assertEqual(delete_res.status_code, status.HTTP_200_OK)

        # 5. Verify records purged
        self.assertFalse(ResultSession.objects.filter(id=session_id).exists())
        self.assertFalse(ResultSheet.objects.filter(id=session_id).exists())
