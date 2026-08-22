"""
Unit and Integration tests for Student Analysis Excel (.xlsx) Export.

Verifies:
  1. build_student_excel: generates valid multi-tab Excel workbook.
  2. Sheet 1 (Student Summary), Sheet 2 (Subject Results), Sheet 3 (Student Statistics).
  3. API endpoint /api/v1/sessions/<id>/export/student/<id>/excel/ status codes and headers.
  4. 404 for non-existent student or invalid session.
"""

import io
import uuid
import openpyxl
from django.test import TestCase
from rest_framework.test import APIClient

from apps.export.data_builders import build_student_report_data
from apps.export.services.student_excel_exporter import build_student_excel
from apps.sessions_manager.models import ResultSession


class TestStudentExcelExport(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.session_id = uuid.uuid4()
        self.courses = [
            {"course_code": "CSE-1101", "course_title": "Intro to CS", "credit_hours": 3.0},
            {"course_code": "CSE-1102", "course_title": "Structured Programming", "credit_hours": 3.0},
            {"course_code": "CSE-1103", "course_title": "Programming Lab", "credit_hours": 1.5},
        ]
        self.students = [
            {
                "student_id": "2102045",
                "student_name": "TANVIRUL ISLAM",
                "serial_no": 1,
                "status": "VALID",
                "results": [
                    {"course_code": "CSE-1101", "grade_point": 4.00, "letter_grade": "A+", "status": "VALID"},
                    {"course_code": "CSE-1102", "grade_point": 3.75, "letter_grade": "A", "status": "VALID"},
                    {"course_code": "CSE-1103", "grade_point": 4.00, "letter_grade": "A+", "status": "VALID"},
                ],
                "current_semester_summary": {
                    "gpa": 3.90,
                    "total_credit": 7.5,
                    "earned_credit": 7.5,
                    "grade_points": 29.25,
                    "result_status": "PASSED",
                    "remarks": "Honours",
                },
                "cumulative_summary": {
                    "cgpa": 3.90,
                    "total_credit": 7.5,
                    "earned_credit": 7.5,
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

    def test_build_student_excel_direct(self):
        report_data = build_student_report_data(self.session, "2102045")
        xlsx_bytes = build_student_excel(report_data)

        self.assertIsInstance(xlsx_bytes, bytes)
        self.assertTrue(len(xlsx_bytes) > 500)
        # XLSX is a zip archive starting with PK\x03\x04
        self.assertTrue(xlsx_bytes.startswith(b"PK\x03\x04"))

        # Load back into openpyxl and inspect sheets
        wb = openpyxl.load_workbook(io.BytesIO(xlsx_bytes))
        self.assertEqual(wb.sheetnames, ["Student Summary", "Subject Results", "Student Statistics"])

        # Sheet 1: Student Summary
        ws1 = wb["Student Summary"]
        self.assertEqual(ws1["B6"].value, "TANVIRUL ISLAM")
        self.assertEqual(ws1["D6"].value, "2102045")
        self.assertEqual(ws1["B11"].value, 3.90)  # Semester GPA
        self.assertEqual(ws1["B13"].value, 3.90)  # Cumulative CGPA

        # Sheet 2: Subject Results
        ws2 = wb["Subject Results"]
        self.assertEqual(ws2["A1"].value, "Course Code")
        self.assertEqual(ws2["B1"].value, "Course Title")
        self.assertEqual(ws2["A2"].value, "CSE-1101")
        self.assertEqual(ws2["D2"].value, 4.00)  # Grade point
        self.assertEqual(ws2["E2"].value, "A+")  # Letter grade

        # Sheet 3: Student Statistics
        ws3 = wb["Student Statistics"]
        self.assertEqual(ws3["A5"].value, "Highest Subject GP")
        self.assertEqual(ws3["B5"].value, 4.00)

    def test_api_export_student_excel_success(self):
        url = f"/api/v1/sessions/{self.session_id}/export/student/2102045/excel/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        self.assertIn("attachment; filename=\"JNU_Student_Analysis_2102045.xlsx\"", response["Content-Disposition"])
        self.assertTrue(response.content.startswith(b"PK\x03\x04"))

    def test_api_export_student_dispatcher_format_param(self):
        url = f"/api/v1/sessions/{self.session_id}/export/student/2102045/"
        response = self.client.get(url, {'format': 'xlsx'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    def test_api_export_student_excel_invalid_student_returns_404(self):
        url = f"/api/v1/sessions/{self.session_id}/export/student/9999999/excel/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)

    def test_api_export_student_excel_invalid_session_returns_404(self):
        fake_session = uuid.uuid4()
        url = f"/api/v1/sessions/{fake_session}/export/student/2102045/excel/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)
