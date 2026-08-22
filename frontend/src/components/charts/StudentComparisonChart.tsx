import React from 'react';
import { Card } from '../common/Card';
import { Badge } from '../common/Badge';
import { CourseComparisonItem, ComparedStudentProfile, ComparisonDeltas } from '../../types/comparison';
import { Scale } from 'lucide-react';

interface StudentComparisonChartProps {
  studentA: ComparedStudentProfile;
  studentB: ComparedStudentProfile;
  deltas?: ComparisonDeltas;
  courseComparisons: CourseComparisonItem[];
}

export const StudentComparisonChart: React.FC<StudentComparisonChartProps> = ({
  studentA,
  studentB,
  courseComparisons = [],
}) => {
  return (
    <Card glass className="p-6 border-slate-200 dark:border-slate-800 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 border-b border-slate-200 dark:border-slate-800 pb-3">
        <div>
          <div className="flex flex-wrap items-center gap-2 mb-1">
            <Scale className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0" />
            <h4 className="font-bold text-sm text-slate-900 dark:text-slate-100">
              Visual Head-to-Head Comparative Bar Chart
            </h4>
            <Badge variant="emerald" size="sm">Course GP Deltas</Badge>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Comparing Course GP performance between <strong className="text-emerald-600 dark:text-emerald-400">{studentA.name}</strong> ({studentA.id}) and <strong className="text-sky-600 dark:text-sky-400">{studentB.name}</strong> ({studentB.id}).
          </p>
        </div>
      </div>

      {/* Visual Bar Comparison per Course */}
      <div className="space-y-3">
        {courseComparisons.map((c) => {
          const gpA = c.student_a_gp || 0.0;
          const gpB = c.student_b_gp || 0.0;
          const pctA = (gpA / 4.0) * 100;
          const pctB = (gpB / 4.0) * 100;
          const delta = c.delta_gp;

          const deltaLabel = delta && delta > 0
            ? `+${delta.toFixed(2)} (A)`
            : delta && delta < 0
              ? `${delta.toFixed(2)} (B)`
              : 'Tied';
          const deltaColor = delta && delta > 0
            ? 'text-emerald-600 dark:text-emerald-400'
            : delta && delta < 0
              ? 'text-sky-600 dark:text-sky-400'
              : 'text-slate-500 dark:text-slate-400';

          return (
            <div key={c.course_code} className="p-3 bg-white dark:bg-slate-950/60 rounded-xl border border-slate-200 dark:border-slate-800 space-y-2.5 shadow-sm">
              {/* Row 1: Course code + name + delta */}
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0 flex-1">
                  <span className="font-mono font-bold text-xs text-slate-900 dark:text-slate-200">{c.course_code}</span>
                  <p className="text-xs text-slate-500 dark:text-slate-400 truncate mt-0.5">{c.course_title}</p>
                </div>
                <span className={`font-mono font-bold text-xs shrink-0 ${deltaColor}`}>
                  {deltaLabel}
                </span>
              </div>

              {/* Row 2: A vs B GP values side by side */}
              <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                <div className="flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-emerald-500 shrink-0" />
                  <span className="text-slate-500 dark:text-slate-400">A:</span>
                  <span className="font-bold text-emerald-600 dark:text-emerald-400">{gpA.toFixed(2)} GP</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-sky-500 shrink-0" />
                  <span className="text-slate-500 dark:text-slate-400">B:</span>
                  <span className="font-bold text-sky-600 dark:text-sky-400">{gpB.toFixed(2)} GP</span>
                </div>
              </div>

              {/* Row 3: Side-by-Side Progress Bars */}
              <div className="grid grid-cols-2 gap-2">
                <div className="w-full h-2 rounded-full bg-slate-100 dark:bg-slate-900 overflow-hidden border border-slate-200 dark:border-slate-800">
                  <div
                    className="h-full bg-emerald-500 rounded-full transition-all duration-300"
                    style={{ width: `${Math.max(pctA, 3)}%` }}
                  />
                </div>
                <div className="w-full h-2 rounded-full bg-slate-100 dark:bg-slate-900 overflow-hidden border border-slate-200 dark:border-slate-800">
                  <div
                    className="h-full bg-sky-500 rounded-full transition-all duration-300"
                    style={{ width: `${Math.max(pctB, 3)}%` }}
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
