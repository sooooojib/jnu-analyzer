export interface CourseComparisonItem {
  course_code: string;
  course_title?: string;
  credits: number;
  student_a_gp: number | null;
  student_a_grade: string;
  student_b_gp: number | null;
  student_b_grade: string;
  delta_gp: number | null;
  better_performer: 'STUDENT_A' | 'STUDENT_B' | 'TIED' | 'N/A';
  cohort_average_gp?: number;
}

export interface ComparedStudentProfile {
  id: string;
  name: string;
  gpa: number;
  cgpa: number;
  semester_rank?: number;
  semester_percentile?: number;
  cumulative_rank?: number;
  cumulative_percentile?: number;
  credits_earned?: number;
  result_status?: string;
}

export interface ComparisonDeltas {
  gpa_diff: number;
  cgpa_diff: number;
  average_gp_diff: number;
  semester_rank_diff: number;
  cumulative_rank_diff: number;
}

export interface SubjectTally {
  a_better_count: number;
  b_better_count: number;
  tied_count: number;
  subjects_a_better: string[];
  subjects_b_better: string[];
  subjects_tied: string[];
}

export interface StudentComparisonResult {
  student_a: ComparedStudentProfile;
  student_b: ComparedStudentProfile;
  deltas: ComparisonDeltas;
  subject_tally: SubjectTally;
  course_comparison: CourseComparisonItem[];
}
