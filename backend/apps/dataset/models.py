"""
Dataset models for Result Analyzer.

Design principles:
  - Every ResultSheet is an independent dataset — NO cross-sheet relationships.
  - Raw values (exactly as extracted from OCR / PDF text layer) are preserved
    alongside normalised values so discrepancies can always be audited.
  - Course count is NOT fixed: StudentResult rows are created per (student, course)
    pair, so any number of courses can appear on any sheet.
  - All monetary-style decimal arithmetic (GPA, CGPA, credit hours, grade points)
    uses DecimalField to avoid floating-point rounding surprises.
  - Indexes are placed on every FK and on the most common query predicates.
  - Unique constraints prevent duplicate extraction artefacts.
"""

import uuid
from decimal import Decimal, InvalidOperation

from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.db import models


# ---------------------------------------------------------------------------
# Shared constants
# ---------------------------------------------------------------------------

LETTER_GRADES = [
    ('A+', 'A+'), ('A', 'A'), ('A-', 'A-'),
    ('B+', 'B+'), ('B', 'B'), ('B-', 'B-'),
    ('C+', 'C+'), ('C', 'C'), ('C-', 'C-'),
    ('D+', 'D+'), ('D', 'D'), ('D-', 'D-'),
    ('F', 'F'),
    ('I', 'Incomplete'), ('W', 'Withdrawn'), ('UW', 'Unofficial Withdrawal'),
    ('NA', 'Not Available'),
]

GPA_VALIDATORS = [MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('4.00'))]
CREDIT_VALIDATORS = [MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('30.00'))]


# ---------------------------------------------------------------------------
# 1. ResultSheet  (one row per uploaded document)
# ---------------------------------------------------------------------------

class ResultSheet(models.Model):
    """
    Represents one uploaded and parsed academic result sheet.
    Every other model in this app is scoped to a single ResultSheet via FK.

    Linked to ResultSession (apps.sessions_manager) for ephemeral lifecycle
    management; the FK is nullable so the dataset survives a soft session
    expiry sweep that only deletes the session row, not the parsed data.
    """

    class ProcessingStatus(models.TextChoices):
        PENDING    = 'PENDING',    'Pending'
        PROCESSING = 'PROCESSING', 'Processing'
        COMPLETED  = 'COMPLETED',  'Completed'
        FAILED     = 'FAILED',     'Failed'
        PARTIAL    = 'PARTIAL',    'Partially Extracted'

    # ---- Identity ----------------------------------------------------------
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Soft-link to ephemeral session (nullable intentionally — session may be
    # purged independently of the dataset record).
    session = models.OneToOneField(
        'sessions_manager.ResultSession',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='result_sheet',
    )

    # ---- File metadata -----------------------------------------------------
    original_filename  = models.CharField(max_length=255, db_index=True)
    file_type          = models.CharField(max_length=10)   # 'pdf' | 'png' | 'jpeg'
    file_size_bytes    = models.BigIntegerField(default=0)
    uploaded_at        = models.DateTimeField(auto_now_add=True, db_index=True)

    # ---- Processing state --------------------------------------------------
    status = models.CharField(
        max_length=20,
        choices=ProcessingStatus.choices,
        default=ProcessingStatus.PENDING,
        db_index=True,
    )
    processing_started_at  = models.DateTimeField(null=True, blank=True)
    processing_finished_at = models.DateTimeField(null=True, blank=True)
    error_message          = models.TextField(blank=True, default='')

    # ---- Sheet-level metadata (detected during parsing) -------------------
    detected_institution   = models.CharField(max_length=512, blank=True, default='')
    detected_program       = models.CharField(max_length=255, blank=True, default='')
    detected_semester      = models.CharField(max_length=255, blank=True, default='')
    detected_exam_session  = models.CharField(max_length=255, blank=True, default='')

    # ---- Extraction summary ------------------------------------------------
    detected_student_count = models.PositiveIntegerField(default=0)
    detected_course_count  = models.PositiveIntegerField(default=0)
    parsing_confidence     = models.DecimalField(
        max_digits=5, decimal_places=4,
        default=Decimal('0.0000'),
        validators=[MinValueValidator(Decimal('0.0')), MaxValueValidator(Decimal('1.0'))],
        help_text='0.0–1.0 overall OCR/parsing quality score.',
    )

    # ---- Warnings list (non-fatal issues found during parsing) ------------
    # Stored as JSON list of strings, e.g. ["GPA mismatch for student 2102045"]
    warnings = models.JSONField(default=list, blank=True)

    # ---- Arbitrary processing metadata ------------------------------------
    # Stores things like page_count, dpi_used, pipeline_version, skew_angle, etc.
    processing_meta = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'Result Sheet'
        verbose_name_plural = 'Result Sheets'
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['uploaded_at']),
        ]

    def __str__(self):
        return f'ResultSheet({self.id}) — {self.original_filename} [{self.status}]'

    @property
    def processing_duration_seconds(self):
        if self.processing_started_at and self.processing_finished_at:
            return (self.processing_finished_at - self.processing_started_at).total_seconds()
        return None


# ---------------------------------------------------------------------------
# 2. Course  (one row per distinct course column detected in the sheet)
# ---------------------------------------------------------------------------

class Course(models.Model):
    """
    A course (subject) column detected in the result sheet.

    credit_hours_raw  — exactly what the sheet printed, e.g. '1.50' or '3'
    credit_hours      — normalised Decimal value used in GPA calculations
    column_index      — positional order of the column in the original sheet,
                        used to preserve original left-to-right ordering.
    """

    dataset = models.ForeignKey(
        ResultSheet,
        on_delete=models.CASCADE,
        related_name='courses',
        db_index=True,
    )

    course_code       = models.CharField(max_length=50)
    course_name       = models.CharField(max_length=512, blank=True, default='')

    # Raw string extracted from the sheet header
    credit_hours_raw  = models.CharField(max_length=20, blank=True, default='')
    # Normalised value
    credit_hours      = models.DecimalField(
        max_digits=5, decimal_places=2,
        validators=CREDIT_VALIDATORS,
    )

    # Position of this course in the sheet (0-based) for stable ordering
    column_index      = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['dataset', 'column_index']
        verbose_name = 'Course'
        verbose_name_plural = 'Courses'
        # A course code must be unique within a single result sheet
        unique_together = [('dataset', 'course_code')]
        indexes = [
            models.Index(fields=['dataset', 'column_index']),
            models.Index(fields=['course_code']),
        ]

    def clean(self):
        if self.credit_hours is not None and self.credit_hours < 0:
            raise ValidationError({'credit_hours': 'Credit hours cannot be negative.'})

    def __str__(self):
        return f'{self.course_code} ({self.credit_hours} cr) — sheet {self.dataset_id}'


# ---------------------------------------------------------------------------
# 3. Student  (one row per student detected in the sheet)
# ---------------------------------------------------------------------------

class Student(models.Model):
    """
    A student row detected in the result sheet.

    student_id_raw — exactly as OCR read it (may contain stray spaces / dashes)
    student_id     — normalised (trimmed, uppercased) version used for lookups
    student_name_raw / student_name — same raw/normalised split for the name
    row_index      — original position in the sheet for stable ordering
    """

    dataset = models.ForeignKey(
        ResultSheet,
        on_delete=models.CASCADE,
        related_name='students',
        db_index=True,
    )

    student_id_raw    = models.CharField(max_length=100)
    student_id        = models.CharField(max_length=100, db_index=True)

    student_name_raw  = models.CharField(max_length=512, blank=True, default='')
    student_name      = models.CharField(max_length=512, blank=True, default='')

    # Original row position in the tabulation sheet (0-based)
    row_index         = models.PositiveIntegerField(default=0)

    # Per-student OCR quality
    extraction_confidence = models.DecimalField(
        max_digits=5, decimal_places=4, default=Decimal('1.0000'),
        validators=[MinValueValidator(Decimal('0.0')), MaxValueValidator(Decimal('1.0'))],
    )
    has_warnings = models.BooleanField(default=False, db_index=True)

    class Meta:
        ordering = ['dataset', 'row_index']
        verbose_name = 'Student'
        verbose_name_plural = 'Students'
        # Same student ID must appear at most once per result sheet
        unique_together = [('dataset', 'student_id')]
        indexes = [
            models.Index(fields=['dataset', 'student_id']),
            models.Index(fields=['student_id']),
            models.Index(fields=['dataset', 'row_index']),
        ]

    def clean(self):
        if not self.student_id:
            raise ValidationError({'student_id': 'Normalised student ID must not be blank.'})

    def __str__(self):
        return f'{self.student_id} — {self.student_name or "?"} (sheet {self.dataset_id})'


# ---------------------------------------------------------------------------
# 4. StudentResult  (one row per student × course intersection)
# ---------------------------------------------------------------------------

class StudentResult(models.Model):
    """
    A single grade cell: the result of one student in one course.

    Raw values are preserved verbatim from OCR / text extraction.
    Normalised values are validated, cleaned, and ready for calculations.

    is_valid_gp_lg_match — set during validation: does the letter grade match
                           the grade point on the institutional grading scale?
    cell_confidence      — per-cell OCR confidence (0.0–1.0)
    """

    dataset = models.ForeignKey(
        ResultSheet,
        on_delete=models.CASCADE,
        related_name='student_results',
        db_index=True,
    )
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='results',
        db_index=True,
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='results',
        db_index=True,
    )

    # ---- Raw (verbatim OCR output) ----------------------------------------
    grade_point_raw   = models.CharField(max_length=20, blank=True, default='')
    letter_grade_raw  = models.CharField(max_length=10, blank=True, default='')

    # ---- Normalised --------------------------------------------------------
    grade_point = models.DecimalField(
        max_digits=4, decimal_places=2,
        null=True, blank=True,
        validators=GPA_VALIDATORS,
        help_text='Normalised GP on 0.00–4.00 scale.',
    )
    letter_grade = models.CharField(
        max_length=5, choices=LETTER_GRADES,
        blank=True, default='',
    )

    # ---- Validation flags --------------------------------------------------
    is_valid_gp_lg_match = models.BooleanField(
        null=True, blank=True,
        help_text='True if grade_point and letter_grade are consistent with institutional scale.',
    )
    cell_confidence = models.DecimalField(
        max_digits=5, decimal_places=4, default=Decimal('1.0000'),
        validators=[MinValueValidator(Decimal('0.0')), MaxValueValidator(Decimal('1.0'))],
    )

    class Meta:
        ordering = ['student', 'course__column_index']
        verbose_name = 'Student Result'
        verbose_name_plural = 'Student Results'
        # A student can have at most one result per course per dataset
        unique_together = [('dataset', 'student', 'course')]
        indexes = [
            models.Index(fields=['dataset', 'student']),
            models.Index(fields=['dataset', 'course']),
            models.Index(fields=['letter_grade']),
            models.Index(fields=['grade_point']),
        ]

    def clean(self):
        if self.grade_point is not None:
            if not (Decimal('0.00') <= self.grade_point <= Decimal('4.00')):
                raise ValidationError(
                    {'grade_point': f'Grade point {self.grade_point} is outside 0.00–4.00.'}
                )

    def __str__(self):
        return (
            f'{self.student.student_id} / {self.course.course_code} '
            f'→ {self.letter_grade or "?"} ({self.grade_point or "?"})'
        )


# ---------------------------------------------------------------------------
# 5. CurrentSemesterSummary  (one row per student in the sheet)
# ---------------------------------------------------------------------------

class CurrentSemesterSummary(models.Model):
    """
    The current-semester summary columns printed in the result sheet for each student.

    These values come directly from the sheet (not calculated by us), so they
    represent the institution's own arithmetic.  Our re-calculated GPA is stored
    separately in calculated_gpa so discrepancies can be detected and flagged.

    All *_raw fields hold the verbatim extracted string; the partner field holds
    the normalised Decimal / float value.
    """

    dataset = models.ForeignKey(
        ResultSheet,
        on_delete=models.CASCADE,
        related_name='current_summaries',
        db_index=True,
    )
    student = models.OneToOneField(
        Student,
        on_delete=models.CASCADE,
        related_name='current_semester_summary',
    )

    # ---- Credits -----------------------------------------------------------
    credits_attempted_raw = models.CharField(max_length=20, blank=True, default='')
    credits_attempted     = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True,
        validators=CREDIT_VALIDATORS,
    )

    credits_earned_raw    = models.CharField(max_length=20, blank=True, default='')
    credits_earned        = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True,
        validators=CREDIT_VALIDATORS,
    )

    # ---- Grade Points Total ------------------------------------------------
    # Sum of (credit × GP) for the semester as printed in the sheet
    total_grade_points_raw = models.CharField(max_length=20, blank=True, default='')
    total_grade_points     = models.DecimalField(
        max_digits=8, decimal_places=3, null=True, blank=True,
        validators=[MinValueValidator(Decimal('0.000'))],
    )

    # ---- GPA ---------------------------------------------------------------
    gpa_raw = models.CharField(max_length=20, blank=True, default='')
    gpa     = models.DecimalField(
        max_digits=4, decimal_places=2, null=True, blank=True,
        validators=GPA_VALIDATORS,
        help_text='GPA as printed in the result sheet.',
    )

    # ---- Our re-calculated GPA (for validation) ----------------------------
    calculated_gpa = models.DecimalField(
        max_digits=4, decimal_places=2, null=True, blank=True,
        validators=GPA_VALIDATORS,
        help_text='GPA re-calculated by us from StudentResult rows.',
    )
    is_gpa_arithmetic_valid = models.BooleanField(
        null=True, blank=True,
        help_text='True when |gpa − calculated_gpa| ≤ 0.02.',
    )

    # ---- Semester-level rank (computed by ranking engine) ------------------
    semester_rank       = models.PositiveIntegerField(null=True, blank=True, db_index=True)
    semester_percentile = models.DecimalField(
        max_digits=6, decimal_places=3, null=True, blank=True,
        validators=[MinValueValidator(Decimal('0.0')), MaxValueValidator(Decimal('100.0'))],
    )

    class Meta:
        ordering = ['dataset', 'semester_rank']
        verbose_name = 'Current Semester Summary'
        verbose_name_plural = 'Current Semester Summaries'
        indexes = [
            models.Index(fields=['dataset', 'semester_rank']),
            models.Index(fields=['dataset', 'gpa']),
        ]

    def clean(self):
        if (
            self.credits_earned is not None
            and self.credits_attempted is not None
            and self.credits_earned > self.credits_attempted
        ):
            raise ValidationError(
                'Credits earned cannot exceed credits attempted for current semester.'
            )

    def __str__(self):
        return f'Current summary: {self.student.student_id} GPA={self.gpa} rank={self.semester_rank}'


# ---------------------------------------------------------------------------
# 6. CumulativeSummary  (one row per student in the sheet)
# ---------------------------------------------------------------------------

class CumulativeSummary(models.Model):
    """
    The cumulative result columns printed in the result sheet for each student.

    These are the institution's own cumulative figures as printed on the sheet —
    they already account for all prior semesters.  This application never
    accumulates them itself; it only reads and validates what is present.
    """

    dataset = models.ForeignKey(
        ResultSheet,
        on_delete=models.CASCADE,
        related_name='cumulative_summaries',
        db_index=True,
    )
    student = models.OneToOneField(
        Student,
        on_delete=models.CASCADE,
        related_name='cumulative_summary',
    )

    # ---- Credits -----------------------------------------------------------
    total_credits_attempted_raw = models.CharField(max_length=20, blank=True, default='')
    total_credits_attempted     = models.DecimalField(
        max_digits=7, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
    )

    total_credits_earned_raw    = models.CharField(max_length=20, blank=True, default='')
    total_credits_earned        = models.DecimalField(
        max_digits=7, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
    )

    # ---- Cumulative Grade Points -------------------------------------------
    total_grade_points_raw = models.CharField(max_length=20, blank=True, default='')
    total_grade_points     = models.DecimalField(
        max_digits=10, decimal_places=3, null=True, blank=True,
        validators=[MinValueValidator(Decimal('0.000'))],
    )

    # ---- CGPA --------------------------------------------------------------
    cgpa_raw = models.CharField(max_length=20, blank=True, default='')
    cgpa     = models.DecimalField(
        max_digits=4, decimal_places=2, null=True, blank=True,
        validators=GPA_VALIDATORS,
        help_text='Cumulative GPA as printed in the result sheet.',
    )

    # ---- Our re-calculated CGPA (for validation) ---------------------------
    calculated_cgpa = models.DecimalField(
        max_digits=4, decimal_places=2, null=True, blank=True,
        validators=GPA_VALIDATORS,
        help_text='CGPA re-derived from total_grade_points / total_credits_attempted.',
    )
    is_cgpa_arithmetic_valid = models.BooleanField(
        null=True, blank=True,
        help_text='True when |cgpa − calculated_cgpa| ≤ 0.02.',
    )

    # ---- Cumulative rank (computed by ranking engine) ----------------------
    cumulative_rank       = models.PositiveIntegerField(null=True, blank=True, db_index=True)
    cumulative_percentile = models.DecimalField(
        max_digits=6, decimal_places=3, null=True, blank=True,
        validators=[MinValueValidator(Decimal('0.0')), MaxValueValidator(Decimal('100.0'))],
    )

    class Meta:
        ordering = ['dataset', 'cumulative_rank']
        verbose_name = 'Cumulative Summary'
        verbose_name_plural = 'Cumulative Summaries'
        indexes = [
            models.Index(fields=['dataset', 'cumulative_rank']),
            models.Index(fields=['dataset', 'cgpa']),
        ]

    def clean(self):
        if (
            self.total_credits_earned is not None
            and self.total_credits_attempted is not None
            and self.total_credits_earned > self.total_credits_attempted
        ):
            raise ValidationError(
                'Total credits earned cannot exceed total credits attempted (cumulative).'
            )
        if self.cgpa is not None and not (Decimal('0.00') <= self.cgpa <= Decimal('4.00')):
            raise ValidationError({'cgpa': f'CGPA {self.cgpa} is outside 0.00–4.00.'})

    def __str__(self):
        return (
            f'Cumulative summary: {self.student.student_id} '
            f'CGPA={self.cgpa} rank={self.cumulative_rank}'
        )
