import React from 'react';
import { Card } from '../common/Card';
import { Badge } from '../common/Badge';
import { TrendingUp, ArrowUpRight, ArrowDownRight } from 'lucide-react';

interface StudentVsClassAverageChartProps {
  studentGPA: number;
  studentName: string;
  studentId: string;
  classMeanGPA: number;
  classMedianGPA: number;
  classHighestGPA: number;
  classLowestGPA: number;
  classStdDev?: number;
  totalStudents: number;
}

export const StudentVsClassAverageChart: React.FC<StudentVsClassAverageChartProps> = ({
  studentGPA,
  studentName,
  studentId,
  classMeanGPA,
  classMedianGPA,
  classHighestGPA,
  classLowestGPA,
  classStdDev = 0.0,
  totalStudents,
}) => {
  const diffFromMean = studentGPA - classMeanGPA;
  const isAboveAverage = diffFromMean >= 0;

  // Percentage on 0.0 - 4.0 scale
  const studentPct = (studentGPA / 4.0) * 100;
  const meanPct = (classMeanGPA / 4.0) * 100;
  const medianPct = (classMedianGPA / 4.0) * 100;

  return (
    <Card glass className="p-4 sm:p-6 border-slate-800 space-y-4 sm:space-y-6">
      {/* Header */}
      <div className="border-b border-slate-800 pb-3 space-y-2">
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-2 min-w-0">
            <TrendingUp className="w-4 h-4 text-emerald-400 shrink-0" />
            <h4 className="font-bold text-sm text-slate-100 leading-tight">
              Student vs. Class Cohort Performance
            </h4>
          </div>
          <Badge variant="blue" size="sm" className="shrink-0 whitespace-nowrap">Current-Semester GPA</Badge>
        </div>
        <p className="text-xs text-slate-400 leading-relaxed">
          Comparing <strong className="text-slate-200">{studentName}</strong>{' '}
          <span className="font-mono text-slate-400">({studentId})</span> against {totalStudents} verified students.
        </p>
        <Badge variant={isAboveAverage ? 'emerald' : 'amber'} size="sm" className="gap-1 font-mono font-bold">
          {isAboveAverage ? <ArrowUpRight className="w-3.5 h-3.5" /> : <ArrowDownRight className="w-3.5 h-3.5" />}
          {isAboveAverage ? '+' : ''}{diffFromMean.toFixed(2)} GPA vs Class Mean
        </Badge>
      </div>

      {/* Primary Comparative Scale Bar (0.00 to 4.00) */}
      <div className="space-y-4">
        <div className="flex justify-between text-xs font-mono text-slate-400">
          <span>0.00 GPA</span>
          <span>Scale: 0.00 - 4.00 (Credit-Weighted)</span>
          <span>4.00 GPA</span>
        </div>

        <div className="relative h-10 bg-slate-100 dark:bg-slate-950 rounded-2xl border border-slate-200 dark:border-slate-800 overflow-hidden flex items-center px-1">
          {/* Class Mean Marker */}
          <div
            className="absolute top-0 bottom-0 w-0.5 bg-sky-500 dark:bg-sky-400 z-10"
            style={{ left: `${meanPct}%` }}
            title={`Class Mean: ${classMeanGPA.toFixed(2)}`}
          />

          {/* Class Median Marker */}
          <div
            className="absolute top-0 bottom-0 w-0.5 bg-purple-500 dark:bg-purple-400 z-10 border-dashed"
            style={{ left: `${medianPct}%` }}
            title={`Class Median: ${classMedianGPA.toFixed(2)}`}
          />

          {/* Student Position Bar */}
          <div
            className="h-6 rounded-xl bg-gradient-to-r from-emerald-600 to-emerald-400 transition-all duration-500 flex items-center justify-end pr-2 text-slate-950 font-black text-xs font-mono shadow-md"
            style={{ width: `${Math.max(studentPct, 8)}%` }}
          >
            {studentGPA.toFixed(2)}
          </div>
        </div>

        {/* Legend */}
        <div className="grid grid-cols-2 sm:flex sm:flex-wrap sm:items-center sm:justify-between gap-2 text-xs font-mono pt-1 text-slate-500 dark:text-slate-400">
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded bg-emerald-500 dark:bg-emerald-400 shrink-0" />
            <span>Student: <strong className="text-slate-900 dark:text-slate-200">{studentGPA.toFixed(2)}</strong></span>
          </div>

          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded bg-sky-500 dark:bg-sky-400 shrink-0" />
            <span>Mean: <strong className="text-sky-600 dark:text-sky-400">{classMeanGPA.toFixed(2)}</strong></span>
          </div>

          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded bg-purple-500 dark:bg-purple-400 shrink-0" />
            <span>Median: <strong className="text-purple-600 dark:text-purple-400">{classMedianGPA.toFixed(2)}</strong></span>
          </div>

          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded bg-amber-500 dark:bg-amber-400 shrink-0" />
            <span>Peak: <strong className="text-amber-600 dark:text-amber-400">{classHighestGPA.toFixed(2)}</strong></span>
          </div>
        </div>
      </div>

      {/* 4 Statistical Breakdown KPI Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2 text-center font-mono text-xs">
        <div className="p-3 bg-slate-50 dark:bg-slate-950/60 rounded-xl border border-slate-200 dark:border-slate-800">
          <span className="text-[10px] text-slate-500 dark:text-slate-400 uppercase font-sans font-semibold">Class Mean (μ)</span>
          <div className="text-base font-bold text-sky-600 dark:text-sky-400 mt-0.5">{classMeanGPA.toFixed(2)} GPA</div>
          <span className="text-[10px] text-slate-400 dark:text-slate-500 font-sans">Weighted Average</span>
        </div>

        <div className="p-3 bg-slate-50 dark:bg-slate-950/60 rounded-xl border border-slate-200 dark:border-slate-800">
          <span className="text-[10px] text-slate-500 dark:text-slate-400 uppercase font-sans font-semibold">Class Median</span>
          <div className="text-base font-bold text-purple-600 dark:text-purple-400 mt-0.5">{classMedianGPA.toFixed(2)} GPA</div>
          <span className="text-[10px] text-slate-400 dark:text-slate-500 font-sans">Middle Score</span>
        </div>

        <div className="p-3 bg-slate-50 dark:bg-slate-950/60 rounded-xl border border-slate-200 dark:border-slate-800">
          <span className="text-[10px] text-slate-500 dark:text-slate-400 uppercase font-sans font-semibold">Std Deviation (σ)</span>
          <div className="text-base font-bold text-slate-900 dark:text-slate-200 mt-0.5">±{classStdDev.toFixed(2)}</div>
          <span className="text-[10px] text-slate-400 dark:text-slate-500 font-sans">Cohort Spread</span>
        </div>

        <div className="p-3 bg-slate-50 dark:bg-slate-950/60 rounded-xl border border-slate-200 dark:border-slate-800">
          <span className="text-[10px] text-slate-500 dark:text-slate-400 uppercase font-sans font-semibold">Score Range</span>
          <div className="text-base font-bold text-amber-600 dark:text-amber-400 mt-0.5">
            {classLowestGPA.toFixed(2)} – {classHighestGPA.toFixed(2)}
          </div>
          <span className="text-[10px] text-slate-400 dark:text-slate-500 font-sans">Min – Max</span>
        </div>
      </div>
    </Card>
  );
};
