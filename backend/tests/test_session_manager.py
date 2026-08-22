import uuid
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from apps.sessions_manager.models import ResultSession

class SessionManagerTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.session = ResultSession.objects.create(
            original_filename="sample_sheet.md",
            file_path="",
            file_type="md",
            file_size_bytes=1024,
            status="PENDING"
        )

    def test_get_session_status(self):
        response = self.client.get(f'/api/v1/sessions/{self.session.id}/status/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['id'], str(self.session.id))
        self.assertEqual(data['data']['status'], 'PENDING')

    def test_get_nonexistent_session(self):
        random_uuid = uuid.uuid4()
        response = self.client.get(f'/api/v1/sessions/{random_uuid}/status/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_session(self):
        response = self.client.delete(f'/api/v1/sessions/{self.session.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(ResultSession.objects.filter(id=self.session.id).exists())
