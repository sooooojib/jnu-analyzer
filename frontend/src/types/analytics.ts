export interface DistributionStudent {
  student_id: string;
  student_name: string;
  gpa: number;
}

export interface MetricDistributionItem {
  bracket: string;
  count: number;
  percentage: number;
  students?: DistributionStudent[];
}

export interface ClassAnalysis {
  total_students: number;
  students_with_gpa_count: number;
  average_gpa: number;
  median_gpa: number;
  mode_gpa: number;
  highest_gpa: number;
  lowest_gpa: number;
  std_dev_gpa: number;
  distribution: MetricDistributionItem[];
}

export interface CumulativeAnalysis {
  total_students: number;
  students_with_cgpa_count: number;
  average_cgpa: number;
  median_cgpa: number;
  mode_cgpa: number;
  highest_cgpa: number;
  lowest_cgpa: number;
  std_dev_cgpa: number;
  distribution: MetricDistributionItem[];
}

export interface SubjectTopper {
  student_id: string;
  student_name: string;
  gp: number;
  letter_grade: string;
}

export interface SubjectAnalysisItem {
  course_code: string;
  course_title: string;
  credit_hours: number;
  number_of_students: number;
  average_gp: number;
  median_gp: number;
  mode_gp: number;
  highest_gp: number;
  lowest_gp: number;
  std_dev_gp: number;
  highest_performing_students: SubjectTopper[];
  grade_counts: Record<string, number>;
  selected_student_gp?: number | null;
  selected_student_letter_grade?: string | null;
  selected_student_subject_rank?: number | null;
  selected_student_diff_from_average?: number | null;
  selected_student_percentile?: number | null;
}

export interface StudentLeaderboardItem {
  rank: number;
  student_id: string;
  student_name: string;
  gpa: number;
  cgpa: number;
  semester_rank?: number | null;
  cumulative_rank?: number | null;
  status: string;
}

export interface CohortAnalytics {
  class_analysis?: ClassAnalysis;
  cumulative_analysis?: CumulativeAnalysis;
  subject_analysis?: SubjectAnalysisItem[];
  student_leaderboard?: StudentLeaderboardItem[];
  summary_metrics?: {
    count: number;
    mean: number;
    median: number;
    mode: number;
    std_dev: number;
    min: number;
    max: number;
  };
  gpa_distribution_histogram?: MetricDistributionItem[];
  subject_wise_breakdown?: any[];
  leaderboard?: any[];
}
