"""
Field-specific validation engines for academic result sheet data.

Implements strict validation, grading scale conformance, uncertainty flagging,
and OCR correction tracking for:
  - Student ID, Name, Serial Number
  - Course Code, Credit Hours
  - Grade Points, Letter Grades, GP/LG cross-consistency
  - Current-Semester and Cumulative Summary metrics
"""

from __future__ import annotations

import logging
import re
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional, Tuple

from apps.processing.parser.template import (
    DEFAULT_GRADING_SCALE,
    NON_NUMERIC_GRADES,
    ResultSheetTemplate,
    get_default_template,
)
from .ocr_corrector import OCRCorrector
from .schema import (
    ValidatedCumulativeSummary,
    ValidatedCurrentSemesterSummary,
    ValidatedField,
    ValidatedStudentResult,
    ValidationStatus,
)

logger = logging.getLogger(__name__)


class FieldValidators:
    """
    Collection of strict field validators.
    """

    # -----------------------------------------------------------------------
    # 1. Student ID
    # -----------------------------------------------------------------------

    @staticmethod
    def validate_student_id(
        raw_str: str,
        confidence: float = 1.0,
        template: Optional[ResultSheetTemplate] = None,
    ) -> ValidatedField[str]:
        template = template or get_default_template()
        raw = str(raw_str).strip() if raw_str is not None else ""
        warnings: List[str] = []

        if not raw:
            return ValidatedField(
                field_name="student_id",
                raw_value=raw,
                normalized_value=None,
                confidence=confidence,
                status=ValidationStatus.INVALID,
                error="Student ID is missing or empty.",
                is_usable_in_calculations=False,
            )

        cleaned, corrections, is_uncertain = OCRCorrector.clean_student_id(
            raw, confidence=confidence, min_confidence=template.min_acceptable_confidence
        )

        status = ValidationStatus.VALID
        if corrections:
            status = ValidationStatus.WARNING
            warnings.extend(corrections)

        # Check format against template pattern
        if not re.match(template.student_id_pattern, cleaned):
            if is_uncertain or len(cleaned) < 5:
                return ValidatedField(
                    field_name="student_id",
                    raw_value=raw,
                    normalized_value=cleaned if cleaned else None,
                    confidence=confidence,
                    status=ValidationStatus.NEEDS_REVIEW,
                    warnings=warnings + [f"Student ID '{cleaned}' does not match expected format pattern."],
                    error="Unrecognized Student ID format.",
                    applied_corrections=corrections,
                    is_usable_in_calculations=False,
                )
            else:
                status = ValidationStatus.WARNING
                warnings.append(f"Non-standard Student ID format: '{cleaned}'.")

        if confidence < template.min_acceptable_confidence:
            status = ValidationStatus.NEEDS_REVIEW
            warnings.append(f"Low OCR confidence on Student ID ({confidence:.2f}).")

        return ValidatedField(
            field_name="student_id",
            raw_value=raw,
            normalized_value=cleaned,
            confidence=confidence,
            status=status,
            warnings=warnings,
            applied_corrections=corrections,
            is_usable_in_calculations=True,
        )

    # -----------------------------------------------------------------------
    # 2. Student Name
    # -----------------------------------------------------------------------

    @staticmethod
    def validate_student_name(
        raw_str: str,
        confidence: float = 1.0,
        template: Optional[ResultSheetTemplate] = None,
    ) -> ValidatedField[str]:
        template = template or get_default_template()
        raw = str(raw_str).strip() if raw_str is not None else ""
        warnings: List[str] = []
        corrections: List[str] = []

        if not raw:
            return ValidatedField(
                field_name="student_name",
                raw_value=raw,
                normalized_value="",
                confidence=confidence,
                status=ValidationStatus.WARNING,
                warnings=["Student Name is empty."],
                is_usable_in_calculations=True,
            )

        # Strip leading numbers or noise (e.g. '1. ALICE' -> 'ALICE')
        cleaned = re.sub(r"^[\d\.\-\s]+", "", raw).strip()
        if cleaned != raw:
            corrections.append("Removed leading serial numbers/punctuation from name.")

        cleaned = re.sub(r"\s+", " ", cleaned).upper()
        if len(cleaned) < 2:
            return ValidatedField(
                field_name="student_name",
                raw_value=raw,
                normalized_value=cleaned,
                confidence=confidence,
                status=ValidationStatus.NEEDS_REVIEW,
                warnings=warnings + ["Student Name is too short."],
                applied_corrections=corrections,
                is_usable_in_calculations=True,
            )

        status = ValidationStatus.WARNING if corrections else ValidationStatus.VALID
        if confidence < template.min_acceptable_confidence:
            status = ValidationStatus.NEEDS_REVIEW
            warnings.append(f"Low OCR confidence on Student Name ({confidence:.2f}).")

        return ValidatedField(
            field_name="student_name",
            raw_value=raw,
            normalized_value=cleaned,
            confidence=confidence,
            status=status,
            warnings=warnings + corrections,
            applied_corrections=corrections,
            is_usable_in_calculations=True,
        )

    # -----------------------------------------------------------------------
    # 3. Serial Number
    # -----------------------------------------------------------------------

    @staticmethod
    def validate_serial_no(
        raw_str: str,
        row_idx: int = 0,
        confidence: float = 1.0,
    ) -> ValidatedField[int]:
        raw = str(raw_str).strip() if raw_str is not None else ""
        digits = re.sub(r"[^\d]", "", raw)
        if digits:
            num = int(digits)
            return ValidatedField(
                field_name="serial_no",
                raw_value=raw,
                normalized_value=num,
                confidence=confidence,
                status=ValidationStatus.VALID,
            )
        return ValidatedField(
            field_name="serial_no",
            raw_value=raw,
            normalized_value=None,
            confidence=confidence,
            status=ValidationStatus.WARNING,
            warnings=["No numeric serial number found."],
        )

    # -----------------------------------------------------------------------
    # 4. Course Code
    # -----------------------------------------------------------------------

    @staticmethod
    def validate_course_code(
        raw_str: str,
        confidence: float = 1.0,
        template: Optional[ResultSheetTemplate] = None,
    ) -> ValidatedField[str]:
        template = template or get_default_template()
        raw = str(raw_str).strip() if raw_str is not None else ""
        warnings: List[str] = []

        if not raw:
            return ValidatedField(
                field_name="course_code",
                raw_value=raw,
                normalized_value=None,
                confidence=confidence,
                status=ValidationStatus.INVALID,
                error="Course code is missing.",
                is_usable_in_calculations=False,
            )

        cleaned, corrections, is_uncertain = OCRCorrector.clean_course_code(raw, confidence=confidence)
        status = ValidationStatus.WARNING if corrections else ValidationStatus.VALID

        if is_uncertain:
            if re.match(r"^[A-Z0-9\-_]{4,12}$", cleaned):
                status = ValidationStatus.WARNING
                warnings.append(f"Non-standard course code format: '{cleaned}'.")
            else:
                return ValidatedField(
                    field_name="course_code",
                    raw_value=raw,
                    normalized_value=cleaned,
                    confidence=confidence,
                    status=ValidationStatus.NEEDS_REVIEW,
                    warnings=warnings + [f"Malformed course code: '{raw}'."],
                    applied_corrections=corrections,
                    is_usable_in_calculations=False,
                )

        return ValidatedField(
            field_name="course_code",
            raw_value=raw,
            normalized_value=cleaned,
            confidence=confidence,
            status=status,
            warnings=warnings + corrections,
            applied_corrections=corrections,
            is_usable_in_calculations=True,
        )

    # -----------------------------------------------------------------------
    # 5. Credit Hours
    # -----------------------------------------------------------------------

    @staticmethod
    def validate_credit_hours(
        raw_str: str,
        confidence: float = 1.0,
        template: Optional[ResultSheetTemplate] = None,
    ) -> ValidatedField[Decimal]:
        template = template or get_default_template()
        raw = str(raw_str).strip() if raw_str is not None else ""
        warnings: List[str] = []

        if not raw:
            return ValidatedField(
                field_name="credit_hours",
                raw_value=raw,
                normalized_value=None,
                confidence=confidence,
                status=ValidationStatus.INVALID,
                error="Credit hours value is missing.",
                is_usable_in_calculations=False,
            )

        cleaned, corrections, is_uncertain = OCRCorrector.clean_credit_hours(raw, confidence=confidence)

        try:
            val = Decimal(cleaned).quantize(Decimal("0.01"))
            if val < template.min_credit_hours or val > template.max_credit_hours:
                return ValidatedField(
                    field_name="credit_hours",
                    raw_value=raw,
                    normalized_value=val,
                    confidence=confidence,
                    status=ValidationStatus.INVALID,
                    warnings=warnings + [f"Credit hours {val} outside allowed range [{template.min_credit_hours}, {template.max_credit_hours}]."],
                    error=f"Credit hours {val} outside valid range.",
                    applied_corrections=corrections,
                    is_usable_in_calculations=False,
                )

            status = ValidationStatus.WARNING if corrections else ValidationStatus.VALID
            return ValidatedField(
                field_name="credit_hours",
                raw_value=raw,
                normalized_value=val,
                confidence=confidence,
                status=status,
                warnings=warnings + corrections,
                applied_corrections=corrections,
                is_usable_in_calculations=True,
            )
        except (InvalidOperation, ValueError):
            return ValidatedField(
                field_name="credit_hours",
                raw_value=raw,
                normalized_value=None,
                confidence=confidence,
                status=ValidationStatus.INVALID,
                error=f"Could not parse numeric credit hours from '{raw}'.",
                is_usable_in_calculations=False,
            )

    # -----------------------------------------------------------------------
    # 6. Grade Point (GP)
    # -----------------------------------------------------------------------

    @staticmethod
    def validate_grade_point(
        raw_str: str,
        confidence: float = 1.0,
        template: Optional[ResultSheetTemplate] = None,
    ) -> ValidatedField[Decimal]:
        template = template or get_default_template()
        raw = str(raw_str).strip() if raw_str is not None else ""
        warnings: List[str] = []

        if not raw:
            return ValidatedField(
                field_name="grade_point",
                raw_value=raw,
                normalized_value=None,
                confidence=confidence,
                status=ValidationStatus.NEEDS_REVIEW,
                warnings=["Grade point is empty."],
                is_usable_in_calculations=False,
            )

        cleaned, corrections, is_uncertain = OCRCorrector.clean_grade_point(
            raw, confidence=confidence, min_confidence=template.min_acceptable_confidence
        )

        try:
            val = Decimal(cleaned).quantize(Decimal("0.01"))
            if val < Decimal("0.00") or val > template.max_gpa:
                return ValidatedField(
                    field_name="grade_point",
                    raw_value=raw,
                    normalized_value=val,
                    confidence=confidence,
                    status=ValidationStatus.INVALID,
                    warnings=warnings + [f"Grade point {val} exceeds 4.00 scale."],
                    error=f"Grade point {val} outside 0.00–{template.max_gpa} scale.",
                    applied_corrections=corrections,
                    is_usable_in_calculations=False,
                )

            # Check if value conforms to grading scale allowable grade points
            scale_gps = {scale_val[0] for scale_val in template.grading_scale.values()}
            status = ValidationStatus.WARNING if corrections else ValidationStatus.VALID

            if val not in scale_gps:
                status = ValidationStatus.WARNING
                warnings.append(f"Grade point {val} is non-standard on {template.name} scale.")

            if confidence < template.min_acceptable_confidence:
                status = ValidationStatus.NEEDS_REVIEW
                warnings.append(f"Low OCR confidence on grade point ({confidence:.2f}).")

            return ValidatedField(
                field_name="grade_point",
                raw_value=raw,
                normalized_value=val,
                confidence=confidence,
                status=status,
                warnings=warnings + corrections,
                applied_corrections=corrections,
                is_usable_in_calculations=True,
            )
        except (InvalidOperation, ValueError):
            return ValidatedField(
                field_name="grade_point",
                raw_value=raw,
                normalized_value=None,
                confidence=confidence,
                status=ValidationStatus.INVALID,
                error=f"Could not parse numeric grade point from '{raw}'.",
                is_usable_in_calculations=False,
            )

    # -----------------------------------------------------------------------
    # 7. Letter Grade
    # -----------------------------------------------------------------------

    @staticmethod
    def validate_letter_grade(
        raw_str: str,
        confidence: float = 1.0,
        template: Optional[ResultSheetTemplate] = None,
    ) -> ValidatedField[str]:
        template = template or get_default_template()
        raw = str(raw_str).strip() if raw_str is not None else ""
        warnings: List[str] = []

        if not raw:
            return ValidatedField(
                field_name="letter_grade",
                raw_value=raw,
                normalized_value="",
                confidence=confidence,
                status=ValidationStatus.NEEDS_REVIEW,
                warnings=["Letter grade is empty."],
                is_usable_in_calculations=True,
            )

        cleaned, corrections, is_uncertain = OCRCorrector.clean_letter_grade(raw, confidence=confidence)

        if not template.is_valid_letter_grade(cleaned):
            return ValidatedField(
                field_name="letter_grade",
                raw_value=raw,
                normalized_value=cleaned,
                confidence=confidence,
                status=ValidationStatus.INVALID,
                warnings=warnings + [f"Letter grade '{cleaned}' not recognized on supported scale."],
                error=f"Unsupported letter grade: '{raw}'.",
                applied_corrections=corrections,
                is_usable_in_calculations=False,
            )

        status = ValidationStatus.WARNING if corrections else ValidationStatus.VALID
        if confidence < template.min_acceptable_confidence:
            status = ValidationStatus.NEEDS_REVIEW
            warnings.append(f"Low OCR confidence on letter grade ({confidence:.2f}).")

        return ValidatedField(
            field_name="letter_grade",
            raw_value=raw,
            normalized_value=cleaned,
            confidence=confidence,
            status=status,
            warnings=warnings + corrections,
            applied_corrections=corrections,
            is_usable_in_calculations=True,
        )

    # -----------------------------------------------------------------------
    # 8. Full Student Course Result (GP + LG + Consistency)
    # -----------------------------------------------------------------------

    @classmethod
    def validate_student_result(
        cls,
        course_code_raw: str,
        gp_raw: str,
        lg_raw: str,
        confidence: float = 1.0,
        template: Optional[ResultSheetTemplate] = None,
        cell_coordinates: Optional[Tuple[float, float, float, float]] = None,
    ) -> ValidatedStudentResult:
        template = template or get_default_template()

        vf_code = cls.validate_course_code(course_code_raw, confidence=confidence, template=template)
        vf_gp = cls.validate_grade_point(gp_raw, confidence=confidence, template=template)
        vf_lg = cls.validate_letter_grade(lg_raw, confidence=confidence, template=template)

        # Cross-validate GP and LG consistency against institutional grading scale
        is_consistent = True
        result_status = ValidationStatus.VALID

        if vf_gp.is_invalid or vf_code.is_invalid or vf_lg.is_invalid:
            result_status = ValidationStatus.INVALID
            is_consistent = False
        elif vf_gp.needs_review or vf_lg.needs_review or vf_code.needs_review:
            result_status = ValidationStatus.NEEDS_REVIEW
        elif vf_gp.normalized_value is not None and vf_lg.normalized_value:
            lg = vf_lg.normalized_value
            gp = vf_gp.normalized_value
            if lg in template.grading_scale:
                expected_gp = template.grading_scale[lg][0]
                if abs(gp - expected_gp) > Decimal("0.05"):
                    is_consistent = False
                    result_status = ValidationStatus.NEEDS_REVIEW
                    msg = f"Grade mismatch: '{lg}' expects GP {expected_gp} but found {gp}."
                    vf_gp.warnings.append(msg)
                    vf_lg.warnings.append(msg)
            elif lg in NON_NUMERIC_GRADES and gp != Decimal("0.00"):
                is_consistent = False
                result_status = ValidationStatus.WARNING
                vf_gp.warnings.append(f"Non-numeric grade '{lg}' paired with non-zero GP {gp}.")

        if result_status == ValidationStatus.VALID and (vf_gp.is_warning or vf_lg.is_warning or vf_code.is_warning):
            result_status = ValidationStatus.WARNING

        return ValidatedStudentResult(
            course_code=vf_code,
            grade_point=vf_gp,
            letter_grade=vf_lg,
            is_consistent_gp_lg=is_consistent,
            status=result_status,
            cell_coordinates=cell_coordinates,
        )

    # -----------------------------------------------------------------------
    # 9. Current Semester Summary
    # -----------------------------------------------------------------------

    @classmethod
    def validate_current_semester_summary(
        cls,
        gpa_raw: str,
        total_cr_raw: str = "",
        earned_cr_raw: str = "",
        points_raw: str = "",
        status_raw: str = "",
        remarks_raw: str = "",
        confidence: float = 1.0,
        template: Optional[ResultSheetTemplate] = None,
    ) -> ValidatedCurrentSemesterSummary:
        template = template or get_default_template()

        # GPA validation
        cleaned_gpa, gpa_corrections, _ = OCRCorrector.clean_grade_point(gpa_raw, confidence=confidence)
        vf_gpa = cls._validate_gpa_field(cleaned_gpa, gpa_raw, confidence, template, "Semester GPA", gpa_corrections)

        # Credits & Points validation
        vf_total_cr = cls._validate_credit_field(total_cr_raw, confidence, "Total Credits", max_val=Decimal("35.0"))
        vf_earned_cr = cls._validate_credit_field(earned_cr_raw, confidence, "Earned Credits", max_val=Decimal("35.0"))
        vf_points = cls._validate_numeric_field(points_raw, confidence, "Grade Points", max_val=Decimal("150.0"))
        vf_status = ValidatedField("result_status", status_raw, status_raw.strip(), confidence=confidence)
        vf_remarks = ValidatedField("remarks", remarks_raw, remarks_raw.strip(), confidence=confidence)

        overall_status = ValidationStatus.VALID
        if vf_gpa.is_invalid:
            overall_status = ValidationStatus.INVALID
        elif vf_gpa.needs_review or vf_total_cr.needs_review:
            overall_status = ValidationStatus.NEEDS_REVIEW
        elif vf_gpa.is_warning or vf_total_cr.is_warning:
            overall_status = ValidationStatus.WARNING

        return ValidatedCurrentSemesterSummary(
            gpa=vf_gpa,
            total_credit=vf_total_cr,
            earned_credit=vf_earned_cr,
            grade_points=vf_points,
            result_status=vf_status,
            remarks=vf_remarks,
            status=overall_status,
        )

    # -----------------------------------------------------------------------
    # 10. Cumulative Summary
    # -----------------------------------------------------------------------

    @classmethod
    def validate_cumulative_summary(
        cls,
        cgpa_raw: str,
        total_cr_raw: str = "",
        earned_cr_raw: str = "",
        points_raw: str = "",
        status_raw: str = "",
        remarks_raw: str = "",
        confidence: float = 1.0,
        template: Optional[ResultSheetTemplate] = None,
    ) -> ValidatedCumulativeSummary:
        template = template or get_default_template()

        cleaned_cgpa, cgpa_corrections, _ = OCRCorrector.clean_grade_point(cgpa_raw, confidence=confidence)
        vf_cgpa = cls._validate_gpa_field(cleaned_cgpa, cgpa_raw, confidence, template, "Cumulative CGPA", cgpa_corrections)

        vf_total_cr = cls._validate_credit_field(total_cr_raw, confidence, "Cumulative Total Credits", max_val=Decimal("250.0"))
        vf_earned_cr = cls._validate_credit_field(earned_cr_raw, confidence, "Cumulative Earned Credits", max_val=Decimal("250.0"))
        vf_points = cls._validate_numeric_field(points_raw, confidence, "Cumulative Grade Points", max_val=Decimal("1000.0"))
        vf_status = ValidatedField("result_status", status_raw, status_raw.strip(), confidence=confidence)
        vf_remarks = ValidatedField("remarks", remarks_raw, remarks_raw.strip(), confidence=confidence)

        overall_status = ValidationStatus.VALID
        if vf_cgpa.is_invalid:
            overall_status = ValidationStatus.INVALID
        elif vf_cgpa.needs_review:
            overall_status = ValidationStatus.NEEDS_REVIEW
        elif vf_cgpa.is_warning:
            overall_status = ValidationStatus.WARNING

        return ValidatedCumulativeSummary(
            cgpa=vf_cgpa,
            total_credit=vf_total_cr,
            earned_credit=vf_earned_cr,
            grade_points=vf_points,
            result_status=vf_status,
            remarks=vf_remarks,
            status=overall_status,
        )

    # -----------------------------------------------------------------------
    # Helper Numeric Validators
    # -----------------------------------------------------------------------

    @staticmethod
    def _validate_gpa_field(
        cleaned: str,
        raw: str,
        confidence: float,
        template: ResultSheetTemplate,
        name: str,
        corrections: List[str],
    ) -> ValidatedField[Decimal]:
        if not cleaned:
            return ValidatedField(
                name, raw, None, confidence, ValidationStatus.WARNING,
                warnings=[f"{name} is missing."], is_usable_in_calculations=False
            )
        try:
            val = Decimal(cleaned).quantize(Decimal("0.01"))
            if val < Decimal("0.00") or val > template.max_gpa:
                return ValidatedField(
                    name, raw, val, confidence, ValidationStatus.INVALID,
                    warnings=[f"{name} {val} exceeds 0.00–{template.max_gpa} scale."],
                    error=f"{name} {val} is outside valid range.",
                    applied_corrections=corrections,
                    is_usable_in_calculations=False,
                )
            status = ValidationStatus.WARNING if corrections else ValidationStatus.VALID
            if confidence < template.min_acceptable_confidence:
                status = ValidationStatus.NEEDS_REVIEW
            return ValidatedField(name, raw, val, confidence, status, warnings=corrections, applied_corrections=corrections, is_usable_in_calculations=True)
        except (InvalidOperation, ValueError):
            return ValidatedField(name, raw, None, confidence, ValidationStatus.INVALID, error=f"Could not parse numeric {name} from '{raw}'.", is_usable_in_calculations=False)

    @staticmethod
    def _validate_credit_field(raw_str: str, confidence: float, name: str, max_val: Decimal) -> ValidatedField[Decimal]:
        raw = str(raw_str).strip() if raw_str else ""
        if not raw:
            return ValidatedField(name, raw, None, confidence, ValidationStatus.WARNING, warnings=[f"{name} not present."])
        clean_digits = re.sub(r"[^\d.]", "", raw)
        try:
            val = Decimal(clean_digits).quantize(Decimal("0.01"))
            if val < Decimal("0.00") or val > max_val:
                return ValidatedField(name, raw, val, confidence, ValidationStatus.INVALID, error=f"{name} {val} outside allowed range.", is_usable_in_calculations=False)
            return ValidatedField(name, raw, val, confidence, ValidationStatus.VALID, is_usable_in_calculations=True)
        except (InvalidOperation, ValueError):
            return ValidatedField(name, raw, None, confidence, ValidationStatus.WARNING, warnings=[f"Could not parse {name}."])

    @staticmethod
    def _validate_numeric_field(raw_str: str, confidence: float, name: str, max_val: Decimal) -> ValidatedField[Decimal]:
        raw = str(raw_str).strip() if raw_str else ""
        if not raw:
            return ValidatedField(name, raw, None, confidence, ValidationStatus.VALID)
        clean_digits = re.sub(r"[^\d.]", "", raw)
        try:
            val = Decimal(clean_digits).quantize(Decimal("0.01"))
            return ValidatedField(name, raw, val, confidence, ValidationStatus.VALID)
        except (InvalidOperation, ValueError):
            return ValidatedField(name, raw, None, confidence, ValidationStatus.WARNING, warnings=[f"Could not parse {name}."])
