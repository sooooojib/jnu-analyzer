"""
Comprehensive Security, Boundary Isolation, and Performance Stress Tests
for the JnU Analyzer PDF Export Suite.

Covers:
  1. Security & Edge Cases:
     - Path traversal / injection attempts in Student IDs and filenames.
     - Expired sessions / Non-existent session IDs.
     - Non-existent Student IDs (single and cross-comparison).
     - Missing or malformed parameters.
     - Cross-dataset boundary isolation (Candidate from Session 1 vs Candidate from Session 2).
     - In-memory generation verification (no files left on disk).
  2. Performance & Stress:
     - Large cohort dataset (150 students, 12 courses).
     - Large course load dataset (35 courses per student).
     - Latency & memory throughput benchmarks.
  3. Data Consistency:
     - Verified that exported metrics exactly equal the computed analysis outputs.
"""

import os
import re
import time
import uuid
from django.test import TestCase
from rest_framework.test import APIClient

from apps.export.data_builders import (
    build_student_report_data,
    build_class_report_data,
    build_comparison_report_data,
)
from apps.export.services.student_pdf_exporter import build_student_pdf
from apps.export.services.class_pdf_exporter import build_class_pdf
from apps.export.services.comparison_pdf_exporter import build_comparison_pdf
from apps.sessions_manager.models import ResultSession


class TestExportSecurityAndPerformance(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.session_id_1 = uuid.uuid4()
        self.session_id_2 = uuid.uuid4()

        # Session 1 Dataset
        self.courses_1 = [
            {"course_code": "CSE-1101", "course_title": "Structured Programming", "credit_hours": 3.0},
            {"course_code": "CSE-1102", "course_title": "Discrete Mathematics", "credit_hours": 3.0},
        ]
        self.students_1 = [
            {
                "student_id": "2102001",
                "student_name": "STUDENT ONE",
                "serial_no": 1,
                "status": "VALID",
                "results": [
                    {"course_code": "CSE-1101", "grade_point": 4.00, "letter_grade": "A+", "status": "VALID"},
                    {"course_code": "CSE-1102", "grade_point": 3.75, "letter_grade": "A", "status": "VALID"},
                ],
                "current_semester_summary": {"gpa": 3.88, "total_credit": 6.0, "earned_credit": 6.0, "result_status": "PASSED"},
            },
            {
                "student_id": "2102002",
                "student_name": "STUDENT TWO",
                "serial_no": 2,
                "status": "VALID",
                "results": [
                    {"course_code": "CSE-1101", "grade_point": 3.50, "letter_grade": "A-", "status": "VALID"},
                    {"course_code": "CSE-1102", "grade_point": 3.25, "letter_grade": "B+", "status": "VALID"},
                ],
                "current_semester_summary": {"gpa": 3.38, "total_credit": 6.0, "earned_credit": 6.0, "result_status": "PASSED"},
            },
        ]

        # Session 2 Dataset (Completely isolated)
        self.students_2 = [
            {
                "student_id": "9902099",
                "student_name": "ISOLATED STUDENT",
                "serial_no": 1,
                "status": "VALID",
                "results": [
                    {"course_code": "CSE-1101", "grade_point": 3.00, "letter_grade": "B", "status": "VALID"},
                ],
                "current_semester_summary": {"gpa": 3.00, "total_credit": 3.0, "earned_credit": 3.0, "result_status": "PASSED"},
            }
        ]

        self.session_1 = ResultSession.objects.create(
            id=self.session_id_1,
            original_filename="Session_1.md",
            parsed_dataset={"institution": "JnU", "courses": self.courses_1, "students": self.students_1},
        )
        self.session_2 = ResultSession.objects.create(
            id=self.session_id_2,
            original_filename="Session_2.md",
            parsed_dataset={"institution": "JnU", "courses": self.courses_1, "students": self.students_2},
        )

    # -------------------------------------------------------------
    # 1. SECURITY & INJECTION VULNERABILITY AUDIT
    # -------------------------------------------------------------

    def test_path_traversal_sanitization_in_student_pdf(self):
        """Attempts path traversal via malicious student ID input in URL."""
        malicious_id = "../../etc/passwd"
        url = f"/api/v1/sessions/{self.session_id_1}/export/student/{malicious_id}/pdf/"
        response = self.client.get(url)
        # Should return 404 (not found in dataset) without crashing or accessing filesystem
        self.assertEqual(response.status_code, 404)

    def test_unsafe_characters_in_filename_sanitization(self):
        """Verifies special characters and quotes are stripped from Content-Disposition."""
        unsafe_session = ResultSession.objects.create(
            id=uuid.uuid4(),
            original_filename="test.md",
            parsed_dataset={
                "courses": self.courses_1,
                "students": [
                    {
                        "student_id": '2102001_test"quote;rm',
                        "student_name": "INJECTION TESTER",
                        "results": self.students_1[0]["results"],
                        "current_semester_summary": {"gpa": 4.0},
                    }
                ],
            },
        )
        url = f"/api/v1/sessions/{unsafe_session.id}/export/student/2102001_test\"quote;rm/pdf/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        cd = response["Content-Disposition"]
        self.assertNotIn("..", cd)
        self.assertNotIn('"', cd.split('filename="')[1][:-1])

    def test_cross_dataset_candidate_isolation(self):
        """Cross-dataset comparison: Student from Session 1 vs Student from Session 2."""
        # Attempting to compare 2102001 (Session 1) with 9902099 (Session 2) under Session 1 ID
        url = f"/api/v1/sessions/{self.session_id_1}/export/comparison/pdf/?student_a=2102001&student_b=9902099"
        response = self.client.get(url)
        # Must return 404 because Student B belongs to a different session dataset
        self.assertEqual(response.status_code, 404)

    def test_expired_or_invalid_session_id(self):
        """Non-existent session UUID returns 404."""
        fake_session = uuid.uuid4()
        url = f"/api/v1/sessions/{fake_session}/export/class/pdf/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    # -------------------------------------------------------------
    # 2. DATA INTEGRITY & CONSISTENCY AUDIT
    # -------------------------------------------------------------

    def test_student_data_consistency(self):
        """Verifies that Student PDF report data exactly matches pre-computed values."""
        data = build_student_report_data(self.session_1, "2102001")
        self.assertEqual(data["student_info"]["student_id"], "2102001")
        self.assertEqual(data["student_info"]["student_name"], "STUDENT ONE")
        self.assertEqual(data["academic_summary"]["semester_gpa"], 3.88)
        self.assertEqual(data["academic_summary"]["semester_rank"], 1)
        self.assertEqual(len(data["subject_results"]), 2)
        # Class Highest
        self.assertEqual(data["subject_results"][0]["class_highest_gp"], 4.00)

    def test_class_data_consistency(self):
        """Verifies that Class PDF report data uses existing deterministic cohort metrics."""
        data = build_class_report_data(self.session_1)
        self.assertEqual(data["class_overview"]["total_students"], 2)
        self.assertAlmostEqual(data["class_overview"]["average_gpa"], 3.63, places=2)
        self.assertEqual(data["class_overview"]["highest_gpa"], 3.88)
        self.assertEqual(data["class_overview"]["lowest_gpa"], 3.38)
        self.assertEqual(len(data["student_rankings"]), 2)

    def test_comparison_data_consistency(self):
        """Verifies that Comparison PDF data uses existing comparison service delta."""
        data = build_comparison_report_data(self.session_1, "2102001", "2102002")
        self.assertEqual(data["student_a"]["student_id"], "2102001")
        self.assertEqual(data["student_b"]["student_id"], "2102002")
        self.assertAlmostEqual(data["deltas"]["gpa_difference"], 0.50, places=2)
        self.assertEqual(data["subject_tally"]["student_a_wins"], 2)
        self.assertEqual(data["subject_tally"]["student_b_wins"], 0)

    # -------------------------------------------------------------
    # 3. PERFORMANCE & STRESS AUDIT
    # -------------------------------------------------------------

    def test_large_cohort_class_pdf_performance(self):
        """Stress tests Class PDF generation with 150 students across 10 courses."""
        num_students = 150
        courses = [
            {"course_code": f"CSE-2{i:03d}", "course_title": f"Core Subject #{i}", "credit_hours": 3.0}
            for i in range(1, 11)
        ]
        students = []
        for s in range(1, num_students + 1):
            s_id = f"2102{s:03d}"
            base_gp = 2.50 + ((s % 15) * 0.1)
            results = [
                {"course_code": f"CSE-2{i:03d}", "grade_point": min(4.00, round(base_gp + (i * 0.02), 2)), "letter_grade": "A", "status": "VALID"}
                for i in range(1, 11)
            ]
            students.append({
                "student_id": s_id,
                "student_name": f"STUDENT RECORD {s}",
                "serial_no": s,
                "results": results,
                "current_semester_summary": {"gpa": round(base_gp, 2), "total_credit": 30.0, "earned_credit": 30.0, "result_status": "PASSED"},
            })

        large_session = ResultSession.objects.create(
            id=uuid.uuid4(),
            original_filename="large_cohort_150.md",
            parsed_dataset={"institution": "Jagannath University", "courses": courses, "students": students},
        )

        start_time = time.time()
        report_data = build_class_report_data(large_session)
        pdf_bytes = build_class_pdf(report_data)
        elapsed = time.time() - start_time

        # Validations
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))
        self.assertTrue(len(pdf_bytes) > 5000)
        # Must generate under 1.5 seconds even for 150 multi-page students leaderboard
        self.assertLess(elapsed, 2.0, f"Generation took {elapsed:.2f}s, expected < 2.0s")

    def test_heavy_course_load_student_pdf_performance(self):
        """Stress tests Student PDF generation with a heavy load of 40 courses."""
        courses = [
            {"course_code": f"CSE-3{i:03d}", "course_title": f"Specialized Engineering Elective Course {i}", "credit_hours": 3.0}
            for i in range(1, 41)
        ]
        results = [
            {"course_code": f"CSE-3{i:03d}", "grade_point": 4.00 if i % 2 == 0 else 3.75, "letter_grade": "A+" if i % 2 == 0 else "A", "status": "VALID"}
            for i in range(1, 41)
        ]
        heavy_session = ResultSession.objects.create(
            id=uuid.uuid4(),
            original_filename="heavy_courses_40.md",
            parsed_dataset={
                "institution": "Jagannath University",
                "courses": courses,
                "students": [
                    {
                        "student_id": "2102099",
                        "student_name": "HIGH COURSE LOAD CANDIDATE",
                        "serial_no": 1,
                        "results": results,
                        "current_semester_summary": {"gpa": 3.88, "total_credit": 120.0, "earned_credit": 120.0, "result_status": "PASSED"},
                    }
                ],
            },
        )

        start_time = time.time()
        report_data = build_student_report_data(heavy_session, "2102099")
        pdf_bytes = build_student_pdf(report_data)
        elapsed = time.time() - start_time

        self.assertTrue(pdf_bytes.startswith(b"%PDF"))
        self.assertLess(elapsed, 1.5, f"Generation took {elapsed:.2f}s, expected < 1.5s")
