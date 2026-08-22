"""
End-to-end integration test suite verifying the complete lifecycle of Result Analyzer:
Upload -> Process -> Verification -> Correction -> Confirm -> Scorecard -> Analytics -> Comparison -> Debug -> Purge.
"""

from django.test import TestCase, Client
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from apps.sessions_manager.models import ResultSession
from apps.dataset.models import ResultSheet


class EndToEndIntegrationTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def test_full_pipeline_end_to_end(self):
        # 1. Upload Markdown Document
        md_content = """# Result Sheet
- **Institution**: Department of Computer Science & Engineering
- **Semester**: 2nd Semester
- **Session / Batch**: 2022-23

### Course List:
- CSE-1201: OOP-I (Credit: 3.00)
- CSEL-1202: OOP-I Lab (Credit: 1.50)

| S/N | Student ID | Student Name | CSE-1201 GP | CSE-1201 LG | CSEL-1202 GP | CSEL-1202 LG | GPA | CGPA | Result |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 2102045 | ALICE JOHNSON | 4.00 | A+ | 3.75 | A | 3.92 | 3.88 | PASSED |
| 2 | 2102046 | BOB SMITH | 3.50 | A- | 3.00 | B | 3.33 | 3.40 | PASSED |
""".encode('utf-8')
        uploaded_file = SimpleUploadedFile("4th_sem_results.md", md_content, content_type="text/markdown")
        
        upload_resp = self.client.post("/api/v1/upload/", {"file": uploaded_file})
        self.assertEqual(upload_resp.status_code, status.HTTP_201_CREATED)
        upload_data = upload_resp.json()["data"]
        session_id = upload_data["id"]

        # Verify Session & ResultSheet created
        self.assertTrue(ResultSession.objects.filter(id=session_id).exists())
        self.assertTrue(ResultSheet.objects.filter(id=session_id).exists())

        # 2. Process Dataset (Deterministic Markdown Parsing)
        process_resp = self.client.post(f"/api/v1/sessions/{session_id}/process/")
        self.assertEqual(process_resp.status_code, status.HTTP_200_OK)
        session = ResultSession.objects.get(id=session_id)
        self.assertEqual(session.status, "PENDING_VERIFICATION")

        # Seed parsed_dataset with integration test fixture
        session.parsed_dataset = {
            "institution": "Department of Computer Science & Engineering",
            "semester": "2nd Semester",
            "exam_session": "2022-23",
            "courses": [
                {"course_code": "CSE-1201", "course_title": "OOP-I", "credit_hours": 3.0, "column_index": 3},
                {"course_code": "CSEL-1202", "course_title": "OOP-I Lab", "credit_hours": 1.5, "column_index": 4},
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
                        {"course_code": "CSE-1201", "grade_point": 4.00, "letter_grade": "A+", "status": "VALID", "review_reasons": []},
                        {"course_code": "CSEL-1202", "grade_point": 3.75, "letter_grade": "A", "status": "VALID", "review_reasons": []},
                    ],
                    "current_semester_summary": {"gpa": 3.92, "total_credit": 4.5, "earned_credit": 4.5, "status": "VALID"},
                    "cumulative_summary": {"cgpa": 3.88, "total_credit": 25.0, "status": "VALID"},
                },
                {
                    "student_id": "2102046",
                    "student_name": "BOB SMITH",
                    "serial_no": 2,
                    "row_index": 3,
                    "status": "VALID",
                    "confidence": 0.95,
                    "results": [
                        {"course_code": "CSE-1201", "grade_point": 3.50, "letter_grade": "A-", "status": "VALID", "review_reasons": []},
                        {"course_code": "CSEL-1202", "grade_point": 3.00, "letter_grade": "B", "status": "VALID", "review_reasons": []},
                    ],
                    "current_semester_summary": {"gpa": 3.33, "total_credit": 4.5, "earned_credit": 4.5, "status": "VALID"},
                    "cumulative_summary": {"cgpa": 3.40, "total_credit": 25.0, "status": "VALID"},
                },
            ],
        }
        session.save(update_fields=["parsed_dataset"])

        # 3. Retrieve Verification Data
        verif_resp = self.client.get(f"/api/v1/sessions/{session_id}/verification/")
        self.assertEqual(verif_resp.status_code, status.HTTP_200_OK)
        verif_data = verif_resp.json()["data"]
        self.assertIn("rows", verif_data)
        self.assertIn("summary", verif_data)
        self.assertEqual(verif_data["summary"]["total_students"], 2)

        # 4. Inline Edit / Correction on a cell
        update_payload = {
            "student_id": "2102045",
            "course_code": "CSE-2201",
            "field_name": "grade_point",
            "new_value": 3.75,
        }
        update_resp = self.client.patch(
            f"/api/v1/sessions/{session_id}/verification/update-cell/",
            data=update_payload,
            content_type="application/json"
        )
        self.assertEqual(update_resp.status_code, status.HTTP_200_OK)

        # 5. Confirm Verification Gate
        confirm_resp = self.client.post(f"/api/v1/sessions/{session_id}/verification/confirm/")
        self.assertEqual(confirm_resp.status_code, status.HTTP_200_OK)
        session.refresh_from_db()
        self.assertEqual(session.status, "VERIFIED")

        # 6. Student Scorecard Lookup
        scorecard_resp = self.client.get(f"/api/v1/sessions/{session_id}/students/2102045/")
        self.assertEqual(scorecard_resp.status_code, status.HTTP_200_OK)
        scorecard = scorecard_resp.json()["data"]
        self.assertEqual(scorecard["student_id"], "2102045")
        self.assertEqual(scorecard["student_name"], "ALICE JOHNSON")
        self.assertIn("semester_result", scorecard)
        self.assertIn("cumulative_result", scorecard)
        self.assertIn("individual_analysis", scorecard)

        # 7. Cohort Analytics Query
        analytics_resp = self.client.get(f"/api/v1/sessions/{session_id}/analytics/")
        self.assertEqual(analytics_resp.status_code, status.HTTP_200_OK)
        analytics = analytics_resp.json()["data"]
        self.assertIn("class_analysis", analytics)
        self.assertIn("subject_analysis", analytics)
        self.assertIn("cumulative_analysis", analytics)

        # 8. 2-Student Comparison Query
        compare_resp = self.client.get(
            f"/api/v1/sessions/{session_id}/compare/?student_a=2102045&student_b=2102046"
        )
        self.assertEqual(compare_resp.status_code, status.HTTP_200_OK)
        comparison = compare_resp.json()["data"]
        self.assertEqual(comparison["student_a"]["id"], "2102045")
        self.assertEqual(comparison["student_b"]["id"], "2102046")
        self.assertIn("deltas", comparison)
        self.assertIn("course_comparison", comparison)
        self.assertIn("subject_tally", comparison)

        # 9. Purge Session and Temporary Storage
        purge_resp = self.client.delete(f"/api/v1/sessions/{session_id}/")
        self.assertEqual(purge_resp.status_code, status.HTTP_200_OK)
        self.assertFalse(ResultSession.objects.filter(id=session_id).exists())

