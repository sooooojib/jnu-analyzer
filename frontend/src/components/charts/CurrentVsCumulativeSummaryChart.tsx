import React from 'react';
import { Card } from '../common/Card';
import { Badge } from '../common/Badge';
import { Layers, GraduationCap, ArrowUpRight, ArrowDownRight } from 'lucide-react';

interface CurrentVsCumulativeSummaryChartProps {
  semesterGPA: number;
  semesterRank?: number;
  semesterPercentile?: number;
  semesterCreditsEarned: number;
  semesterCreditsAttempted: number;
  semesterStatus?: string;
  cumulativeCGPA: number;
  cumulativeRank?: number;
  cumulativePercentile?: number;
  cumulativeCreditsEarned: number;
  cumulativeStatus?: string;
}

export const CurrentVsCumulativeSummaryChart: React.FC<CurrentVsCumulativeSummaryChartProps> = ({
  semesterGPA,
  semesterRank,
  semesterPercentile,
  semesterCreditsEarned,
  semesterCreditsAttempted,
  semesterStatus = 'PASSED',
  cumulativeCGPA,
  cumulativeRank,
  cumulativePercentile,
  cumulativeCreditsEarned,
  cumulativeStatus = 'PASSED',
}) => {
  const gpaDelta = semesterGPA - cumulativeCGPA;
  const isPositiveGrowth = gpaDelta >= 0;

  return (
    <Card glass className="p-5 sm:p-6 border-slate-200 dark:border-slate-800 space-y-6 shadow-md">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 border-b border-slate-200 dark:border-slate-800 pb-3">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Layers className="w-4 h-4 text-sky-600 dark:text-sky-400 shrink-0" />
            <h4 className="font-bold text-sm text-slate-900 dark:text-slate-100">
              Current Semester vs. Cumulative Academic Summary
            </h4>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Comparing Current Semester performance against Cumulative record (extracted directly from sheet).
          </p>
        </div>

        <Badge variant={isPositiveGrowth ? 'emerald' : 'amber'} size="md" className="gap-1 font-mono font-bold">
          {isPositiveGrowth ? <ArrowUpRight className="w-3.5 h-3.5" /> : <ArrowDownRight className="w-3.5 h-3.5" />}
          {isPositiveGrowth ? '+' : ''}{gpaDelta.toFixed(2)} GPA vs Cumulative CGPA
        </Badge>
      </div>

      {/* Side-by-Side Comparative Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Card 1: Current Semester */}
        <div className="p-5 rounded-2xl bg-emerald-50/60 dark:bg-slate-950/60 border border-emerald-500/30 dark:border-emerald-500/20 space-y-4">
          <div className="flex items-center justify-between border-b border-emerald-200/60 dark:border-slate-800/80 pb-3">
            <div className="flex items-center gap-2">
              <GraduationCap className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
              <h5 className="font-bold text-xs text-emerald-700 dark:text-emerald-400 uppercase tracking-wider">
                Current Semester Result
              </h5>
            </div>
            <Badge variant="emerald" size="sm">{semesterStatus}</Badge>
          </div>

          <div className="flex items-baseline justify-between">
            <div>
              <span className="text-[10px] text-slate-500 dark:text-slate-400 uppercase font-sans font-semibold">Current-Semester GPA</span>
              <div className="text-3xl font-black font-mono text-emerald-600 dark:text-emerald-400 mt-0.5">
                {semesterGPA.toFixed(2)}
              </div>
            </div>
            <div className="text-right">
              <span className="text-[10px] text-slate-500 dark:text-slate-400 uppercase font-sans font-semibold">Semester Rank</span>
              <div className="text-xl font-bold font-mono text-amber-600 dark:text-amber-400 mt-0.5">
                {semesterRank != null ? `#${semesterRank}` : '—'}
              </div>
            </div>
          </div>

          <div className="pt-2 border-t border-emerald-200/60 dark:border-slate-800/80 grid grid-cols-2 gap-2 text-xs font-mono text-slate-600 dark:text-slate-300">
            <div>Credits Earned: <strong className="text-slate-900 dark:text-slate-100">{semesterCreditsEarned.toFixed(1)} / {semesterCreditsAttempted.toFixed(1)}</strong></div>
            <div className="text-right">Percentile: <strong className="text-sky-600 dark:text-sky-400">{semesterPercentile != null ? `${semesterPercentile.toFixed(1)}%` : '—'}</strong></div>
          </div>
        </div>

        {/* Card 2: Cumulative CGPA */}
        <div className="p-5 rounded-2xl bg-sky-50/60 dark:bg-slate-950/60 border border-sky-500/30 dark:border-sky-500/20 space-y-4">
          <div className="flex items-center justify-between border-b border-sky-200/60 dark:border-slate-800/80 pb-3">
            <div className="flex items-center gap-2">
              <Layers className="w-4 h-4 text-sky-600 dark:text-sky-400" />
              <h5 className="font-bold text-xs text-sky-700 dark:text-sky-400 uppercase tracking-wider">
                Cumulative Result (From Sheet)
              </h5>
            </div>
            <Badge variant="blue" size="sm">{cumulativeStatus}</Badge>
          </div>

          <div className="flex items-baseline justify-between">
            <div>
              <span className="text-[10px] text-slate-500 dark:text-slate-400 uppercase font-sans font-semibold">Cumulative CGPA</span>
              <div className="text-3xl font-black font-mono text-sky-600 dark:text-sky-400 mt-0.5">
                {cumulativeCGPA.toFixed(2)}
              </div>
            </div>
            <div className="text-right">
              <span className="text-[10px] text-slate-500 dark:text-slate-400 uppercase font-sans font-semibold">Cumulative Rank</span>
              <div className="text-xl font-bold font-mono text-purple-600 dark:text-purple-400 mt-0.5">
                {cumulativeRank != null ? `#${cumulativeRank}` : '—'}
              </div>
            </div>
          </div>

          <div className="pt-2 border-t border-sky-200/60 dark:border-slate-800/80 grid grid-cols-2 gap-2 text-xs font-mono text-slate-600 dark:text-slate-300">
            <div>Total Earned Cr: <strong className="text-slate-900 dark:text-slate-100">{cumulativeCreditsEarned.toFixed(1)}</strong></div>
            <div className="text-right">Percentile: <strong className="text-purple-600 dark:text-purple-400">{cumulativePercentile != null ? `${cumulativePercentile.toFixed(1)}%` : '—'}</strong></div>
          </div>
        </div>
      </div>
    </Card>
  );
};
