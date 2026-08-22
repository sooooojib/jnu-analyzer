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
  const [showTableView, setShowTableView] = useState(false);

  const maxCount = Math.max(...distribution.map((d) => d.count), 1);

  // Helper to determine if the selected student falls into this bracket
  const isStudentInBracket = (bracket: string, gpa?: number): boolean => {
    if (gpa === undefined || gpa === null) return false;
    const b = bracket.toUpperCase().trim();
    if (b.startsWith('A+') || (b.includes('4.00') && !b.includes('3.75'))) return gpa >= 4.00;
    if (b.startsWith('A ') || b.startsWith('A(') || b.startsWith('A (')) return gpa >= 3.75 && gpa < 4.00;
    if (b.startsWith('A-') || (b.includes('3.50') && !b.includes('3.25'))) return gpa >= 3.50 && gpa < 3.75;
    if (b.startsWith('B+') || (b.includes('3.25') && !b.includes('3.00'))) return gpa >= 3.25 && gpa < 3.50;
    if (b.startsWith('B ') || b.startsWith('B(') || b.startsWith('B (')) return gpa >= 3.00 && gpa < 3.25;
    if (b.startsWith('B-') || (b.includes('2.75') && !b.includes('2.50'))) return gpa >= 2.75 && gpa < 3.00;
    if (b.startsWith('C+') || (b.includes('2.50') && !b.includes('2.25'))) return gpa >= 2.50 && gpa < 2.75;
    if (b.startsWith('C ') || b.startsWith('C(') || b.startsWith('C (')) return gpa >= 2.25 && gpa < 2.50;
    if (b.startsWith('D') || (b.includes('2.00') && !b.includes('<'))) return gpa >= 2.00 && gpa < 2.25;
    if (b.startsWith('F') || b.includes('< 2.00') || b.includes('<2')) return gpa < 2.00;

    // Fallback if bracket label is legacy interval (e.g. 3.75 - 4.00)
    if (b.includes('3.75') && gpa >= 3.75) return true;
    if (b.includes('3.50') && gpa >= 3.50 && gpa < 3.75) return true;
    if (b.includes('3.00') && gpa >= 3.00 && gpa < 3.50) return true;
    if (b.includes('2.50') && gpa >= 2.50 && gpa < 3.00) return true;
    if (b.includes('2.00') && gpa >= 2.00 && gpa < 2.50) return true;
    if (b.includes('< 2.00') || b.includes('<2')) return gpa < 2.00;
    return false;
  };

  // Extract clean Letter Grade and Range
  const formatGradeLabel = (bracket: string): { grade: string; range: string } => {
    const parts = bracket.split('(');
    let grade = parts[0].trim();
    let range = parts[1] ? parts[1].replace(')', '').trim() : '';

    // If legacy numeric bracket, assign letter grade
    if (!parts[1] && (grade.includes('3.75') || grade.includes('4.00'))) {
      grade = 'A+ / A';
      range = '3.75–4.00';
    } else if (!parts[1] && grade.includes('3.50')) {
      grade = 'A-';
      range = '3.50–3.74';
    } else if (!parts[1] && grade.includes('3.00')) {
      grade = 'B / B+';
      range = '3.00–3.49';
    } else if (!parts[1] && grade.includes('2.50')) {
      grade = 'B- / C+';
      range = '2.50–2.99';
    } else if (!parts[1] && grade.includes('2.00')) {
      grade = 'C / D';
      range = '2.00–2.49';
    } else if (!parts[1] && (grade.includes('<') || grade.includes('F'))) {
      grade = 'F';
      range = '<2.00';
    }

    return { grade, range };
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
                <th className="p-2.5">Grade / Score Bracket</th>
                <th className="p-2.5 text-center">Student Count</th>
                <th className="p-2.5 text-center">Cohort Percentage</th>
                <th className="p-2.5 text-center">Selected Student</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60 text-slate-700 dark:text-slate-300">
              {distribution.map((item) => {
                const inBracket = isStudentInBracket(item.bracket, selectedStudentGPA);
                return (
                  <tr key={item.bracket} className={inBracket ? 'bg-emerald-500/10 dark:bg-emerald-500/15' : ''}>
                    <td className="p-2.5 font-bold">{item.bracket}</td>
                    <td className="p-2.5 text-center font-bold text-slate-900 dark:text-slate-100">{item.count}</td>
                    <td className="p-2.5 text-center text-emerald-600 dark:text-emerald-400 font-bold">{item.percentage.toFixed(1)}%</td>
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
        <div className="pt-6 pb-2">
          <div className="flex items-end gap-1 sm:gap-2.5 h-56 pt-8 px-1 sm:px-2 relative border-b border-slate-200 dark:border-slate-800">
            {distribution.map((item) => {
              const heightPct = Math.round((item.count / maxCount) * 100);
              const inBracket = isStudentInBracket(item.bracket, selectedStudentGPA);
              const { grade, range } = formatGradeLabel(item.bracket);

              return (
                <div
                  key={item.bracket}
                  className="flex-1 flex flex-col items-center h-full justify-end relative min-w-0"
                >
                  {/* Selected Student Floating Marker */}
                  {inBracket && (
                    <div className="absolute -top-7 text-[9px] sm:text-[10px] font-black font-mono px-2 py-0.5 rounded-full bg-emerald-500 text-slate-950 shadow-md ring-2 ring-emerald-400/50 whitespace-nowrap z-10 animate-bounce">
                      You
                    </div>
                  )}

                  {/* Count label directly above bar */}
                  <div className={`text-[10px] sm:text-xs font-mono font-bold mb-1 ${inBracket ? 'text-emerald-600 dark:text-emerald-400 font-black' : 'text-slate-600 dark:text-slate-300'}`}>
                    {item.count}
                  </div>

                  {/* Histogram Bar */}
                  <div
                    className={`w-full max-w-[48px] rounded-t-lg transition-all duration-300 ${
                      inBracket
                        ? 'bg-gradient-to-t from-emerald-600 to-emerald-400 ring-2 ring-emerald-400 shadow-lg shadow-emerald-500/25'
                        : item.count > 0
                        ? 'bg-slate-200 dark:bg-slate-800/90 hover:bg-slate-300 dark:hover:bg-slate-700/90'
                        : 'bg-slate-100 dark:bg-slate-800/30'
                    }`}
                    style={{ height: `${Math.max(heightPct, 6)}%` }}
                  />

                  {/* X-axis Label: Grade + Range + Percentage */}
                  <div className="mt-2 text-center w-full px-0.5">
                    <div className={`text-[11px] sm:text-xs font-black font-mono tracking-tight leading-tight ${inBracket ? 'text-emerald-600 dark:text-emerald-400' : 'text-slate-800 dark:text-slate-200'}`}>
                      {grade}
                    </div>
                    {range && (
                      <div className="text-[9px] text-slate-400 dark:text-slate-500 font-mono hidden md:block leading-tight mt-0.5">
                        {range}
                      </div>
                    )}
                    <div className={`text-[10px] sm:text-[11px] font-bold font-mono mt-0.5 ${inBracket ? 'text-emerald-600 dark:text-emerald-400' : 'text-slate-500 dark:text-slate-400'}`}>
                      {item.percentage.toFixed(0)}%
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </Card>
  );
};
