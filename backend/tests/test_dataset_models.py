"""
Comprehensive model tests for the dataset app.

Tests cover:
  - Model creation and string representation
  - Unique constraints (duplicates raise IntegrityError)
  - clean() validators (ValidationError on invalid data)
  - Index presence (verified through Meta.indexes)
  - Decimal / boundary validation for GP, GPA, CGPA, credits
  - OneToOne constraints (student → summaries)
  - CASCADE deletes
  - ResultSheet ↔ Course ↔ Student ↔ StudentResult relational integrity
  - Raw vs normalised field independence
  - Processing-duration property
"""

import uuid
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.dataset.models import (
    Course,
    CumulativeSummary,
    CurrentSemesterSummary,
    ResultSheet,
    Student,
    StudentResult,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_sheet(**kwargs):
    """Create a minimal ResultSheet."""
    defaults = dict(
        original_filename='test_sheet.pdf',
        file_type='pdf',
        file_size_bytes=1024,
        status=ResultSheet.ProcessingStatus.PENDING,
    )
    defaults.update(kwargs)
    return ResultSheet.objects.create(**defaults)


def make_course(sheet, code='CSE-2201', credit=Decimal('3.00'), index=0):
    return Course.objects.create(
        dataset=sheet,
        course_code=code,
        course_name='Algorithms',
        credit_hours_raw='3.00',
        credit_hours=credit,
        column_index=index,
    )


def make_student(sheet, sid='2102045', name='Test Student', row=0):
    return Student.objects.create(
        dataset=sheet,
        student_id_raw=sid,
        student_id=sid,
        student_name_raw=name,
        student_name=name,
        row_index=row,
    )


def make_result(sheet, student, course, gp=Decimal('3.75'), lg='A'):
    return StudentResult.objects.create(
        dataset=sheet,
        student=student,
        course=course,
        grade_point_raw='3.75',
        letter_grade_raw='A',
        grade_point=gp,
        letter_grade=lg,
        cell_confidence=Decimal('0.9900'),
    )


# ===========================================================================
# ResultSheet
# ===========================================================================

class ResultSheetModelTests(TestCase):

    def test_create_minimal(self):
        sheet = make_sheet()
        self.assertIsNotNone(sheet.id)
        self.assertEqual(sheet.status, ResultSheet.ProcessingStatus.PENDING)
        self.assertEqual(sheet.detected_student_count, 0)
        self.assertEqual(sheet.detected_course_count, 0)
        self.assertEqual(sheet.warnings, [])
        self.assertEqual(sheet.processing_meta, {})

    def test_uuid_primary_key(self):
        sheet = make_sheet()
        self.assertIsInstance(sheet.id, uuid.UUID)

    def test_str_representation(self):
        sheet = make_sheet(original_filename='results.pdf')
        self.assertIn('results.pdf', str(sheet))
        self.assertIn('PENDING', str(sheet))

    def test_processing_duration_none_when_incomplete(self):
        sheet = make_sheet()
        self.assertIsNone(sheet.processing_duration_seconds)

    def test_processing_duration_computed(self):
        from django.utils import timezone
        from datetime import timedelta
        sheet = make_sheet()
        sheet.processing_started_at = timezone.now() - timedelta(seconds=10)
        sheet.processing_finished_at = timezone.now()
        sheet.save()
        duration = sheet.processing_duration_seconds
        self.assertIsNotNone(duration)
        self.assertGreater(duration, 0)

    def test_status_choices(self):
        for status, _ in ResultSheet.ProcessingStatus.choices:
            sheet = make_sheet(status=status)
            self.assertEqual(sheet.status, status)

    def test_warnings_stored_as_list(self):
        sheet = make_sheet()
        sheet.warnings = ['GPA mismatch for 2102045', 'Low confidence row 12']
        sheet.save()
        sheet.refresh_from_db()
        self.assertEqual(len(sheet.warnings), 2)

    def test_processing_meta_stored_as_dict(self):
        sheet = make_sheet()
        sheet.processing_meta = {'page_count': 2, 'dpi': 300, 'skew_angle': -1.2}
        sheet.save()
        sheet.refresh_from_db()
        self.assertEqual(sheet.processing_meta['page_count'], 2)

    def test_parsing_confidence_bounds(self):
        sheet = make_sheet()
        sheet.parsing_confidence = Decimal('0.9876')
        sheet.full_clean()   # must not raise
        sheet.parsing_confidence = Decimal('1.0000')
        sheet.full_clean()
        sheet.parsing_confidence = Decimal('0.0000')
        sheet.full_clean()

    def test_parsing_confidence_above_one_fails(self):
        sheet = make_sheet()
        sheet.parsing_confidence = Decimal('1.0001')
        with self.assertRaises(ValidationError):
            sheet.full_clean()


# ===========================================================================
# Course
# ===========================================================================

class CourseModelTests(TestCase):

    def setUp(self):
        self.sheet = make_sheet()

    def test_create_course(self):
        course = make_course(self.sheet)
        self.assertEqual(course.dataset, self.sheet)
        self.assertEqual(course.course_code, 'CSE-2201')
        self.assertEqual(course.credit_hours, Decimal('3.00'))

    def test_str_representation(self):
        course = make_course(self.sheet)
        self.assertIn('CSE-2201', str(course))
        self.assertIn('3.00', str(course))

    def test_duplicate_course_code_same_sheet_raises(self):
        make_course(self.sheet, code='CSE-2201')
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                make_course(self.sheet, code='CSE-2201')

    def test_same_course_code_different_sheets_allowed(self):
        sheet2 = make_sheet(original_filename='sheet2.pdf')
        make_course(self.sheet, code='CSE-2201')
        c2 = make_course(sheet2, code='CSE-2201')   # must not raise
        self.assertEqual(c2.dataset, sheet2)

    def test_variable_course_count(self):
        """Sheet structure must support any number of courses."""
        for i, code in enumerate(['CSE-101', 'CSE-102', 'CSE-103', 'MAT-101', 'PHY-101']):
            make_course(self.sheet, code=code, index=i)
        self.assertEqual(self.sheet.courses.count(), 5)

    def test_course_ordering_by_column_index(self):
        make_course(self.sheet, code='CSE-102', index=1)
        make_course(self.sheet, code='CSE-101', index=0)
        make_course(self.sheet, code='CSE-103', index=2)
        codes = list(self.sheet.courses.values_list('course_code', flat=True))
        self.assertEqual(codes, ['CSE-101', 'CSE-102', 'CSE-103'])

    def test_negative_credit_validation(self):
        course = make_course(self.sheet)
        course.credit_hours = Decimal('-1.00')
        with self.assertRaises(ValidationError):
            course.full_clean()

    def test_cascade_delete_with_sheet(self):
        make_course(self.sheet)
        self.sheet.delete()
        self.assertEqual(Course.objects.count(), 0)


# ===========================================================================
# Student
# ===========================================================================

class StudentModelTests(TestCase):

    def setUp(self):
        self.sheet = make_sheet()

    def test_create_student(self):
        student = make_student(self.sheet)
        self.assertEqual(student.student_id, '2102045')
        self.assertFalse(student.has_warnings)
        self.assertEqual(student.extraction_confidence, Decimal('1.0000'))

    def test_str_representation(self):
        student = make_student(self.sheet, sid='2102045', name='John Doe')
        self.assertIn('2102045', str(student))
        self.assertIn('John Doe', str(student))

    def test_duplicate_student_id_same_sheet_raises(self):
        make_student(self.sheet, sid='2102045')
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                make_student(self.sheet, sid='2102045')

    def test_same_student_id_different_sheets_allowed(self):
        sheet2 = make_sheet(original_filename='sheet2.pdf')
        make_student(self.sheet, sid='2102045')
        s2 = make_student(sheet2, sid='2102045')
        self.assertEqual(s2.dataset, sheet2)

    def test_blank_student_id_fails_validation(self):
        student = Student(
            dataset=self.sheet,
            student_id_raw='  ',
            student_id='',
            row_index=0,
        )
        with self.assertRaises(ValidationError):
            student.full_clean()

    def test_confidence_out_of_bounds_fails(self):
        student = make_student(self.sheet)
        student.extraction_confidence = Decimal('1.5000')
        with self.assertRaises(ValidationError):
            student.full_clean()

    def test_ordering_by_row_index(self):
        make_student(self.sheet, sid='S003', row=2)
        make_student(self.sheet, sid='S001', row=0)
        make_student(self.sheet, sid='S002', row=1)
        ids = list(self.sheet.students.values_list('student_id', flat=True))
        self.assertEqual(ids, ['S001', 'S002', 'S003'])

    def test_cascade_delete_with_sheet(self):
        make_student(self.sheet)
        self.sheet.delete()
        self.assertEqual(Student.objects.count(), 0)


# ===========================================================================
# StudentResult
# ===========================================================================

class StudentResultModelTests(TestCase):

    def setUp(self):
        self.sheet   = make_sheet()
        self.course  = make_course(self.sheet)
        self.student = make_student(self.sheet)

    def test_create_result(self):
        result = make_result(self.sheet, self.student, self.course)
        self.assertEqual(result.grade_point, Decimal('3.75'))
        self.assertEqual(result.letter_grade, 'A')

    def test_str_representation(self):
        result = make_result(self.sheet, self.student, self.course)
        self.assertIn(self.student.student_id, str(result))
        self.assertIn(self.course.course_code, str(result))

    def test_duplicate_student_course_same_sheet_raises(self):
        make_result(self.sheet, self.student, self.course)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                make_result(self.sheet, self.student, self.course)

    def test_raw_and_normalised_stored_independently(self):
        result = StudentResult.objects.create(
            dataset=self.sheet,
            student=self.student,
            course=self.course,
            grade_point_raw='3 75',    # deliberately malformed raw
            letter_grade_raw='A ',     # trailing space in raw
            grade_point=Decimal('3.75'),
            letter_grade='A',
        )
        self.assertEqual(result.grade_point_raw, '3 75')
        self.assertEqual(result.grade_point, Decimal('3.75'))

    def test_grade_point_max_boundary(self):
        result = make_result(self.sheet, self.student, self.course, gp=Decimal('4.00'))
        result.full_clean()   # must not raise

    def test_grade_point_min_boundary(self):
        result = make_result(self.sheet, self.student, self.course, gp=Decimal('0.00'))
        result.full_clean()

    def test_grade_point_above_max_fails(self):
        result = make_result(self.sheet, self.student, self.course)
        result.grade_point = Decimal('4.01')
        with self.assertRaises(ValidationError):
            result.full_clean()

    def test_grade_point_below_min_fails(self):
        result = make_result(self.sheet, self.student, self.course)
        result.grade_point = Decimal('-0.01')
        with self.assertRaises(ValidationError):
            result.full_clean()

    def test_null_grade_point_allowed(self):
        """OCR may fail to extract a GP; null is valid."""
        result = StudentResult.objects.create(
            dataset=self.sheet,
            student=self.student,
            course=self.course,
            grade_point=None,
            letter_grade='',
        )
        self.assertIsNone(result.grade_point)

    def test_all_letter_grade_choices(self):
        from apps.dataset.models import LETTER_GRADES
        course = make_course(self.sheet, code='X-001', index=99)
        for i, (lg_code, _) in enumerate(LETTER_GRADES):
            sid = f'S{i:04d}'
            student = make_student(self.sheet, sid=sid, row=100 + i)
            make_result(self.sheet, student, course, gp=Decimal('3.00'), lg=lg_code)
        self.assertEqual(
            StudentResult.objects.filter(dataset=self.sheet, course=course).count(),
            len(LETTER_GRADES),
        )

    def test_variable_courses_per_student(self):
        """Any number of courses per student — no fixed schema."""
        courses = [make_course(self.sheet, code=f'X-{i:03d}', index=i + 1) for i in range(7)]
        for c in courses:
            make_result(self.sheet, self.student, c)
        self.assertEqual(self.student.results.count(), 7)

    def test_cascade_delete_student_removes_results(self):
        make_result(self.sheet, self.student, self.course)
        self.student.delete()
        self.assertEqual(StudentResult.objects.count(), 0)

    def test_cascade_delete_course_removes_results(self):
        make_result(self.sheet, self.student, self.course)
        self.course.delete()
        self.assertEqual(StudentResult.objects.count(), 0)


# ===========================================================================
# CurrentSemesterSummary
# ===========================================================================

class CurrentSemesterSummaryTests(TestCase):

    def setUp(self):
        self.sheet   = make_sheet()
        self.student = make_student(self.sheet)

    def _make_summary(self, **kwargs):
        defaults = dict(
            dataset=self.sheet,
            student=self.student,
            credits_attempted_raw='19.50',
            credits_attempted=Decimal('19.50'),
            credits_earned_raw='19.50',
            credits_earned=Decimal('19.50'),
            gpa_raw='3.85',
            gpa=Decimal('3.85'),
            calculated_gpa=Decimal('3.85'),
            is_gpa_arithmetic_valid=True,
        )
        defaults.update(kwargs)
        return CurrentSemesterSummary.objects.create(**defaults)

    def test_create(self):
        s = self._make_summary()
        self.assertEqual(s.gpa, Decimal('3.85'))
        self.assertTrue(s.is_gpa_arithmetic_valid)

    def test_oneto_one_student_constraint(self):
        self._make_summary()
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                CurrentSemesterSummary.objects.create(
                    dataset=self.sheet,
                    student=self.student,
                    gpa=Decimal('3.00'),
                )

    def test_credits_earned_exceeds_attempted_fails(self):
        s = self._make_summary(
            credits_attempted=Decimal('15.00'),
            credits_earned=Decimal('18.00'),
        )
        with self.assertRaises(ValidationError):
            s.full_clean()

    def test_str_representation(self):
        s = self._make_summary()
        self.assertIn(self.student.student_id, str(s))
        self.assertIn('3.85', str(s))

    def test_cascade_delete_with_student(self):
        self._make_summary()
        self.student.delete()
        self.assertEqual(CurrentSemesterSummary.objects.count(), 0)

    def test_semester_rank_and_percentile(self):
        s = self._make_summary()
        s.semester_rank = 3
        s.semester_percentile = Decimal('96.875')
        s.save()
        s.refresh_from_db()
        self.assertEqual(s.semester_rank, 3)


# ===========================================================================
# CumulativeSummary
# ===========================================================================

class CumulativeSummaryTests(TestCase):

    def setUp(self):
        self.sheet   = make_sheet()
        self.student = make_student(self.sheet)

    def _make_summary(self, **kwargs):
        defaults = dict(
            dataset=self.sheet,
            student=self.student,
            total_credits_attempted_raw='78.00',
            total_credits_attempted=Decimal('78.00'),
            total_credits_earned_raw='78.00',
            total_credits_earned=Decimal('78.00'),
            total_grade_points_raw='294.750',
            total_grade_points=Decimal('294.750'),
            cgpa_raw='3.78',
            cgpa=Decimal('3.78'),
            calculated_cgpa=Decimal('3.78'),
            is_cgpa_arithmetic_valid=True,
        )
        defaults.update(kwargs)
        return CumulativeSummary.objects.create(**defaults)

    def test_create(self):
        s = self._make_summary()
        self.assertEqual(s.cgpa, Decimal('3.78'))
        self.assertTrue(s.is_cgpa_arithmetic_valid)

    def test_oneto_one_student_constraint(self):
        self._make_summary()
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                CumulativeSummary.objects.create(
                    dataset=self.sheet,
                    student=self.student,
                    cgpa=Decimal('3.00'),
                )

    def test_cgpa_above_max_fails(self):
        s = self._make_summary(cgpa=Decimal('4.01'))
        with self.assertRaises(ValidationError):
            s.full_clean()

    def test_cgpa_below_min_fails(self):
        s = self._make_summary(cgpa=Decimal('-0.01'))
        with self.assertRaises(ValidationError):
            s.full_clean()

    def test_credits_earned_exceeds_attempted_fails(self):
        s = self._make_summary(
            total_credits_attempted=Decimal('60.00'),
            total_credits_earned=Decimal('65.00'),
        )
        with self.assertRaises(ValidationError):
            s.full_clean()

    def test_str_representation(self):
        s = self._make_summary()
        self.assertIn(self.student.student_id, str(s))
        self.assertIn('3.78', str(s))

    def test_cascade_delete_with_student(self):
        self._make_summary()
        self.student.delete()
        self.assertEqual(CumulativeSummary.objects.count(), 0)

    def test_cumulative_rank_and_percentile(self):
        s = self._make_summary()
        s.cumulative_rank = 4
        s.cumulative_percentile = Decimal('95.312')
        s.save()
        s.refresh_from_db()
        self.assertEqual(s.cumulative_rank, 4)


# ===========================================================================
# Cross-model integration
# ===========================================================================

class FullDatasetIntegrationTests(TestCase):
    """
    End-to-end: build a complete mini-dataset and verify relational integrity,
    counts, and cascade delete propagation.
    """

    def setUp(self):
        self.sheet    = make_sheet(original_filename='integration.pdf')
        self.courses  = [
            make_course(self.sheet, code='CSE-2201', credit=Decimal('3.00'), index=0),
            make_course(self.sheet, code='CSE-2202', credit=Decimal('1.50'), index=1),
            make_course(self.sheet, code='MAT-2101', credit=Decimal('3.00'), index=2),
        ]
        # Create 3 students
        self.students = [
            make_student(self.sheet, sid=f'21020{i:02d}', row=i)
            for i in range(3)
        ]
        # Every student gets a result for every course
        self.gps = [
            [Decimal('4.00'), Decimal('3.75'), Decimal('3.50')],
            [Decimal('3.50'), Decimal('3.75'), Decimal('4.00')],
            [Decimal('3.25'), Decimal('3.00'), Decimal('3.50')],
        ]
        for si, student in enumerate(self.students):
            for ci, course in enumerate(self.courses):
                make_result(self.sheet, student, course, gp=self.gps[si][ci], lg='A')
            CurrentSemesterSummary.objects.create(
                dataset=self.sheet,
                student=student,
                gpa=sum(self.gps[si]) / 3,
                credits_attempted=Decimal('7.50'),
                credits_earned=Decimal('7.50'),
            )
            CumulativeSummary.objects.create(
                dataset=self.sheet,
                student=student,
                cgpa=sum(self.gps[si]) / 3,
                total_credits_earned=Decimal('60.00'),
            )

    def test_result_count(self):
        self.assertEqual(
            StudentResult.objects.filter(dataset=self.sheet).count(),
            9   # 3 students × 3 courses
        )

    def test_current_summary_count(self):
        self.assertEqual(CurrentSemesterSummary.objects.filter(dataset=self.sheet).count(), 3)

    def test_cumulative_summary_count(self):
        self.assertEqual(CumulativeSummary.objects.filter(dataset=self.sheet).count(), 3)

    def test_related_name_access(self):
        student = self.students[0]
        self.assertEqual(student.results.count(), 3)
        self.assertIsNotNone(student.current_semester_summary)
        self.assertIsNotNone(student.cumulative_summary)

    def test_cascade_delete_sheet_removes_everything(self):
        self.sheet.delete()
        self.assertEqual(Course.objects.count(), 0)
        self.assertEqual(Student.objects.count(), 0)
        self.assertEqual(StudentResult.objects.count(), 0)
        self.assertEqual(CurrentSemesterSummary.objects.count(), 0)
        self.assertEqual(CumulativeSummary.objects.count(), 0)

    def test_datasets_are_independent(self):
        """Results from one sheet must not be visible from another."""
        sheet2   = make_sheet(original_filename='independent.pdf')
        course2  = make_course(sheet2, code='CSE-2201', index=0)
        student2 = make_student(sheet2, sid='2102000', row=0)
        make_result(sheet2, student2, course2, gp=Decimal('4.00'))

        # Sheet 1 result count must remain 9
        self.assertEqual(StudentResult.objects.filter(dataset=self.sheet).count(), 9)
        # Sheet 2 result count is 1
        self.assertEqual(StudentResult.objects.filter(dataset=sheet2).count(), 1)
