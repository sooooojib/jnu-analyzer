import React from 'react';
import { Card } from '../common/Card';
import { Badge } from '../common/Badge';
import { Trophy } from 'lucide-react';
import { CourseGradeItem } from '../../types/student';

interface SubjectRankingChartProps {
  courseGrades: CourseGradeItem[];
  totalStudents?: number;
}

export const SubjectRankingChart: React.FC<SubjectRankingChartProps> = ({
  courseGrades = [],
  totalStudents = 24,
}) => {
  return (
    <Card glass className="p-5 sm:p-6 border-slate-200 dark:border-slate-800 space-y-4 shadow-md">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 border-b border-slate-200 dark:border-slate-800 pb-3">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Trophy className="w-4 h-4 text-amber-500 dark:text-amber-400" />
            <h4 className="font-bold text-sm text-slate-900 dark:text-slate-100">Subject-Specific Ranking & Relative Standing</h4>
            <Badge variant="emerald" size="sm">Standard Competition ("1224")</Badge>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Student's rank standing and percentile rank across {courseGrades.length} enrolled subjects in this sheet.
          </p>
        </div>
      </div>

      {/* Subject Rank Matrix */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 pt-2">
        {courseGrades.map((cg) => {
          const rank = cg.subject_rank || 1;
          const isTopper = rank === 1;
          const percentile = Math.round(((totalStudents - rank + 1) / totalStudents) * 100);

          return (
            <div
              key={cg.course_code}
              className={`p-4 rounded-xl border transition-all ${
                isTopper
                  ? 'bg-amber-50 dark:bg-amber-950/20 border-amber-300 dark:border-amber-500/40 shadow-sm'
                  : 'bg-white dark:bg-slate-950/60 border-slate-200 dark:border-slate-800'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="font-mono font-bold text-xs text-sky-600 dark:text-sky-400">{cg.course_code}</span>
                {isTopper ? (
                  <Badge variant="amber" size="sm" className="gap-1 font-bold">
                    <Trophy className="w-3 h-3 text-amber-500" /> #1 Topper
                  </Badge>
                ) : (
                  <Badge variant="slate" size="sm">#{rank} of {totalStudents}</Badge>
                )}
              </div>

              <h5 className="font-bold text-sm text-slate-800 dark:text-slate-200 truncate mb-3" title={cg.course_title}>
                {cg.course_title || cg.course_code}
              </h5>

              <div className="space-y-2 pt-2 border-t border-slate-100 dark:border-slate-800/80 text-xs font-mono">
                <div className="flex justify-between text-slate-500 dark:text-slate-400">
                  <span>Score:</span>
                  <span className="text-slate-900 dark:text-slate-100 font-bold">
                    {cg.grade_point !== null ? cg.grade_point.toFixed(2) : '—'} GP ({cg.letter_grade})
                  </span>
                </div>

                <div className="flex justify-between text-slate-500 dark:text-slate-400">
                  <span>Percentile:</span>
                  <span className="text-emerald-600 dark:text-emerald-400 font-bold">
                    {percentile}% (Top {Math.max(1, 100 - percentile)}%)
                  </span>
                </div>

                {/* Progress bar representing percentile */}
                <div className="w-full h-1.5 rounded-full bg-slate-100 dark:bg-slate-900 overflow-hidden border border-slate-200 dark:border-slate-800">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${
                      isTopper ? 'bg-amber-500' : 'bg-emerald-500'
                    }`}
                    style={{ width: `${percentile}%` }}
                  />
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
};
