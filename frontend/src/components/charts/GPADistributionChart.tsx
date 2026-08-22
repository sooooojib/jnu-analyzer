import React, { useState } from 'react';
import { Card } from '../common/Card';
import { Badge } from '../common/Badge';
import { MetricDistributionItem } from '../../types/analytics';
import { BarChart3, Table as TableIcon } from 'lucide-react';

interface GPADistributionChartProps {
  distribution: MetricDistributionItem[];
  selectedStudentGPA?: number;
  classMeanGPA?: number;
  classMedianGPA?: number;
  totalStudents?: number;
  title?: string;
  metricLabel?: string;
}

export const GPADistributionChart: React.FC<GPADistributionChartProps> = ({
  distribution = [],
  selectedStudentGPA,
  classMeanGPA,
  classMedianGPA,
  totalStudents = 0,
  title = 'Class GPA Distribution (Current Semester)',
  metricLabel = 'Current-Semester GPA',
}) => {
  const [hoveredBracket, setHoveredBracket] = useState<MetricDistributionItem | null>(null);
  const [showTableView, setShowTableView] = useState(false);

  const maxCount = Math.max(...distribution.map((d) => d.count), 1);

  // Helper to determine if the selected student falls into this bracket
  const isStudentInBracket = (bracket: string, gpa?: number): boolean => {
    if (gpa === undefined || gpa === null) return false;
    if (bracket.includes('3.75') && gpa >= 3.75 && gpa <= 4.0) return true;
    if (bracket.includes('3.50') && gpa >= 3.50 && gpa < 3.75) return true;
    if (bracket.includes('3.00') && gpa >= 3.00 && gpa < 3.50) return true;
    if (bracket.includes('2.50') && gpa >= 2.50 && gpa < 3.00) return true;
    if (bracket.includes('2.00') && gpa >= 2.00 && gpa < 2.50) return true;
    if (bracket.includes('< 2.00') || bracket.includes('<2')) return gpa < 2.00;
    return false;
  };

  // Helper for clean, short mobile labels
  const getShortBracketLabel = (bracket: string): string => {
    if (bracket.includes('3.75')) return '≥3.75';
    if (bracket.includes('3.50')) return '3.50+';
    if (bracket.includes('3.00')) return '3.00+';
    if (bracket.includes('2.50')) return '2.50+';
    if (bracket.includes('2.00')) return '2.00+';
    if (bracket.includes('< 2.00') || bracket.includes('<2')) return '<2.0';
    return bracket.split('(')[0].trim();
  };

  return (
    <Card glass className="p-4 sm:p-6 border-slate-200 dark:border-slate-800 space-y-4 shadow-md">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 border-b border-slate-200 dark:border-slate-800 pb-3">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <BarChart3 className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0" />
            <h4 className="font-bold text-sm text-slate-900 dark:text-slate-100">{title}</h4>
            <Badge variant="emerald" size="sm" className="shrink-0">Credit-Weighted</Badge>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Frequency distribution of {metricLabel} across {totalStudents} verified students.
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs">
          <button
            type="button"
            onClick={() => setShowTableView(!showTableView)}
            className="flex items-center gap-1 text-slate-700 dark:text-slate-300 hover:text-slate-900 dark:hover:text-slate-100 transition-colors px-2.5 py-1 rounded-lg bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 font-medium"
          >
            <TableIcon className="w-3.5 h-3.5" />
            {showTableView ? 'Chart View' : 'Table View'}
          </button>
        </div>
      </div>

      {/* Statistical Reference Summary */}
      {(classMeanGPA !== undefined || classMedianGPA !== undefined || selectedStudentGPA !== undefined) && (
        <div className="flex flex-wrap items-center gap-2 sm:gap-4 text-xs font-mono bg-slate-50 dark:bg-slate-950/60 p-2.5 sm:p-3 rounded-xl border border-slate-200 dark:border-slate-800/80">
          {classMeanGPA !== undefined && (
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-sm bg-sky-500 shrink-0" />
              <span className="text-slate-500 dark:text-slate-400 font-sans">Mean:</span>
              <strong className="text-sky-600 dark:text-sky-400">{classMeanGPA.toFixed(2)}</strong>
            </div>
          )}

          {classMedianGPA !== undefined && (
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-sm bg-sky-500 dark:bg-sky-400 shrink-0" />
              <span className="text-slate-500 dark:text-slate-400 font-sans">Median:</span>
              <strong className="text-sky-600 dark:text-sky-400">{classMedianGPA.toFixed(2)}</strong>
            </div>
          )}

          {selectedStudentGPA !== undefined && (
            <div className="flex items-center gap-1.5 sm:ml-auto">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 ring-2 ring-emerald-500/30 shrink-0" />
              <span className="text-slate-700 dark:text-slate-300 font-sans font-bold">You:</span>
              <strong className="text-emerald-600 dark:text-emerald-400 font-bold">{selectedStudentGPA.toFixed(2)} GPA</strong>
            </div>
          )}
        </div>
      )}

      {/* Accessible Table Alternative */}
      {showTableView ? (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-slate-50 dark:bg-slate-950 text-slate-600 dark:text-slate-400 border-b border-slate-200 dark:border-slate-800">
              <tr>
                <th className="p-2.5">Score Bracket</th>
                <th className="p-2.5 text-center">Student Count</th>
                <th className="p-2.5 text-center">Cohort Percentage</th>
                <th className="p-2.5 text-center">Selected Student</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60 text-slate-700 dark:text-slate-300">
              {distribution.map((item) => {
                const inBracket = isStudentInBracket(item.bracket, selectedStudentGPA);
                return (
                  <tr key={item.bracket} className={inBracket ? 'bg-emerald-500/10' : ''}>
                    <td className="p-2.5 font-bold">{item.bracket}</td>
                    <td className="p-2.5 text-center">{item.count}</td>
                    <td className="p-2.5 text-center">{item.percentage.toFixed(1)}%</td>
                    <td className="p-2.5 text-center font-sans">
                      {inBracket ? <Badge variant="emerald" size="sm">Your Position</Badge> : '—'}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : (
        /* Visual Responsive Column / Histogram Chart */
        <div className="pt-4 pb-2 space-y-4">
          <div className="flex items-end gap-1.5 sm:gap-3 h-52 pt-6 px-1 sm:px-2 relative border-b border-slate-200 dark:border-slate-800">
            {distribution.map((item) => {
              const heightPct = Math.round((item.count / maxCount) * 100);
              const inBracket = isStudentInBracket(item.bracket, selectedStudentGPA);

              return (
                <div
                  key={item.bracket}
                  className="flex-1 flex flex-col items-center h-full justify-end group relative cursor-pointer min-w-0"
                  onMouseEnter={() => setHoveredBracket(item)}
                  onMouseLeave={() => setHoveredBracket(null)}
                >
                  {/* Selected Student Marker */}
                  {inBracket && (
                    <div className="absolute -top-6 text-[9px] sm:text-[10px] font-bold font-mono px-1.5 sm:px-2 py-0.5 rounded-full bg-emerald-500 text-white shadow-md whitespace-nowrap">
                      You
                    </div>
                  )}

                  {/* Count label above bar */}
                  {item.count > 0 && (
                    <div className="text-[9px] sm:text-[10px] font-mono font-bold text-slate-700 dark:text-slate-300 mb-0.5">
                      {item.count}
                    </div>
                  )}

                  {/* Histogram Bar */}
                  <div
                    className={`w-full max-w-[48px] rounded-t-lg transition-all duration-300 ${
                      inBracket
                        ? 'bg-gradient-to-t from-emerald-600 to-emerald-400 ring-2 ring-emerald-400 shadow-md shadow-emerald-500/20'
                        : 'bg-slate-200 dark:bg-slate-800 hover:bg-slate-300 dark:hover:bg-slate-700'
                    }`}
                    style={{ height: `${Math.max(heightPct, 6)}%` }}
                  />

                  {/* X-axis Label */}
                  <div className="mt-1.5 text-center w-full overflow-hidden">
                    <span className={`text-[9px] sm:text-[10px] font-mono block leading-tight truncate ${inBracket ? 'text-emerald-600 dark:text-emerald-400 font-bold' : 'text-slate-600 dark:text-slate-400'}`}>
                      {/* Short clean bracket on mobile, full on sm+ */}
                      <span className="sm:hidden">{getShortBracketLabel(item.bracket)}</span>
                      <span className="hidden sm:block truncate">{item.bracket.split('(')[0].trim()}</span>
                    </span>
                    <span className="text-[8px] sm:text-[10px] text-slate-400 dark:text-slate-500 font-mono">
                      {item.percentage.toFixed(0)}%
                    </span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Hover Tooltip Details */}
          {hoveredBracket && (
            <div className="p-2.5 sm:p-3 bg-slate-50 dark:bg-slate-950 rounded-xl border border-slate-200 dark:border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-1 text-xs font-mono animate-in fade-in duration-100">
              <span className="text-slate-700 dark:text-slate-300">
                Bracket <strong className="text-slate-900 dark:text-slate-100">{hoveredBracket.bracket}</strong>:
              </span>
              <span className="text-emerald-600 dark:text-emerald-400 font-bold">
                {hoveredBracket.count} {hoveredBracket.count === 1 ? 'student' : 'students'} ({hoveredBracket.percentage.toFixed(1)}% of class)
              </span>
            </div>
          )}
        </div>
      )}
    </Card>
  );
};
