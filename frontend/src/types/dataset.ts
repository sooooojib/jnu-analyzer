export interface CourseInfo {
  code: string;
  title: string;
  credits: number;
}

export interface SheetMetadata {
  institution?: string;
  program?: string;
  semester?: string;
  exam_session?: string;
  total_students_detected: number;
  total_courses_detected: number;
  parsing_confidence_score: number;
}

export interface ParsedDataset {
  courses: CourseInfo[];
  students: Array<Record<string, unknown>>;
  confidence_score: number;
}
