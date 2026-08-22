from django.contrib import admin
from .models import (
    ResultSheet,
    Course,
    Student,
    StudentResult,
    CurrentSemesterSummary,
    CumulativeSummary,
)


class CourseInline(admin.TabularInline):
    model = Course
    extra = 0
    readonly_fields = ('course_code', 'course_name', 'credit_hours_raw', 'credit_hours', 'column_index')


class StudentInline(admin.TabularInline):
    model = Student
    extra = 0
    readonly_fields = ('student_id', 'student_name', 'row_index', 'extraction_confidence', 'has_warnings')


@admin.register(ResultSheet)
class ResultSheetAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'original_filename', 'status', 'detected_student_count',
        'detected_course_count', 'parsing_confidence', 'uploaded_at',
    )
    list_filter = ('status', 'file_type')
    search_fields = ('original_filename', 'detected_institution', 'detected_semester')
    readonly_fields = ('id', 'uploaded_at', 'processing_started_at', 'processing_finished_at')
    inlines = [CourseInline, StudentInline]


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('dataset', 'course_code', 'course_name', 'credit_hours', 'column_index')
    search_fields = ('course_code', 'course_name')
    list_filter = ('dataset',)


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('dataset', 'student_id', 'student_name', 'row_index', 'has_warnings', 'extraction_confidence')
    search_fields = ('student_id', 'student_name')
    list_filter = ('dataset', 'has_warnings')


@admin.register(StudentResult)
class StudentResultAdmin(admin.ModelAdmin):
    list_display = ('dataset', 'student', 'course', 'letter_grade', 'grade_point', 'cell_confidence', 'is_valid_gp_lg_match')
    list_filter = ('letter_grade', 'is_valid_gp_lg_match')
    search_fields = ('student__student_id', 'course__course_code')


@admin.register(CurrentSemesterSummary)
class CurrentSemesterSummaryAdmin(admin.ModelAdmin):
    list_display = ('dataset', 'student', 'gpa', 'calculated_gpa', 'credits_earned', 'semester_rank', 'is_gpa_arithmetic_valid')
    list_filter = ('is_gpa_arithmetic_valid',)


@admin.register(CumulativeSummary)
class CumulativeSummaryAdmin(admin.ModelAdmin):
    list_display = ('dataset', 'student', 'cgpa', 'calculated_cgpa', 'total_credits_earned', 'cumulative_rank', 'is_cgpa_arithmetic_valid')
    list_filter = ('is_cgpa_arithmetic_valid',)
