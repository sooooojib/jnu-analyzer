"""
Unit and integration tests for the Result Verification API views.
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from apps.sessions_manager.models import ResultSession
from apps.dataset.models import ResultSheet


class ResultVerificationViewsTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.session = ResultSession.objects.create(
            original_filename="sample_tabulation.pdf",
            file_type="pdf",
            file_size_bytes=10240,
            status="PENDING_VERIFICATION",
            parsed_dataset={
                "institution": "Department of Computer Science & Engineering",
                "semester": "4th Semester",
                "exam_session": "2024",
                "courses": [
                    {"course_code": "CSE-2201", "course_title": "Object Oriented Programming", "credit_hours": 3.0, "column_index": 3},
                    {"course_code": "CSE-2202", "course_title": "Data Structures Lab", "credit_hours": 1.5, "column_index": 4},
                ],
                "students": [
                    {
                        "student_id": "2102045",
                        "student_name": "ALICE JOHNSON",
                        "serial_no": 1,
                        "row_index": 2,
                        "status": "VALID",
                        "confidence": 0.98,
                        "results": [
                            {"course_code": "CSE-2201", "grade_point": 4.00, "letter_grade": "A+", "status": "VALID", "review_reasons": []},
                            {"course_code": "CSE-2202", "grade_point": 3.75, "letter_grade": "A", "status": "VALID", "review_reasons": []},
                        ],
                        "current_semester_summary": {"gpa": 3.90, "total_credit": 4.5, "status": "VALID"},
                        "cumulative_summary": {"cgpa": 3.85, "total_credit": 60.0, "status": "VALID"},
                    },
                    {
                        "student_id": "2102046",
                        "student_name": "BOB SMITH",
                        "serial_no": 2,
                        "row_index": 3,
                        "status": "WARNING",
                        "confidence": 0.95,
                        "results": [
                            {"course_code": "CSE-2201", "grade_point": 3.50, "letter_grade": "A-", "status": "VALID", "review_reasons": []},
                            {"course_code": "CSE-2202", "grade_point": 3.00, "letter_grade": "B", "status": "VALID", "review_reasons": []},
                        ],
                        "current_semester_summary": {"gpa": 3.33, "total_credit": 4.5, "status": "VALID"},
                        "cumulative_summary": {"cgpa": 3.40, "total_credit": 60.0, "status": "VALID"},
                    },
                ],
            },
        )
        ResultSheet.objects.create(
            id=self.session.id,
            session=self.session,
            original_filename="sample_tabulation.pdf",
            file_type="pdf",
            file_size_bytes=10240,
            status=ResultSheet.ProcessingStatus.PROCESSING,
        )

    def test_get_verification_data_success(self):
        url = reverse('processing:dataset_verification', kwargs={'session_id': self.session.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json().get("data", {})
        self.assertIn("summary", data)
        self.assertIn("rows", data)
        self.assertEqual(data["summary"]["total_students"], 2)
        self.assertEqual(data["summary"]["total_courses"], 2)
        self.assertEqual(len(data["rows"]), 4)  # 2 students x 2 courses

    def test_update_verification_cell_grade_point(self):
        url = reverse('processing:update_verification_cell', kwargs={'session_id': self.session.id})
        payload = {
            "student_id": "2102045",
            "course_code": "CSE-2201",
            "field_name": "grade_point",
            "new_value": "3.75",
        }
        response = self.client.patch(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json().get("data", {})
        rows = data.get("rows", [])
        updated_row = next((r for r in rows if r["student_id"] == "2102045" and r["course_code"] == "CSE-2201"), None)
        self.assertIsNotNone(updated_row)
        self.assertEqual(updated_row["grade_point"], 3.75)

    def test_update_verification_cell_student_name(self):
        url = reverse('processing:update_verification_cell', kwargs={'session_id': self.session.id})
        payload = {
            "student_id": "2102045",
            "field_name": "student_name",
            "new_value": "ALICE J. WATSON",
        }
        response = self.client.patch(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json().get("data", {})
        rows = data.get("rows", [])
        updated_row = next((r for r in rows if r["student_id"] == "2102045"), None)
        self.assertIsNotNone(updated_row)
        self.assertEqual(updated_row["student_name"], "ALICE J. WATSON")

    def test_confirm_verification_transitions_to_verified(self):
        url = reverse('processing:confirm_verification', kwargs={'session_id': self.session.id})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.session.refresh_from_db()
        self.assertEqual(self.session.status, "VERIFIED")
        self.assertIn("summary_metrics", self.session.analytics_data)

        # Check sheet status
        sheet = ResultSheet.objects.get(id=self.session.id)
        self.assertEqual(sheet.status, ResultSheet.ProcessingStatus.COMPLETED)
