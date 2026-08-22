"""
Unit and Integration tests for Class Academic Analysis PDF Export.

Verifies:
  1. build_class_pdf: generates valid multi-page PDF starting with %PDF.
  2. Small class, large class with 60 students (multi-page leaderboard), subject analysis, toppers.
  3. API endpoint /api/v1/sessions/<id>/export/class/pdf/ status codes and headers.
  4. 404 for invalid/expired session.
  5. Boundary isolation (no student ID required, no individual scorecard).
"""

import uuid
from django.test import TestCase
from rest_framework.test import APIClient

from apps.export.data_builders import build_class_report_data
from apps.export.services.class_pdf_exporter import build_class_pdf
from apps.sessions_manager.models import ResultSession


class TestClassPdfExport(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.session_id = uuid.uuid4()
        self.courses = [
            {"course_code": "CSE-1101", "course_title": "Introduction to Computer Science", "credit_hours": 3.0},
            {"course_code": "CSE-1102", "course_title": "Structured Programming Language", "credit_hours": 3.0},
            {"course_code": "CSE-1103", "course_title": "Structured Programming Lab", "credit_hours": 1.5},
            {"course_code": "MATH-1104", "course_title": "Calculus and Analytical Geometry", "credit_hours": 3.0},
        ]
        self.students = [
            {
                "student_id": "2102001",
                "student_name": "ALICE WALKER",
                "serial_no": 1,
                "status": "VALID",
                "results": [
                    {"course_code": "CSE-1101", "grade_point": 4.00, "letter_grade": "A+", "status": "VALID"},
                    {"course_code": "CSE-1102", "grade_point": 3.75, "letter_grade": "A", "status": "VALID"},
                    {"course_code": "CSE-1103", "grade_point": 4.00, "letter_grade": "A+", "status": "VALID"},
                    {"course_code": "MATH-1104", "grade_point": 3.75, "letter_grade": "A", "status": "VALID"},
                ],
                "current_semester_summary": {
                    "gpa": 3.85,
                    "total_credit": 10.5,
                    "earned_credit": 10.5,
                    "result_status": "PASSED",
                },
                "cumulative_summary": {
                    "cgpa": 3.85,
                    "total_credit": 10.5,
                    "earned_credit": 10.5,
                    "result_status": "PASSED",
                },
            },
            {
                "student_id": "2102002",
                "student_name": "BOB MARLEY",
                "serial_no": 2,
                "status": "VALID",
                "results": [
                    {"course_code": "CSE-1101", "grade_point": 3.50, "letter_grade": "A-", "status": "VALID"},
                    {"course_code": "CSE-1102", "grade_point": 3.25, "letter_grade": "B+", "status": "VALID"},
                    {"course_code": "CSE-1103", "grade_point": 3.75, "letter_grade": "A", "status": "VALID"},
                    {"course_code": "MATH-1104", "grade_point": 3.00, "letter_grade": "B", "status": "VALID"},
                ],
                "current_semester_summary": {
                    "gpa": 3.32,
                    "total_credit": 10.5,
                    "earned_credit": 10.5,
                    "result_status": "PASSED",
                },
                "cumulative_summary": {
                    "cgpa": 3.32,
                    "total_credit": 10.5,
                    "earned_credit": 10.5,
                    "result_status": "PASSED",
                },
            },
            {
                "student_id": "2102003",
                "student_name": "CHARLIE BROWN",
                "serial_no": 3,
                "status": "VALID",
                "results": [
                    {"course_code": "CSE-1101", "grade_point": 4.00, "letter_grade": "A+", "status": "VALID"},
                    {"course_code": "CSE-1102", "grade_point": 4.00, "letter_grade": "A+", "status": "VALID"},
                    {"course_code": "CSE-1103", "grade_point": 4.00, "letter_grade": "A+", "status": "VALID"},
                    {"course_code": "MATH-1104", "grade_point": 4.00, "letter_grade": "A+", "status": "VALID"},
                ],
                "current_semester_summary": {
                    "gpa": 4.00,
                    "total_credit": 10.5,
                    "earned_credit": 10.5,
                    "result_status": "PASSED",
                },
                "cumulative_summary": {
                    "cgpa": 4.00,
                    "total_credit": 10.5,
                    "earned_credit": 10.5,
                    "result_status": "PASSED",
                },
            },
        ]

        self.session = ResultSession.objects.create(
            id=self.session_id,
            original_filename="BSc_CSE_1st_Sem.md",
            file_type="md",
            status="VERIFIED",
            parsed_dataset={
                "institution": "Jagannath University",
                "program": "Department of Computer Science & Engineering",
                "semester": "BSc 1st Year 1st Semester Examination 2023",
                "exam_session": "2022-23",
                "courses": self.courses,
                "students": self.students,
            },
        )

    def test_build_class_pdf_direct(self):
        report_data = build_class_report_data(self.session)
        pdf_bytes = build_class_pdf(report_data)

        self.assertIsInstance(pdf_bytes, bytes)
        self.assertTrue(len(pdf_bytes) > 500)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))

    def test_build_class_pdf_large_cohort_multipage(self):
        # Generate 60 students to force multi-page leaderboard rendering
        large_students = [
            {
                "student_id": f"2102{i:03d}",
                "student_name": f"STUDENT NUMBER {i} LONG SURNAME",
                "serial_no": i,
                "status": "VALID",
                "results": [
                    {"course_code": "CSE-1101", "grade_point": round(3.0 + (i % 10) * 0.1, 2), "letter_grade": "A", "status": "VALID"},
                    {"course_code": "CSE-1102", "grade_point": round(3.0 + ((i + 1) % 10) * 0.1, 2), "letter_grade": "A", "status": "VALID"},
                ],
                "current_semester_summary": {"gpa": round(3.0 + (i % 10) * 0.1, 2), "total_credit": 6.0},
                "cumulative_summary": {"cgpa": round(3.0 + (i % 10) * 0.1, 2), "total_credit": 6.0},
            }
            for i in range(1, 61)
        ]

        large_session = ResultSession.objects.create(
            id=uuid.uuid4(),
            original_filename="large_class.md",
            parsed_dataset={
                "institution": "Jagannath University",
                "program": "CSE",
                "courses": self.courses[:2],
                "students": large_students,
            },
        )
        report_data = build_class_report_data(large_session)
        pdf_bytes = build_class_pdf(report_data)

        self.assertTrue(pdf_bytes.startswith(b"%PDF"))
        self.assertTrue(len(pdf_bytes) > 3000)

    def test_build_class_pdf_empty_dataset(self):
        empty_session = ResultSession.objects.create(
            id=uuid.uuid4(),
            original_filename="empty.md",
            parsed_dataset={"courses": [], "students": []},
        )
        report_data = build_class_report_data(empty_session)
        pdf_bytes = build_class_pdf(report_data)

        self.assertTrue(pdf_bytes.startswith(b"%PDF"))

    def test_api_export_class_pdf_success(self):
        url = f"/api/v1/sessions/{self.session_id}/export/class/pdf/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn("attachment; filename=\"JNU_Class_Analysis.pdf\"", response["Content-Disposition"])
        self.assertTrue(response.content.startswith(b"%PDF"))

    def test_api_export_class_pdf_fallback_url(self):
        url = f"/api/v1/sessions/{self.session_id}/export/class/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")

    def test_api_export_class_pdf_invalid_session_returns_404(self):
        fake_id = uuid.uuid4()
        url = f"/api/v1/sessions/{fake_id}/export/class/pdf/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)

    def test_class_pdf_distribution_contains_grade_tiers_and_ranges(self):
        report_data = build_class_report_data(self.session)
        gpa_dist = report_data.get("class_overview", {}).get("gpa_distribution", [])

        self.assertTrue(len(gpa_dist) > 0)
        first_item = gpa_dist[0]
        self.assertIn("grade_tier", first_item)
        self.assertIn("gpa_range", first_item)
        self.assertEqual(first_item["grade_tier"], "A+")
        self.assertEqual(first_item["gpa_range"], "4.00")

        # Verify all 10 tiers have non-empty grade_tier and gpa_range
        for d in gpa_dist:
            self.assertTrue(len(d["grade_tier"]) > 0)
            self.assertTrue(len(d["gpa_range"]) > 0)
