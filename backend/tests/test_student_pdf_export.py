"""
Unit and Integration tests for Student Analysis PDF Export.

Verifies:
  1. build_student_pdf: generates valid PDF starting with %PDF.
  2. Multi-page table handling, long course titles, long student names.
  3. API endpoint /api/v1/sessions/<id>/export/student/<id>/pdf/ status codes and headers.
  4. 404 for non-existent student or invalid session.
"""

import uuid
from django.test import TestCase
from rest_framework.test import APIClient

from apps.export.data_builders import build_student_report_data
from apps.export.services.student_pdf_exporter import build_student_pdf
from apps.sessions_manager.models import ResultSession


class TestStudentPdfExport(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.session_id = uuid.uuid4()
        self.courses = [
            {"course_code": "CSE-1101", "course_title": "Introduction to Computer Science and Information Technology", "credit_hours": 3.0},
            {"course_code": "CSE-1102", "course_title": "Structured Programming Language with Comprehensive Laboratory Case Studies", "credit_hours": 3.0},
            {"course_code": "CSE-1103", "course_title": "Structured Programming Language Lab Practice", "credit_hours": 1.5},
            {"course_code": "MATH-1104", "course_title": "Differential and Integral Calculus", "credit_hours": 3.0},
            {"course_code": "PHY-1105", "course_title": "Physics for Engineers and Applied Computing Systems", "credit_hours": 3.0},
        ]
        self.students = [
            {
                "student_id": "2102045",
                "student_name": "MOHAMMAD TANVIRUL ISLAM KHAN CHOWDHURY",
                "serial_no": 1,
                "status": "VALID",
                "results": [
                    {"course_code": "CSE-1101", "grade_point": 4.00, "letter_grade": "A+", "status": "VALID"},
                    {"course_code": "CSE-1102", "grade_point": 3.75, "letter_grade": "A", "status": "VALID"},
                    {"course_code": "CSE-1103", "grade_point": 4.00, "letter_grade": "A+", "status": "VALID"},
                    {"course_code": "MATH-1104", "grade_point": 3.50, "letter_grade": "A-", "status": "VALID"},
                    {"course_code": "PHY-1105", "grade_point": 4.00, "letter_grade": "A+", "status": "VALID"},
                ],
                "current_semester_summary": {
                    "gpa": 3.85,
                    "total_credit": 13.5,
                    "earned_credit": 13.5,
                    "grade_points": 51.97,
                    "result_status": "PASSED",
                    "remarks": "Passed with Honours",
                },
                "cumulative_summary": {
                    "cgpa": 3.85,
                    "total_credit": 13.5,
                    "earned_credit": 13.5,
                    "result_status": "PASSED",
                },
            },
            {
                "student_id": "2102046",
                "student_name": "SADIA SULTANA",
                "serial_no": 2,
                "status": "VALID",
                "results": [
                    {"course_code": "CSE-1101", "grade_point": 3.75, "letter_grade": "A", "status": "VALID"},
                    {"course_code": "CSE-1102", "grade_point": 3.50, "letter_grade": "A-", "status": "VALID"},
                    {"course_code": "CSE-1103", "grade_point": 3.75, "letter_grade": "A", "status": "VALID"},
                    {"course_code": "MATH-1104", "grade_point": 3.25, "letter_grade": "B+", "status": "VALID"},
                    {"course_code": "PHY-1105", "grade_point": 3.50, "letter_grade": "A-", "status": "VALID"},
                ],
                "current_semester_summary": {
                    "gpa": 3.52,
                    "total_credit": 13.5,
                    "earned_credit": 13.5,
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

    def test_build_student_pdf_direct(self):
        report_data = build_student_report_data(self.session, "2102045")
        pdf_bytes = build_student_pdf(report_data)

        self.assertIsInstance(pdf_bytes, bytes)
        self.assertTrue(len(pdf_bytes) > 500)
        # PDF magic header
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))

    def test_build_student_pdf_many_subjects_multipage(self):
        # Create student with 25 subjects to force multi-page rendering
        many_courses = [
            {"course_code": f"CSE-1{i:03d}", "course_title": f"Specialized Computing Topic Course Module #{i}", "credit_hours": 3.0}
            for i in range(1, 26)
        ]
        many_results = [
            {"course_code": f"CSE-1{i:03d}", "grade_point": 3.75, "letter_grade": "A", "status": "VALID"}
            for i in range(1, 26)
        ]
        session_large = ResultSession.objects.create(
            id=uuid.uuid4(),
            original_filename="large.md",
            parsed_dataset={
                "institution": "Jagannath University",
                "courses": many_courses,
                "students": [
                    {
                        "student_id": "2109999",
                        "student_name": "MULTI PAGE TEST STUDENT",
                        "results": many_results,
                        "current_semester_summary": {"gpa": 3.75, "total_credit": 75.0},
                    }
                ],
            },
        )
        report_data = build_student_report_data(session_large, "2109999")
        pdf_bytes = build_student_pdf(report_data)

        self.assertTrue(pdf_bytes.startswith(b"%PDF"))
        self.assertTrue(len(pdf_bytes) > 2000)

    def test_api_export_student_pdf_success(self):
        url = f"/api/v1/sessions/{self.session_id}/export/student/2102045/pdf/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn("attachment; filename=\"JNU_Student_Analysis_2102045.pdf\"", response["Content-Disposition"])
        self.assertTrue(response.content.startswith(b"%PDF"))

    def test_api_export_student_pdf_fallback_url(self):
        url = f"/api/v1/sessions/{self.session_id}/export/student/2102045/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")

    def test_api_export_student_pdf_invalid_student_returns_404(self):
        url = f"/api/v1/sessions/{self.session_id}/export/student/9999999/pdf/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)

    def test_api_export_student_pdf_invalid_session_returns_404(self):
        fake_session = uuid.uuid4()
        url = f"/api/v1/sessions/{fake_session}/export/student/2102045/pdf/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)
