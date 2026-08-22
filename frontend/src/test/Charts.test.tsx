import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { SubjectGPComparisonChart } from '../components/charts/SubjectGPComparisonChart';
import { SubjectRankingChart } from '../components/charts/SubjectRankingChart';
import { StudentComparisonChart } from '../components/charts/StudentComparisonChart';
import { CourseGradeItem } from '../types/student';
import { ComparedStudentProfile, CourseComparisonItem } from '../types/comparison';
import { SubjectAnalysisItem } from '../types/analytics';

describe('Academic Chart Visualizations Tests', () => {
  it('renders SubjectGPComparisonChart with course bars and delta badges', () => {
    const courseGrades: CourseGradeItem[] = [
      {
        course_code: 'CSE-2201',
        course_title: 'Object Oriented Programming',
        credits: 3.0,
        grade_point: 4.00,
        letter_grade: 'A+',
        subject_rank: 1,
        status: 'VALID',
      },
      {
        course_code: 'MAT-2101',
        course_title: 'Discrete Mathematics',
        credits: 3.0,
        grade_point: 3.50,
        letter_grade: 'A-',
        subject_rank: 4,
        status: 'VALID',
      },
    ];

    const subjectAnalytics: SubjectAnalysisItem[] = [
      {
        course_code: 'CSE-2201',
        course_title: 'Object Oriented Programming',
        credit_hours: 3.0,
        average_gp: 3.65,
        median_gp: 3.75,
        mode_gp: 3.75,
        highest_gp: 4.00,
        lowest_gp: 2.75,
        std_dev_gp: 0.25,
        number_of_students: 24,
        highest_performing_students: [],
        grade_counts: { 'A+': 4, 'A': 12, 'A-': 6, 'B': 2 },
      },
      {
        course_code: 'MAT-2101',
        course_title: 'Discrete Mathematics',
        credit_hours: 3.0,
        average_gp: 3.55,
        median_gp: 3.50,
        mode_gp: 3.50,
        highest_gp: 4.00,
        lowest_gp: 2.50,
        std_dev_gp: 0.30,
        number_of_students: 24,
        highest_performing_students: [],
        grade_counts: { 'A+': 2, 'A': 10, 'A-': 8, 'B': 4 },
      },
    ];

    render(
      <SubjectGPComparisonChart
        courseGrades={courseGrades}
        subjectAnalytics={subjectAnalytics}
      />
    );

    expect(screen.getByText(/Subject-by-Subject Grade Point \(GP\) Comparison/i)).toBeInTheDocument();
    expect(screen.getByText('CSE-2201')).toBeInTheDocument();
    expect(screen.getByText('MAT-2101')).toBeInTheDocument();
    expect(screen.getAllByText(/4\.00 GP/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/3\.50 GP/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Highest:/i).length).toBeGreaterThan(0);
  });

  it('renders SubjectRankingChart with ranking medals and percentiles', () => {
    const courseGrades: CourseGradeItem[] = [
      {
        course_code: 'CSE-2201',
        course_title: 'Object Oriented Programming',
        credits: 3.0,
        grade_point: 4.00,
        letter_grade: 'A+',
        subject_rank: 1,
        status: 'VALID',
      },
      {
        course_code: 'CSE-2202',
        course_title: 'Data Structures Lab',
        credits: 1.5,
        grade_point: 3.75,
        letter_grade: 'A',
        subject_rank: 3,
        status: 'VALID',
      },
    ];

    render(<SubjectRankingChart courseGrades={courseGrades} totalStudents={24} />);

    expect(screen.getByText(/Subject-Specific Ranking & Relative Standing/i)).toBeInTheDocument();
    expect(screen.getByText(/#1 Topper/i)).toBeInTheDocument();
    expect(screen.getByText(/#3 of 24/i)).toBeInTheDocument();
  });

  it('renders StudentComparisonChart with side-by-side delta bars', () => {
    const studentA: ComparedStudentProfile = {
      id: '2102045',
      name: 'ALICE JOHNSON',
      gpa: 3.85,
      cgpa: 3.80,
      semester_rank: 1,
      cumulative_rank: 2,
      credits_earned: 60.0,
      result_status: 'PASSED',
    };

    const studentB: ComparedStudentProfile = {
      id: '2102046',
      name: 'BOB SMITH',
      gpa: 3.50,
      cgpa: 3.45,
      semester_rank: 4,
      cumulative_rank: 5,
      credits_earned: 58.5,
      result_status: 'PASSED',
    };

    const courseComparisons: CourseComparisonItem[] = [
      {
        course_code: 'CSE-2201',
        course_title: 'OOP',
        credits: 3.0,
        student_a_gp: 4.00,
        student_a_grade: 'A+',
        student_b_gp: 3.50,
        student_b_grade: 'A-',
        delta_gp: 0.50,
        better_performer: 'STUDENT_A',
      },
      {
        course_code: 'MAT-2101',
        course_title: 'Math',
        credits: 3.0,
        student_a_gp: 3.50,
        student_a_grade: 'A-',
        student_b_gp: 4.00,
        student_b_grade: 'A+',
        delta_gp: -0.50,
        better_performer: 'STUDENT_B',
      },
    ];

    render(
      <StudentComparisonChart
        studentA={studentA}
        studentB={studentB}
        courseComparisons={courseComparisons}
      />
    );

    expect(screen.getByText(/Visual Head-to-Head Comparative Bar Chart/i)).toBeInTheDocument();
    expect(screen.getByText('ALICE JOHNSON')).toBeInTheDocument();
    expect(screen.getByText('BOB SMITH')).toBeInTheDocument();
  });
});
