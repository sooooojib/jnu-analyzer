export interface CourseGradeItem {
  course_code: string;
  course_title: string;
  credits: number;
  grade_point: number | null;
  letter_grade: string;
  status?: string;
  review_reasons?: string[];
  subject_rank?: number;
  cohort_average_gp?: number;
}

export interface StudentRecord {
  student_id: string;
  student_name: string;
  serial_no?: number;
  status?: string;
  semester_result: {
    gpa: number;
    credits_attempted: number;
    credits_earned: number;
    semester_rank: number;
    semester_percentile: number;
    result_status?: string;
    remarks?: string;
  };
  cumulative_result: {
    cgpa: number;
    total_credits_earned: number;
    cumulative_rank: number;
    cumulative_percentile: number;
    result_status?: string;
    remarks?: string;
  };
  course_grades: CourseGradeItem[];
  current_semester_summary?: {
    gpa: number;
    total_credit?: number;
    earned_credit?: number;
    grade_points?: number;
    status?: string;
  };
  cumulative_summary?: {
    cgpa: number;
    total_credit?: number;
    earned_credit?: number;
    grade_points?: number;
    status?: string;
  };
  validation_status: {
    is_arithmetic_valid: boolean;
    calculated_gpa: number;
    confidence_score: number;
  };
  individual_analysis?: {
    student_id: string;
    student_name: string;
    subjects: Array<{
      course_code: string;
      course_title: string;
      credit: number;
      gp: number;
      letter_grade: string;
      subject_rank: number;
      cohort_course_avg: number;
    }>;
    current_semester: {
      gpa: number;
      total_credit?: number;
      earned_credit?: number;
      result_status?: string;
    };
    cumulative: {
      cgpa: number;
      total_credit?: number;
      earned_credit?: number;
      result_status?: string;
    };
    subject_gp_analysis?: {
      highest_subject_gp?: number;
      highest_subject_courses?: string[];
      lowest_subject_gp?: number;
      lowest_subject_courses?: string[];
      average_subject_gp?: number;
    };
  };
  metadata?: {
    institution?: string;
    semester?: string;
    exam_session?: string;
    original_filename?: string;
  };
}
