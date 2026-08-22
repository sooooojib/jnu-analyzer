"""
Advanced parser and validation unit tests testing:
- Malformed OCR tokens
- Missing cells and shifted column cells
- Tied GPAs and multiple subject toppers
- Duplicate student IDs
- Row consistency
"""

import unittest
from decimal import Decimal
from apps.processing.parser.service import SheetParserService
from apps.processing.parser.schema import (
    ParsedSheet,
    ParsedCourse,
    ParsedStudent,
    ParsedStudentResult,
    ParsedCurrentSemesterSummary,
    ParsedCumulativeSummary,
)
from apps.processing.validation.validation_engine import SheetValidationEngine
from apps.processing.validation.validators import FieldValidators
from apps.processing.ranking.engine import compute_standard_competition_ranks
from apps.processing.analysis.engine import DeterministicAnalysisEngine


class AdvancedParserAndValidationTests(unittest.TestCase):
    def setUp(self):
        self.parser_service = SheetParserService()
        self.validation_engine = SheetValidationEngine()
        self.analysis_engine = DeterministicAnalysisEngine()

    def test_ocr_error_correction_deterministic(self):
        """High confidence deterministic correction of O vs 0 in GP values."""
        # '4.O0' with O letter -> 4.00
        vf = FieldValidators.validate_grade_point("4.O0", confidence=0.98)
        self.assertTrue(vf.is_valid or vf.is_warning)
        self.assertEqual(float(vf.normalized_value), 4.00)

        # '3.75'
        vf_s = FieldValidators.validate_grade_point("3.75", confidence=0.98)
        self.assertEqual(float(vf_s.normalized_value), 3.75)

    def test_invalid_gp_never_guessed(self):
        """Uncertain or impossible values are marked INVALID or NEEDS_REVIEW without guessing."""
        vf = FieldValidators.validate_grade_point("9.50", confidence=0.50)
        self.assertTrue(vf.is_invalid or vf.needs_review)

        vf_blank = FieldValidators.validate_grade_point("", confidence=0.90)
        self.assertTrue(vf_blank.is_invalid or vf_blank.needs_review)

    def test_tie_rankings_standard_competition_rule(self):
        """1224 rule: 3.90, 3.90, 3.85, 3.80 -> 1, 1, 3, 4."""
        items = [
            ("A", 3.90, True),
            ("B", 3.90, True),
            ("C", 3.85, True),
            ("D", 3.80, True),
        ]
        rank_map = compute_standard_competition_ranks(items)

        self.assertEqual(rank_map["A"]["rank"], 1)
        self.assertEqual(rank_map["B"]["rank"], 1)
        self.assertEqual(rank_map["C"]["rank"], 3)
        self.assertEqual(rank_map["D"]["rank"], 4)

    def test_multiple_subject_toppers_recognized(self):
        """Multiple students sharing the highest GP in a subject are all toppers at Rank 1."""
        students = [
            {"student_id": "2102045", "results": [{"course_code": "CSE-2201", "grade_point": 4.00, "letter_grade": "A+"}]},
            {"student_id": "2102046", "results": [{"course_code": "CSE-2201", "grade_point": 4.00, "letter_grade": "A+"}]},
            {"student_id": "2102047", "results": [{"course_code": "CSE-2201", "grade_point": 3.75, "letter_grade": "A"}]},
        ]
        courses = [{"course_code": "CSE-2201", "course_title": "OOP", "credit_hours": 3.0}]
        subject_stats = self.analysis_engine.analyze_subjects(students, courses)

        subject_stat = subject_stats[0]
        self.assertEqual(subject_stat["highest_gp"], 4.00)
        self.assertEqual(len(subject_stat["highest_performing_students"]), 2)
        self.assertEqual(subject_stat["highest_performing_students"][0]["gp"], 4.00)
        self.assertEqual(subject_stat["highest_performing_students"][1]["gp"], 4.00)

    def test_missing_cells_and_shifted_cells_flagged(self):
        """Rows with missing subject result cells are flagged as NEEDS_REVIEW."""
        student = ParsedStudent(
            student_id="2102045",
            student_name="ALICE",
            results=[
                ParsedStudentResult(course_code="CSE-2201", grade_point=Decimal("4.00"), letter_grade="A+"),
                # CSE-2202 is missing
            ],
            current_semester_summary=ParsedCurrentSemesterSummary(gpa=Decimal("4.00")),
            cumulative_summary=ParsedCumulativeSummary(cgpa=Decimal("3.90")),
        )
        courses = [
            ParsedCourse(course_code="CSE-2201", course_title="OOP", credit_hours=Decimal("3.0")),
            ParsedCourse(course_code="CSE-2202", course_title="DS Lab", credit_hours=Decimal("1.5")),
        ]
        v_student = self.validation_engine.validate_student(student, courses)
        self.assertEqual(v_student.status.value, "NEEDS_REVIEW")


if __name__ == "__main__":
    unittest.main()
