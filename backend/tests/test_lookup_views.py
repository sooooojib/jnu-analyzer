"""
Unit and integration tests for Student ID lookup and dataset isolation.
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from apps.sessions_manager.models import ResultSession


class StudentLookupViewsTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        # Dataset 1 (Session A)
        self.session_a = ResultSession.objects.create(
            original_filename="dataset_a.pdf",
            file_type="pdf",
            file_size_bytes=10240,
            status="VERIFIED",
            parsed_dataset={
                "institution": "University of Engineering & Technology",
                "semester": "4th Semester",
                "exam_session": "2024",
                "courses": [
                    {"course_code": "CSE-2201", "course_title": "Object Oriented Programming", "credit_hours": 3.0},
                    {"course_code": "CSE-2202", "course_title": "Data Structures Lab", "credit_hours": 1.5},
                ],
                "students": [
                    {
                        "student_id": "2102045",
                        "student_name": "ALICE JOHNSON",
                        "serial_no": 1,
                        "status": "VALID",
                        "confidence": 0.98,
                        "results": [
                            {"course_code": "CSE-2201", "grade_point": 4.00, "letter_grade": "A+", "status": "VALID"},
                            {"course_code": "CSE-2202", "grade_point": 3.75, "letter_grade": "A", "status": "VALID"},
                        ],
                        "current_semester_summary": {"gpa": 3.92, "total_credit": 4.5, "earned_credit": 4.5, "result_status": "PASSED"},
                        "cumulative_summary": {"cgpa": 3.88, "total_credit": 60.0, "earned_credit": 60.0, "result_status": "PASSED"},
                    },
                    {
                        "student_id": "2102046",
                        "student_name": "BOB SMITH",
                        "serial_no": 2,
                        "status": "VALID",
                        "confidence": 0.95,
                        "results": [
                            {"course_code": "CSE-2201", "grade_point": 3.50, "letter_grade": "A-", "status": "VALID"},
                            {"course_code": "CSE-2202", "grade_point": 3.00, "letter_grade": "B", "status": "VALID"},
                        ],
                        "current_semester_summary": {"gpa": 3.33, "total_credit": 4.5, "earned_credit": 4.5, "result_status": "PASSED"},
                        "cumulative_summary": {"cgpa": 3.40, "total_credit": 60.0, "earned_credit": 60.0, "result_status": "PASSED"},
                    },
                ],
            },
        )

        # Dataset 2 (Session B) - Separate isolated dataset
        self.session_b = ResultSession.objects.create(
            original_filename="dataset_b.pdf",
            file_type="pdf",
            file_size_bytes=10240,
            status="VERIFIED",
            parsed_dataset={
                "institution": "University of Engineering & Technology",
                "semester": "5th Semester",
                "exam_session": "2024",
                "courses": [
                    {"course_code": "CSE-3101", "course_title": "Database Systems", "credit_hours": 3.0},
                ],
                "students": [
                    {
                        "student_id": "2002099",
                        "student_name": "CHARLIE BROWN",
                        "serial_no": 1,
                        "status": "VALID",
                        "confidence": 0.99,
                        "results": [
                            {"course_code": "CSE-3101", "grade_point": 3.75, "letter_grade": "A", "status": "VALID"},
                        ],
                        "current_semester_summary": {"gpa": 3.75, "total_credit": 3.0, "earned_credit": 3.0, "result_status": "PASSED"},
                        "cumulative_summary": {"cgpa": 3.70, "total_credit": 90.0, "earned_credit": 90.0, "result_status": "PASSED"},
                    },
                ],
            },
        )

    def test_lookup_student_exact_match(self):
        url = reverse('processing:student_scorecard', kwargs={'session_id': self.session_a.id, 'student_id': '2102045'})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json().get("data", {})
        self.assertEqual(data["student_id"], "2102045")
        self.assertEqual(data["student_name"], "ALICE JOHNSON")
        self.assertEqual(len(data["course_grades"]), 2)
        self.assertEqual(data["semester_result"]["gpa"], 3.92)
        self.assertEqual(data["cumulative_result"]["cgpa"], 3.88)
        # Alice is rank #1 in both subjects
        self.assertEqual(data["course_grades"][0]["subject_rank"], 1)
        self.assertEqual(data["course_grades"][1]["subject_rank"], 1)

    def test_lookup_student_subject_ranks(self):
        # Bob has lower GP in both subjects, so Bob MUST be rank #2 in both subjects
        url = reverse('processing:student_scorecard', kwargs={'session_id': self.session_a.id, 'student_id': '2102046'})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json().get("data", {})
        self.assertEqual(data["student_id"], "2102046")
        self.assertEqual(data["course_grades"][0]["subject_rank"], 2)
        self.assertEqual(data["course_grades"][1]["subject_rank"], 2)

    def test_lookup_student_with_leading_trailing_spaces(self):
        url = reverse('processing:student_scorecard', kwargs={'session_id': self.session_a.id, 'student_id': '  2102045  '})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json().get("data", {})
        self.assertEqual(data["student_id"], "2102045")
        self.assertEqual(data["student_name"], "ALICE JOHNSON")

    def test_lookup_student_with_stray_internal_space(self):
        url = reverse('processing:student_scorecard', kwargs={'session_id': self.session_a.id, 'student_id': '210 2045'})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json().get("data", {})
        self.assertEqual(data["student_id"], "2102045")

    def test_lookup_student_not_found_in_session(self):
        url = reverse('processing:student_scorecard', kwargs={'session_id': self.session_a.id, 'student_id': '9999999'})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        json_resp = response.json()
        self.assertIn("not found in this result sheet", json_resp.get("message", ""))

    def test_dataset_isolation_does_not_leak_other_session_students(self):
        # Student 2002099 belongs to Session B, searching in Session A MUST return 404
        url = reverse('processing:student_scorecard', kwargs={'session_id': self.session_a.id, 'student_id': '2002099'})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("not found in this result sheet", response.json().get("message", ""))

    def test_lookup_does_not_guess_approximate_id(self):
        # 210204 matches prefix of 2102045, but MUST NOT be guessed
        url = reverse('processing:student_scorecard', kwargs={'session_id': self.session_a.id, 'student_id': '210204'})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
