export type ValidationStatus = 'VALID' | 'WARNING' | 'NEEDS_REVIEW' | 'INVALID';

export interface VerificationSummary {
  total_students: number;
  total_courses: number;
  valid_fields_count: number;
  warnings_count: number;
  invalid_fields_count: number;
  needs_review_count: number;
}

export interface VerificationCourse {
  course_code: string;
  course_title: string;
  credit_hours: number;
  column_index: number;
}

export interface VerificationRowItem {
  row_id: string;
  student_id: string;
  student_name: string;
  course_code: string;
  credit_hours: number | string;
  grade_point: number | null;
  letter_grade: string;
  status: ValidationStatus;
  warnings: string[];
  errors: string[];
  applied_corrections: string[];
  is_usable_in_calculations: boolean;
  cell_coordinates?: [number, number, number, number];
}

export interface VerificationDataResponse {
  session_id: string;
  status: 'PENDING_VERIFICATION' | 'VERIFIED' | 'COMPLETED' | 'PROCESSING' | 'PENDING';
  original_filename: string;
  summary: VerificationSummary;
  courses: VerificationCourse[];
  rows: VerificationRowItem[];
  students: any[];
}

export interface CellUpdateRequest {
  student_id: string;
  course_code?: string;
  field_name: 'grade_point' | 'letter_grade' | 'student_name' | 'student_id' | 'credit_hours';
  new_value: string;
}
