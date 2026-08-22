import React, { useState } from 'react';
import { Card } from '../common/Card';
import { Badge } from '../common/Badge';
import { BookOpen, Table as TableIcon, Award } from 'lucide-react';
import { CourseGradeItem } from '../../types/student';
import { SubjectAnalysisItem } from '../../types/analytics';

interface SubjectGPComparisonChartProps {
  courseGrades: CourseGradeItem[];
  subjectAnalytics?: SubjectAnalysisItem[];
}

export const SubjectGPComparisonChart: React.FC<SubjectGPComparisonChartProps> = ({
  courseGrades = [],
  subjectAnalytics = [],
}) => {
  const [hoveredCourse, setHoveredCourse] = useState<string | null>(null);
  const [showTableView, setShowTableView] = useState(false);

  // Build merged map of course code -> { student_gp, class_avg_gp, highest_gp, credits }
  const courseMap = new Map<string, {
    course_code: string;
    course_title: string;
    credits: number;
    student_gp: number | null;
    student_grade: string;
    class_avg_gp: number;
    highest_gp: number;
    lowest_gp: number;
  }>();

  courseGrades.forEach((cg) => {
    courseMap.set(cg.course_code, {
      course_code: cg.course_code,
      course_title: cg.course_title || cg.course_code,
      credits: cg.credits,
      student_gp: cg.grade_point,
      student_grade: cg.letter_grade,
      class_avg_gp: 0.0,
      highest_gp: 4.0,
      lowest_gp: 0.0,
    });
  });

  subjectAnalytics.forEach((sa) => {
    const existing = courseMap.get(sa.course_code);
    if (existing) {
      existing.class_avg_gp = sa.average_gp;
      existing.highest_gp = sa.highest_gp;
      existing.lowest_gp = sa.lowest_gp;
    } else {
      courseMap.set(sa.course_code, {
        course_code: sa.course_code,
        course_title: sa.course_title,
        credits: sa.credit_hours,
        student_gp: null,
        student_grade: '—',
        class_avg_gp: sa.average_gp,
        highest_gp: sa.highest_gp,
        lowest_gp: sa.lowest_gp,
      });
    }
  });

  const comparisonData = Array.from(courseMap.values());

  return (
    <Card glass className="p-6 border-slate-200 dark:border-slate-800 space-y-4">
      {/* Header */}
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 border-b border-slate-200 dark:border-slate-800 pb-3">
        <div className="space-y-1 min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <BookOpen className="w-4 h-4 text-amber-500 dark:text-amber-400 shrink-0" />
            <h4 className="font-bold text-sm text-slate-900 dark:text-slate-100">
              Subject-by-Subject Grade Point (GP) Comparison
            </h4>
            <Badge variant="amber" size="sm">
              Unweighted Single-Subject GP (0.00 – 4.00)
            </Badge>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Comparing student's course GP against class average GP and cohort peak GP across all curriculum subjects.
          </p>
        </div>

        <button
          onClick={() => setShowTableView(!showTableView)}
          className="flex items-center gap-1 text-xs text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 transition-colors px-2.5 py-1.5 rounded-xl bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 font-medium shrink-0"
        >
          <TableIcon className="w-3.5 h-3.5" />
          {showTableView ? 'Visual Chart View' : 'Tabular Table View'}
        </button>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap items-center gap-3 sm:gap-5 text-xs font-mono bg-slate-100/70 dark:bg-slate-950/60 p-3 rounded-xl border border-slate-200 dark:border-slate-800/80">
        <div className="flex items-center gap-2">
          <span className="w-3 h-3 rounded-full bg-emerald-500 dark:bg-emerald-400 shadow-sm shadow-emerald-500/50 shrink-0" />
          <span className="text-slate-800 dark:text-slate-200 font-sans font-bold">Student GP</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-3 h-3 rounded-full bg-sky-500 dark:bg-sky-400 shadow-sm shadow-sky-500/50 shrink-0" />
          <span className="text-slate-700 dark:text-slate-300 font-sans">Class Average GP</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-3 h-3 rounded-full bg-amber-500 dark:bg-amber-400 shadow-sm shadow-amber-500/50 shrink-0" />
          <span className="text-slate-700 dark:text-slate-300 font-sans font-semibold">Highest GP (Cohort Peak)</span>
        </div>
      </div>

      {/* Table View */}
      {showTableView ? (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-slate-100 dark:bg-slate-950 text-slate-700 dark:text-slate-400 border-b border-slate-200 dark:border-slate-800">
              <tr>
                <th className="p-2.5">Course</th>
                <th className="p-2.5 text-center">Credit</th>
                <th className="p-2.5 text-center">Student GP</th>
                <th className="p-2.5 text-center">Grade</th>
                <th className="p-2.5 text-center">Class Avg GP</th>
                <th className="p-2.5 text-center">Highest GP</th>
                <th className="p-2.5 text-center">Diff from Avg</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200/60 dark:divide-slate-800/60 text-slate-700 dark:text-slate-300">
              {comparisonData.map((item) => {
                const diff = item.student_gp !== null ? item.student_gp - item.class_avg_gp : null;
                return (
                  <tr key={item.course_code} className="hover:bg-slate-50 dark:hover:bg-slate-900/40">
                    <td className="p-2.5 font-bold text-slate-900 dark:text-slate-200">
                      {item.course_code}
                      <span className="block text-[11px] text-slate-500 dark:text-slate-400 font-sans">{item.course_title}</span>
                    </td>
                    <td className="p-2.5 text-center text-slate-500 dark:text-slate-400">{item.credits.toFixed(1)}</td>
                    <td className="p-2.5 text-center font-bold text-emerald-600 dark:text-emerald-400">
                      {item.student_gp !== null ? item.student_gp.toFixed(2) : '—'}
                    </td>
                    <td className="p-2.5 text-center">{item.student_grade}</td>
                    <td className="p-2.5 text-center text-sky-600 dark:text-sky-400 font-bold">{item.class_avg_gp.toFixed(2)}</td>
                    <td className="p-2.5 text-center text-amber-600 dark:text-amber-400 font-bold">{item.highest_gp.toFixed(2)}</td>
                    <td className="p-2.5 text-center font-bold">
                      {diff !== null ? (
                        <span className={diff >= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-rose-600 dark:text-rose-400'}>
                          {diff >= 0 ? `+${diff.toFixed(2)}` : diff.toFixed(2)} GP
                        </span>
                      ) : (
                        '—'
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : (
        /* Grouped Visual Multi-Bar Chart */
        <div className="space-y-4 pt-2">
          {comparisonData.map((item) => {
            const studentVal = item.student_gp || 0.0;
            const avgVal = item.class_avg_gp || 0.0;
            const highestVal = item.highest_gp || 4.0;

            const studentPct = (studentVal / 4.0) * 100;
            const avgPct = (avgVal / 4.0) * 100;
            const highestPct = (highestVal / 4.0) * 100;

            const isHovered = hoveredCourse === item.course_code;

            return (
              <div
                key={item.course_code}
                className={`p-3.5 rounded-2xl transition-all border ${
                  isHovered
                    ? 'bg-slate-100/90 dark:bg-slate-900/90 border-amber-500/50 shadow-md'
                    : 'bg-white dark:bg-slate-950/40 border-slate-200 dark:border-slate-800/80 shadow-sm'
                }`}
                onMouseEnter={() => setHoveredCourse(item.course_code)}
                onMouseLeave={() => setHoveredCourse(null)}
              >
                {/* Course Header & Metric Stats */}
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between text-xs gap-2 mb-2.5">
                  <div className="flex items-center gap-2 flex-wrap min-w-0">
                    <span className="font-mono font-bold text-slate-800 dark:text-slate-100 bg-slate-100 dark:bg-slate-900 px-2 py-0.5 rounded border border-slate-200 dark:border-slate-800 shrink-0">
                      {item.course_code}
                    </span>
                    <span className="text-slate-800 dark:text-slate-300 font-medium truncate max-w-xs sm:max-w-sm">{item.course_title}</span>
                    <Badge variant="slate" size="sm" className="shrink-0">{item.credits} cr</Badge>
                  </div>

                  <div className="flex items-center gap-2 sm:gap-3 font-mono text-xs flex-wrap">
                    <span className="text-emerald-600 dark:text-emerald-400 font-bold flex items-center gap-1">
                      Student: {studentVal > 0 ? studentVal.toFixed(2) : '—'} GP ({item.student_grade})
                    </span>
                    <span className="text-slate-300 dark:text-slate-600 hidden sm:inline">|</span>
                    <span className="text-sky-600 dark:text-sky-400 font-medium">Avg: {avgVal.toFixed(2)} GP</span>
                    <span className="text-slate-300 dark:text-slate-600 hidden sm:inline">|</span>
                    <span className="text-amber-600 dark:text-amber-400 font-bold flex items-center gap-1">
                      <Award className="w-3 h-3 text-amber-500 dark:text-amber-400 shrink-0" />
                      Highest: {highestVal.toFixed(2)} GP
                    </span>
                  </div>
                </div>

                {/* 3 Comparative Multi-Bars: Student, Class Avg, Highest GP */}
                <div className="space-y-1.5 pt-1">
                  {/* 1. Student GP Bar */}
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-sans text-emerald-600 dark:text-emerald-400 font-semibold w-16">Student</span>
                    <div className="w-full h-2 rounded-full bg-slate-100 dark:bg-slate-950 overflow-hidden border border-slate-200 dark:border-slate-800">
                      <div
                        className="h-full bg-emerald-500 rounded-full transition-all duration-300"
                        style={{ width: `${Math.max(studentPct, 2)}%` }}
                      />
                    </div>
                  </div>

                  {/* 2. Class Avg GP Bar */}
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-sans text-sky-600 dark:text-sky-400 w-16">Class Avg</span>
                    <div className="w-full h-2 rounded-full bg-slate-100 dark:bg-slate-950 overflow-hidden border border-slate-200 dark:border-slate-800">
                      <div
                        className="h-full bg-sky-500 rounded-full transition-all duration-300"
                        style={{ width: `${Math.max(avgPct, 2)}` + '%' }}
                      />
                    </div>
                  </div>

                  {/* 3. Highest GP Bar */}
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-sans text-amber-600 dark:text-amber-400 font-semibold w-16">Highest</span>
                    <div className="w-full h-2 rounded-full bg-slate-100 dark:bg-slate-950 overflow-hidden border border-slate-200 dark:border-slate-800">
                      <div
                        className="h-full bg-amber-400 rounded-full transition-all duration-300 shadow-sm shadow-amber-500/50"
                        style={{ width: `${Math.max(highestPct, 2)}` + '%' }}
                      />
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </Card>
  );
};
