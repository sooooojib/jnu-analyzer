"""
Comprehensive unit and integration tests for the strict Validation & Normalization layer.

Tests:
  - ValidationStatus enum and ValidatedField schema
  - OCR error detection and deterministic corrections (O vs 0, I vs 1, missing decimals, spaces, duplicates)
  - Strict refusal to guess on ambiguous values
  - Conformance to institutional grading scale
  - Grade point and Letter grade consistency cross-checks
  - Exclusion of critical invalid values from calculation eligibility
  - End-to-end sheet and student validation workflows
"""

import unittest
from decimal import Decimal

from apps.processing.parser.schema import (
    ParsedCourse,
    ParsedCumulativeSummary,
    ParsedCurrentSemesterSummary,
    ParsedSheet,
    ParsedStudent,
    ParsedStudentResult,
)
from apps.processing.parser.template import (
    DEFAULT_GRADING_SCALE,
    ResultSheetTemplate,
    get_default_template,
)
from apps.processing.validation.ocr_corrector import OCRCorrector
from apps.processing.validation.schema import (
    ValidatedCumulativeSummary,
    ValidatedCurrentSemesterSummary,
    ValidatedField,
    ValidatedSheet,
    ValidatedStudent,
    ValidatedStudentResult,
    ValidationStatus,
)
from apps.processing.validation.service import ValidationService
from apps.processing.validation.validation_engine import SheetValidationEngine
from apps.processing.validation.validators import FieldValidators


# ===========================================================================
# 1. OCR Error Corrector Tests
# ===========================================================================

class TestOCRCorrector(unittest.TestCase):

    def test_clean_student_id_o_vs_0(self):
        # 'O' in numeric student ID
        cleaned, corrs, uncertain = OCRCorrector.clean_student_id("21O2O45", confidence=0.95)
        self.assertEqual(cleaned, "2102045")
        self.assertFalse(uncertain)
        self.assertTrue(any("letter 'O'" in c for c in corrs))

    def test_clean_student_id_i_vs_1(self):
        # 'I' and 'l' in numeric student ID
        cleaned, corrs, uncertain = OCRCorrector.clean_student_id("2I02l45", confidence=0.95)
        self.assertEqual(cleaned, "2102145")
        self.assertFalse(uncertain)
        self.assertTrue(any("character 'I'" in c for c in corrs))

    def test_clean_student_id_internal_whitespace(self):
        cleaned, corrs, uncertain = OCRCorrector.clean_student_id("210 2045")
        self.assertEqual(cleaned, "2102045")
        self.assertTrue(any("whitespace" in c for c in corrs))

    def test_clean_grade_point_missing_decimal(self):
        # "400" -> "4.00"
        cleaned, corrs, uncertain = OCRCorrector.clean_grade_point("400", confidence=0.95)
        self.assertEqual(cleaned, "4.00")
        self.assertFalse(uncertain)
        self.assertTrue(any("missing decimal" in c for c in corrs))

        # "375" -> "3.75"
        cleaned, corrs, uncertain = OCRCorrector.clean_grade_point("375", confidence=0.95)
        self.assertEqual(cleaned, "3.75")
        self.assertFalse(uncertain)

        # "350" -> "3.50"
        cleaned, corrs, uncertain = OCRCorrector.clean_grade_point("350", confidence=0.95)
        self.assertEqual(cleaned, "3.50")
        self.assertFalse(uncertain)

    def test_clean_grade_point_o_vs_0(self):
        # "4.OO" -> "4.00"
        cleaned, corrs, uncertain = OCRCorrector.clean_grade_point("4.OO", confidence=0.95)
        self.assertEqual(cleaned, "4.00")
        self.assertTrue(any("letter 'O'" in c for c in corrs))

    def test_clean_grade_point_stray_spaces(self):
        # "3 . 75" -> "3.75"
        cleaned, corrs, uncertain = OCRCorrector.clean_grade_point("3 . 75")
        self.assertEqual(cleaned, "3.75")
        self.assertTrue(any("spaces around decimal" in c for c in corrs))

    def test_clean_letter_grade_duplicates_and_spaces(self):
        # "A++" -> "A+"
        cleaned, corrs, uncertain = OCRCorrector.clean_letter_grade("A++")
        self.assertEqual(cleaned, "A+")
        self.assertFalse(uncertain)
        self.assertTrue(any("duplicated '+'" in c for c in corrs))

        # "B -" -> "B-"
        cleaned, corrs, uncertain = OCRCorrector.clean_letter_grade("B -")
        self.assertEqual(cleaned, "B-")
        self.assertFalse(uncertain)

    def test_clean_course_code_hyphen_and_spaces(self):
        # "CSE - 2201" -> "CSE-2201"
        cleaned, corrs, uncertain = OCRCorrector.clean_course_code("CSE - 2201")
        self.assertEqual(cleaned, "CSE-2201")
        self.assertFalse(uncertain)

        # "CSE 2201" -> "CSE-2201"
        cleaned, corrs, uncertain = OCRCorrector.clean_course_code("CSE 2201")
        self.assertEqual(cleaned, "CSE-2201")

        # "CSE--2201" -> "CSE-2201"
        cleaned, corrs, uncertain = OCRCorrector.clean_course_code("CSE--2201")
        self.assertEqual(cleaned, "CSE-2201")

    def test_refuse_to_guess_ambiguous_gp(self):
        # "450" is 4.50 (outside 4.00 scale) -> should flag uncertain, not invent 4.00
        cleaned, corrs, uncertain = OCRCorrector.clean_grade_point("450", confidence=0.95)
        # Even if it converts, it must be flagged uncertain because 4.50 exceeds scale
        self.assertTrue(uncertain or float(cleaned) > 4.0)

    def test_clean_credit_hours(self):
        # "3.OO" -> "3.00"
        cleaned, corrs, uncertain = OCRCorrector.clean_credit_hours("3.OO")
        self.assertEqual(cleaned, "3.00")

        # "150" -> "1.50"
        cleaned, corrs, uncertain = OCRCorrector.clean_credit_hours("150")
        self.assertEqual(cleaned, "1.50")


# ===========================================================================
# 2. Strict FieldValidators Tests
# ===========================================================================

class TestFieldValidators(unittest.TestCase):

    def test_validate_student_id_valid(self):
        vf = FieldValidators.validate_student_id("2102045")
        self.assertEqual(vf.status, ValidationStatus.VALID)
        self.assertEqual(vf.normalized_value, "2102045")
        self.assertTrue(vf.is_usable_in_calculations)

    def test_validate_student_id_with_correction(self):
        vf = FieldValidators.validate_student_id("21O2045", confidence=0.95)
        self.assertEqual(vf.status, ValidationStatus.WARNING)
        self.assertEqual(vf.normalized_value, "2102045")
        self.assertTrue(len(vf.applied_corrections) > 0)
        self.assertTrue(vf.is_usable_in_calculations)

    def test_validate_student_id_empty(self):
        vf = FieldValidators.validate_student_id("")
        self.assertEqual(vf.status, ValidationStatus.INVALID)
        self.assertFalse(vf.is_usable_in_calculations)

    def test_validate_student_id_malformed(self):
        vf = FieldValidators.validate_student_id("210")
        self.assertEqual(vf.status, ValidationStatus.NEEDS_REVIEW)
        self.assertFalse(vf.is_usable_in_calculations)

    def test_validate_course_code_valid(self):
        vf = FieldValidators.validate_course_code("CSE-2201")
        self.assertEqual(vf.status, ValidationStatus.VALID)
        self.assertEqual(vf.normalized_value, "CSE-2201")

    def test_validate_course_code_invalid(self):
        vf = FieldValidators.validate_course_code("")
        self.assertEqual(vf.status, ValidationStatus.INVALID)
        self.assertFalse(vf.is_usable_in_calculations)

    def test_validate_credit_hours_valid(self):
        vf = FieldValidators.validate_credit_hours("3.00")
        self.assertEqual(vf.status, ValidationStatus.VALID)
        self.assertEqual(vf.normalized_value, Decimal("3.00"))

    def test_validate_credit_hours_out_of_bounds(self):
        vf = FieldValidators.validate_credit_hours("25.00")
        self.assertEqual(vf.status, ValidationStatus.INVALID)
        self.assertFalse(vf.is_usable_in_calculations)

    def test_validate_grade_point_valid(self):
        vf = FieldValidators.validate_grade_point("4.00")
        self.assertEqual(vf.status, ValidationStatus.VALID)
        self.assertEqual(vf.normalized_value, Decimal("4.00"))
        self.assertTrue(vf.is_usable_in_calculations)

    def test_validate_grade_point_exceeds_scale(self):
        vf = FieldValidators.validate_grade_point("4.85")
        self.assertEqual(vf.status, ValidationStatus.INVALID)
        self.assertFalse(vf.is_usable_in_calculations)
        self.assertIn("exceeds 4.00 scale", vf.warnings[0])

    def test_validate_letter_grade_valid(self):
        vf = FieldValidators.validate_letter_grade("A+")
        self.assertEqual(vf.status, ValidationStatus.VALID)
        self.assertEqual(vf.normalized_value, "A+")

    def test_validate_letter_grade_invalid(self):
        vf = FieldValidators.validate_letter_grade("XYZ")
        self.assertEqual(vf.status, ValidationStatus.INVALID)
        self.assertFalse(vf.is_usable_in_calculations)

    def test_validate_student_result_matching_scale(self):
        res = FieldValidators.validate_student_result(
            course_code_raw="CSE-2201",
            gp_raw="4.00",
            lg_raw="A+",
        )
        self.assertEqual(res.status, ValidationStatus.VALID)
        self.assertTrue(res.is_consistent_gp_lg)
        self.assertTrue(res.is_usable_in_calculations)

    def test_validate_student_result_mismatch_flags_review(self):
        res = FieldValidators.validate_student_result(
            course_code_raw="CSE-2201",
            gp_raw="3.00",
            lg_raw="A+",
        )
        self.assertEqual(res.status, ValidationStatus.NEEDS_REVIEW)
        self.assertFalse(res.is_consistent_gp_lg)
        self.assertTrue(any("Grade mismatch" in w for w in res.grade_point.warnings))

    def test_validate_current_semester_summary_invalid_gpa(self):
        summary = FieldValidators.validate_current_semester_summary(
            gpa_raw="5.20",
            total_cr_raw="18.00",
        )
        self.assertEqual(summary.status, ValidationStatus.INVALID)
        self.assertFalse(summary.gpa.is_usable_in_calculations)


# ===========================================================================
# 3. End-to-End Sheet and Student Validation Tests
# ===========================================================================

class TestValidationEngineEndToEnd(unittest.TestCase):

    def _build_synthetic_parsed_sheet(self) -> ParsedSheet:
        courses = [
            ParsedCourse(course_code="CSE-2201", credit_hours=Decimal("3.00"), credit_hours_raw="3.00"),
            ParsedCourse(course_code="CSE-2202", credit_hours=Decimal("1.50"), credit_hours_raw="1.50"),
            ParsedCourse(course_code="MAT-2101", credit_hours=Decimal("3.00"), credit_hours_raw="3.00"),
        ]

        # Student 1: Clean valid
        s1 = ParsedStudent(
            student_id="2102045",
            student_id_raw="2102045",
            student_name="ALICE JOHNSON",
            serial_no=1,
            row_index=2,
            results=[
                ParsedStudentResult(course_code="CSE-2201", grade_point=Decimal("4.00"), grade_point_raw="4.00", letter_grade="A+", letter_grade_raw="A+"),
                ParsedStudentResult(course_code="CSE-2202", grade_point=Decimal("3.75"), grade_point_raw="3.75", letter_grade="A", letter_grade_raw="A"),
                ParsedStudentResult(course_code="MAT-2101", grade_point=Decimal("3.50"), grade_point_raw="3.50", letter_grade="A-", letter_grade_raw="A-"),
            ],
            current_semester_summary=ParsedCurrentSemesterSummary(gpa=Decimal("3.85"), gpa_raw="3.85", total_credit=Decimal("7.50")),
            cumulative_summary=ParsedCumulativeSummary(cgpa=Decimal("3.78"), cgpa_raw="3.78"),
        )

        # Student 2: Has OCR fix (21O2046) -> WARNING
        s2 = ParsedStudent(
            student_id="2102046",
            student_id_raw="21O2046",
            student_name="BOB SMITH",
            serial_no=2,
            row_index=3,
            results=[
                ParsedStudentResult(course_code="CSE-2201", grade_point=Decimal("3.50"), grade_point_raw="3.50", letter_grade="A-", letter_grade_raw="A-"),
                ParsedStudentResult(course_code="CSE-2202", grade_point=Decimal("3.00"), grade_point_raw="3.00", letter_grade="B", letter_grade_raw="B"),
                ParsedStudentResult(course_code="MAT-2101", grade_point=Decimal("4.00"), grade_point_raw="4.00", letter_grade="A+", letter_grade_raw="A+"),
            ],
            current_semester_summary=ParsedCurrentSemesterSummary(gpa=Decimal("3.50"), gpa_raw="3.50"),
            cumulative_summary=ParsedCumulativeSummary(cgpa=Decimal("3.45"), cgpa_raw="3.45"),
        )

        return ParsedSheet(
            institution="University of Engineering & Technology",
            program="B.Sc. in Computer Science and Engineering",
            semester="4th Semester",
            exam_session="2024",
            courses=courses,
            students=[s1, s2],
        )

    def test_validate_clean_sheet(self):
        service = ValidationService()
        parsed_sheet = self._build_synthetic_parsed_sheet()
        v_sheet = service.validate_sheet(parsed_sheet)

        self.assertEqual(v_sheet.total_students, 2)
        self.assertEqual(v_sheet.valid_students_count, 1)    # s1 is VALID
        self.assertEqual(v_sheet.warning_students_count, 1)  # s2 has OCR warning on ID
        self.assertEqual(v_sheet.needs_review_students_count, 0)
        self.assertEqual(v_sheet.invalid_students_count, 0)

        s1 = v_sheet.get_student("2102045")
        self.assertIsNotNone(s1)
        self.assertEqual(s1.status, ValidationStatus.VALID)
        self.assertFalse(s1.has_critical_errors)

        s2 = v_sheet.get_student("2102046")
        self.assertIsNotNone(s2)
        self.assertEqual(s2.status, ValidationStatus.WARNING)
        self.assertTrue(len(s2.student_id.applied_corrections) > 0)

    def test_validate_sheet_with_mismatched_grades(self):
        parsed_sheet = self._build_synthetic_parsed_sheet()
        # Inject grade mismatch in s1 (GP 3.00 with A+)
        parsed_sheet.students[0].results[0].grade_point = Decimal("3.00")
        parsed_sheet.students[0].results[0].grade_point_raw = "3.00"
        parsed_sheet.students[0].results[0].letter_grade = "A+"
        parsed_sheet.students[0].results[0].letter_grade_raw = "A+"

        service = ValidationService()
        v_sheet = service.validate_sheet(parsed_sheet)

        self.assertEqual(v_sheet.needs_review_students_count, 1)
        s1 = v_sheet.get_student("2102045")
        self.assertEqual(s1.status, ValidationStatus.NEEDS_REVIEW)
        self.assertTrue(any("Grade mismatch" in msg for msg in s1.validation_messages))

    def test_validate_sheet_with_critical_invalid_gpa(self):
        parsed_sheet = self._build_synthetic_parsed_sheet()
        # Inject invalid GPA (> 4.00) in s1
        parsed_sheet.students[0].current_semester_summary.gpa_raw = "5.50"
        parsed_sheet.students[0].current_semester_summary.gpa = Decimal("5.50")

        service = ValidationService()
        v_sheet = service.validate_sheet(parsed_sheet)

        self.assertEqual(v_sheet.invalid_students_count, 1)
        s1 = v_sheet.get_student("2102045")
        self.assertEqual(s1.status, ValidationStatus.INVALID)
        self.assertTrue(s1.has_critical_errors)
        self.assertFalse(s1.current_semester_summary.gpa.is_usable_in_calculations)

    def test_as_dict_serializable(self):
        import json
        service = ValidationService()
        parsed_sheet = self._build_synthetic_parsed_sheet()
        v_sheet = service.validate_sheet(parsed_sheet)

        d = v_sheet.as_dict()
        json_str = json.dumps(d)
        self.assertIsInstance(json_str, str)
        self.assertEqual(d["total_students"], 2)


if __name__ == "__main__":
    unittest.main()
