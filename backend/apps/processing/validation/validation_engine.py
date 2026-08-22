"""
Validation Engine for academic result sheets.

Orchestrates full sheet and student record validation, applying grading scale
conformance checks, field normalization, and calculation eligibility determination.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from apps.processing.parser.schema import (
    ParsedCourse,
    ParsedSheet,
    ParsedStudent,
    ParsedStudentResult,
)
from apps.processing.parser.template import ResultSheetTemplate, get_default_template
from .schema import (
    ValidatedField,
    ValidatedSheet,
    ValidatedStudent,
    ValidatedStudentResult,
    ValidationStatus,
)
from .validators import FieldValidators

logger = logging.getLogger(__name__)


class SheetValidationEngine:
    """
    Validates complete parsed result sheets and individual student records.
    """

    def __init__(self, template: Optional[ResultSheetTemplate] = None):
        self.template = template or get_default_template()

    def validate_sheet(
        self,
        sheet: ParsedSheet,
        template: Optional[ResultSheetTemplate] = None,
    ) -> ValidatedSheet:
        """
        Runs comprehensive validation across an entire ParsedSheet.
        """
        active_template = template or self.template
        warnings: List[str] = list(sheet.warnings)

        # 1. Validate Sheet-Level Metadata
        vf_inst = ValidatedField("institution", sheet.institution, sheet.institution, confidence=sheet.overall_confidence)
        vf_prog = ValidatedField("program", sheet.program, sheet.program, confidence=sheet.overall_confidence)
        vf_sem = ValidatedField("semester", sheet.semester, sheet.semester, confidence=sheet.overall_confidence)
        vf_sess = ValidatedField("exam_session", sheet.exam_session, sheet.exam_session, confidence=sheet.overall_confidence)

        # 2. Validate Courses
        validated_courses: List[ValidatedField[Any]] = []
        for course in sheet.courses:
            vf_code = FieldValidators.validate_course_code(course.course_code, confidence=course.confidence, template=active_template)
            vf_cr = FieldValidators.validate_credit_hours(course.credit_hours_raw or str(course.credit_hours or ""), confidence=course.confidence, template=active_template)

            course_status = ValidationStatus.VALID
            if vf_code.is_invalid or vf_cr.is_invalid:
                course_status = ValidationStatus.INVALID
            elif vf_code.needs_review or vf_cr.needs_review or course.requires_review:
                course_status = ValidationStatus.NEEDS_REVIEW
            elif vf_code.is_warning or vf_cr.is_warning:
                course_status = ValidationStatus.WARNING

            course_field = ValidatedField(
                field_name=course.course_code,
                raw_value=course.course_code_raw,
                normalized_value=course,
                confidence=course.confidence,
                status=course_status,
                warnings=vf_code.warnings + vf_cr.warnings + course.review_reasons,
                is_usable_in_calculations=course_status != ValidationStatus.INVALID,
            )
            validated_courses.append(course_field)

        # 3. Validate Student Records
        validated_students: List[ValidatedStudent] = []
        for student in sheet.students:
            v_student = self.validate_student(
                student=student,
                courses=sheet.courses,
                template=active_template,
            )
            validated_students.append(v_student)

        # 4. Sheet Level Status and Confidence
        all_student_confs = [s.overall_confidence for s in validated_students]
        overall_conf = (sum(all_student_confs) / len(all_student_confs)) if all_student_confs else sheet.overall_confidence

        sheet_status = ValidationStatus.VALID
        if any(s.status == ValidationStatus.INVALID for s in validated_students) or any(c.is_invalid for c in validated_courses):
            sheet_status = ValidationStatus.INVALID
        elif any(s.status == ValidationStatus.NEEDS_REVIEW for s in validated_students) or any(c.needs_review for c in validated_courses):
            sheet_status = ValidationStatus.NEEDS_REVIEW
        elif any(s.status == ValidationStatus.WARNING for s in validated_students) or any(c.is_warning for c in validated_courses):
            sheet_status = ValidationStatus.WARNING

        validated_sheet = ValidatedSheet(
            institution=vf_inst,
            program=vf_prog,
            semester=vf_sem,
            exam_session=vf_sess,
            courses=validated_courses,
            students=validated_students,
            overall_confidence=overall_conf,
            status=sheet_status,
            warnings=warnings,
            metadata={
                "template_name": active_template.name,
                "total_students": len(validated_students),
                "total_courses": len(validated_courses),
            },
        )

        logger.info(
            f"[validation_engine] Validated sheet: {validated_sheet.valid_students_count} valid, "
            f"{validated_sheet.warning_students_count} warning, "
            f"{validated_sheet.needs_review_students_count} review, "
            f"{validated_sheet.invalid_students_count} invalid students"
        )
        return validated_sheet

    def validate_student(
        self,
        student: ParsedStudent,
        courses: List[ParsedCourse],
        template: Optional[ResultSheetTemplate] = None,
    ) -> ValidatedStudent:
        """
        Validates an individual student record.
        """
        active_template = template or self.template
        validation_messages: List[str] = list(student.review_reasons)

        # 1. Validate Identity
        vf_id = FieldValidators.validate_student_id(student.student_id_raw or student.student_id, confidence=student.confidence, template=active_template)
        vf_name = FieldValidators.validate_student_name(student.student_name_raw or student.student_name, confidence=student.confidence, template=active_template)
        vf_serial = FieldValidators.validate_serial_no(student.serial_no_raw or str(student.serial_no or ""), row_idx=student.row_index, confidence=student.confidence)

        if vf_id.warnings:
            validation_messages.extend(vf_id.warnings)
        if vf_name.warnings:
            validation_messages.extend(vf_name.warnings)

        # 2. Validate Course Results
        validated_results: List[ValidatedStudentResult] = []
        for course in courses:
            raw_res = student.get_result(course.course_code)
            if raw_res:
                v_res = FieldValidators.validate_student_result(
                    course_code_raw=raw_res.course_code,
                    gp_raw=raw_res.grade_point_raw or str(raw_res.grade_point or ""),
                    lg_raw=raw_res.letter_grade_raw or raw_res.letter_grade,
                    confidence=raw_res.confidence,
                    template=active_template,
                    cell_coordinates=raw_res.cell_coordinates,
                )
            else:
                # Missing course result
                v_res = ValidatedStudentResult(
                    course_code=ValidatedField("course_code", course.course_code, course.course_code, confidence=1.0),
                    grade_point=ValidatedField("grade_point", "", None, confidence=1.0, status=ValidationStatus.NEEDS_REVIEW, warnings=["Missing course grade."]),
                    letter_grade=ValidatedField("letter_grade", "", "", confidence=1.0, status=ValidationStatus.NEEDS_REVIEW, warnings=["Missing letter grade."]),
                    is_consistent_gp_lg=False,
                    status=ValidationStatus.NEEDS_REVIEW,
                )
            validated_results.append(v_res)
            if v_res.grade_point.warnings:
                validation_messages.extend([f"[{course.course_code}] {w}" for w in v_res.grade_point.warnings])

        # 3. Validate Current Semester Summary
        v_current_summary = None
        if student.current_semester_summary:
            cs = student.current_semester_summary
            v_current_summary = FieldValidators.validate_current_semester_summary(
                gpa_raw=cs.gpa_raw or str(cs.gpa or ""),
                total_cr_raw=cs.total_credit_raw or str(cs.total_credit or ""),
                earned_cr_raw=cs.earned_credit_raw or str(cs.earned_credit or ""),
                points_raw=cs.grade_points_raw or str(cs.grade_points or ""),
                status_raw=cs.result_status_raw or cs.result_status,
                remarks_raw=cs.remarks_raw or cs.remarks,
                confidence=cs.confidence,
                template=active_template,
            )
            if v_current_summary.gpa.warnings:
                validation_messages.extend(v_current_summary.gpa.warnings)

        # 4. Validate Cumulative Summary
        v_cum_summary = None
        if student.cumulative_summary:
            cum = student.cumulative_summary
            v_cum_summary = FieldValidators.validate_cumulative_summary(
                cgpa_raw=cum.cgpa_raw or str(cum.cgpa or ""),
                total_cr_raw=cum.total_credit_raw or str(cum.total_credit or ""),
                earned_cr_raw=cum.earned_credit_raw or str(cum.earned_credit or ""),
                points_raw=cum.grade_points_raw or str(cum.grade_points or ""),
                status_raw=cum.result_status_raw or cum.result_status,
                remarks_raw=cum.remarks_raw or cum.remarks,
                confidence=cum.confidence,
                template=active_template,
            )
            if v_cum_summary.cgpa.warnings:
                validation_messages.extend(v_cum_summary.cgpa.warnings)

        # 5. Determine Overall Student Status & Usability
        has_critical = (
            vf_id.is_invalid or
            any(r.grade_point.is_invalid for r in validated_results) or
            (v_current_summary and v_current_summary.gpa.is_invalid) or
            (v_cum_summary and v_cum_summary.cgpa.is_invalid)
        )

        student_status = ValidationStatus.VALID
        if has_critical:
            student_status = ValidationStatus.INVALID
        elif (
            vf_id.needs_review or vf_name.needs_review or
            any(r.status == ValidationStatus.NEEDS_REVIEW for r in validated_results) or
            (v_current_summary and v_current_summary.status == ValidationStatus.NEEDS_REVIEW) or
            (v_cum_summary and v_cum_summary.status == ValidationStatus.NEEDS_REVIEW) or
            student.requires_review
        ):
            student_status = ValidationStatus.NEEDS_REVIEW
        elif (
            vf_id.is_warning or vf_name.is_warning or
            any(r.status == ValidationStatus.WARNING for r in validated_results) or
            (v_current_summary and v_current_summary.status == ValidationStatus.WARNING) or
            (v_cum_summary and v_cum_summary.status == ValidationStatus.WARNING)
        ):
            student_status = ValidationStatus.WARNING

        return ValidatedStudent(
            student_id=vf_id,
            student_name=vf_name,
            serial_no=vf_serial,
            row_index=student.row_index,
            results=validated_results,
            current_semester_summary=v_current_summary,
            cumulative_summary=v_cum_summary,
            status=student_status,
            overall_confidence=student.confidence,
            has_critical_errors=has_critical,
            validation_messages=list(dict.fromkeys(validation_messages)),
        )
