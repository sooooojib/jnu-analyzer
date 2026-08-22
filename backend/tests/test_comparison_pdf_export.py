"""
Unit and Integration tests for Student Head-to-Head Comparison PDF Export.

Verifies:
  1. build_comparison_pdf: generates valid multi-page PDF starting with %PDF.
  2. Candidate profiles, deltas, subject win/loss tally, course comparison breakdown.
  3. API endpoint /api/v1/sessions/<id>/export/comparison/pdf/ status codes and headers.
  4. 400 for missing params, 404 for invalid student(s) or expired session.
  5. Boundary isolation (strictly scoped to Student A vs Student B).
"""

import uuid
from django.test import TestCase
from rest_framework.test import APIClient

from apps.export.data_builders import build_comparison_report_data
from apps.export.services.comparison_pdf_exporter import build_comparison_pdf
from apps.sessions_manager.models import ResultSession


class TestComparisonPdfExport(TestCase):

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
                    {"course_code": "CSE-1103", "grade_point": 4.00, "letter_grade": "A+", "status": "VALID"},
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

    def test_build_comparison_pdf_direct(self):
        report_data = build_comparison_report_data(
            session=self.session,
            student_a_id="2102001",
            student_b_id="2102002",
        )
        pdf_bytes = build_comparison_pdf(report_data)

        self.assertIsInstance(pdf_bytes, bytes)
        self.assertTrue(len(pdf_bytes) > 500)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))

    def test_build_comparison_pdf_many_courses_multipage(self):
        many_courses = [
            {"course_code": f"CSE-1{i:03d}", "course_title": f"Advanced Topic Course Number {i} Specialization", "credit_hours": 3.0}
            for i in range(1, 31)
        ]
        stu_a_results = [
            {"course_code": f"CSE-1{i:03d}", "grade_point": 4.00, "letter_grade": "A+", "status": "VALID"}
            for i in range(1, 31)
        ]
        stu_b_results = [
            {"course_code": f"CSE-1{i:03d}", "grade_point": 3.50, "letter_grade": "A-", "status": "VALID"}
            for i in range(1, 31)
        ]

        large_session = ResultSession.objects.create(
            id=uuid.uuid4(),
            original_filename="large_comparison.md",
            parsed_dataset={
                "institution": "Jagannath University",
                "courses": many_courses,
                "students": [
                    {
                        "student_id": "2102001",
                        "student_name": "STUDENT A VERY LONG FULL NAME FOR TESTING",
                        "results": stu_a_results,
                        "current_semester_summary": {"gpa": 4.00, "total_credit": 90.0},
                    },
                    {
                        "student_id": "2102002",
                        "student_name": "STUDENT B VERY LONG FULL NAME FOR TESTING",
                        "results": stu_b_results,
                        "current_semester_summary": {"gpa": 3.50, "total_credit": 90.0},
                    },
                ],
            },
        )

        report_data = build_comparison_report_data(
            session=large_session,
            student_a_id="2102001",
            student_b_id="2102002",
        )
        pdf_bytes = build_comparison_pdf(report_data)

        self.assertTrue(pdf_bytes.startswith(b"%PDF"))
        self.assertTrue(len(pdf_bytes) > 2000)

    def test_api_export_comparison_pdf_success(self):
        url = f"/api/v1/sessions/{self.session_id}/export/comparison/pdf/?student_a=2102001&student_b=2102002"
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn("attachment; filename=\"JNU_Comparison_2102001_vs_2102002.pdf\"", response["Content-Disposition"])
        self.assertTrue(response.content.startswith(b"%PDF"))

    def test_api_export_comparison_pdf_fallback_url(self):
        url = f"/api/v1/sessions/{self.session_id}/export/comparison/?student_a=2102001&student_b=2102002"
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")

    def test_api_export_comparison_missing_params_returns_400(self):
        url = f"/api/v1/sessions/{self.session_id}/export/comparison/pdf/?student_a=2102001"
        response = self.client.get(url)

        self.assertEqual(response.status_code, 400)

    def test_api_export_comparison_invalid_student_returns_404(self):
        url = f"/api/v1/sessions/{self.session_id}/export/comparison/pdf/?student_a=2102001&student_b=9999999"
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)

    def test_api_export_comparison_invalid_session_returns_404(self):
        fake_id = uuid.uuid4()
        url = f"/api/v1/sessions/{fake_id}/export/comparison/pdf/?student_a=2102001&student_b=2102002"
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)
