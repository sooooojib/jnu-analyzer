import React, { useState, useMemo, useRef } from 'react';
import { Card } from '../common/Card';
import { Badge } from '../common/Badge';
import { MetricDistributionItem } from '../../types/analytics';
import { 
  BarChart3, 
  Table as TableIcon, 
  Users, 
  X
} from 'lucide-react';

interface GPADistributionChartProps {
  distribution: MetricDistributionItem[];
  selectedStudentGPA?: number;
  selectedStudentId?: string;
  classMeanGPA?: number;
  classMedianGPA?: number;
  totalStudents?: number;
  title?: string;
  metricLabel?: string;
}

export const GPADistributionChart: React.FC<GPADistributionChartProps> = ({
  distribution = [],
  selectedStudentGPA,
  selectedStudentId,
  classMeanGPA,
  classMedianGPA,
  totalStudents = 0,
  title = 'Class GPA Distribution (Current Semester)',
  metricLabel = 'Current-Semester GPA',
}) => {
  const [showTableView, setShowTableView] = useState(false);
  const [hoveredBracket, setHoveredBracket] = useState<string | null>(null);
  const [selectedBracket, setSelectedBracket] = useState<string | null>(null);
  const rosterRef = useRef<HTMLDivElement | null>(null);

  // Determine which bracket is currently clicked/pinned for full roster inspection below
  const selectedBracketData = useMemo(() => {
    if (!selectedBracket) return null;
    return distribution.find((d) => d.bracket === selectedBracket) || null;
  }, [selectedBracket, distribution]);

  // Scroll to roster on mobile tap/click
  const handleBarClick = (bracket: string) => {
    if (selectedBracket === bracket) {
      setSelectedBracket(null);
    } else {
      setSelectedBracket(bracket);
      // Smooth scroll into view on small screens
      setTimeout(() => {
        if (rosterRef.current) {
          rosterRef.current.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
      }, 100);
    }
  };

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

  // Determine max count for proportional heights
  const maxCount = Math.max(...distribution.map((d) => d.count), 1);

  // Students for the active roster (pinned by click)
  const rosterStudents = selectedBracketData?.students || [];

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
            Frequency distribution of {metricLabel} across {totalStudents} verified students. Hover or click any bar to inspect student IDs and names.
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs">
          <button
            type="button"
            onClick={() => setShowTableView(!showTableView)}
            className="flex items-center gap-1 text-slate-700 dark:text-slate-300 hover:text-slate-900 dark:hover:text-slate-100 transition-colors px-2.5 py-1 rounded-lg bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 font-medium shadow-sm"
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
                <th className="p-2.5 text-right">Inspect Roster</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60 text-slate-700 dark:text-slate-300">
              {distribution.map((item) => {
                const inBracket = isStudentInBracket(item.bracket, selectedStudentGPA);
                const isSelected = selectedBracket === item.bracket;
                return (
                  <tr 
                    key={item.bracket} 
                    onClick={() => handleBarClick(item.bracket)}
                    className={`cursor-pointer transition-colors ${
                      isSelected 
                        ? 'bg-sky-500/10 dark:bg-sky-500/15' 
                        : inBracket 
                        ? 'bg-emerald-500/10 dark:bg-emerald-500/15' 
                        : 'hover:bg-slate-50 dark:hover:bg-slate-800/40'
                    }`}
                  >
                    <td className="p-2.5 font-bold">{item.bracket}</td>
                    <td className="p-2.5 text-center font-bold text-slate-900 dark:text-slate-100">{item.count}</td>
                    <td className="p-2.5 text-center text-emerald-600 dark:text-emerald-400 font-bold">{item.percentage.toFixed(1)}%</td>
                    <td className="p-2.5 text-center font-sans">
                      {inBracket ? <Badge variant="emerald" size="sm">Your Position</Badge> : '—'}
                    </td>
                    <td className="p-2.5 text-right">
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleBarClick(item.bracket);
                        }}
                        className={`text-[11px] font-sans font-medium px-2 py-0.5 rounded transition-colors ${
                          isSelected
                            ? 'bg-emerald-600 text-white'
                            : 'text-sky-600 dark:text-sky-400 hover:underline'
                        }`}
                      >
                        {isSelected ? 'Viewing' : `View ${item.count}`}
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : (
        /* Visual Responsive Column / Histogram Chart */
        <div className="pt-4 pb-2">
          <div className="flex items-end gap-1 sm:gap-2.5 h-60 pt-10 px-1 sm:px-2 relative border-b border-slate-200 dark:border-slate-800">
            {distribution.map((item) => {
              const heightPct = Math.round((item.count / maxCount) * 100);
              const inBracket = isStudentInBracket(item.bracket, selectedStudentGPA);
              const isHovered = hoveredBracket === item.bracket;
              const isSelected = selectedBracket === item.bracket;
              const { grade, range } = formatGradeLabel(item.bracket);

              return (
                <div
                  key={item.bracket}
                  tabIndex={0}
                  role="button"
                  onPointerEnter={(e) => {
                    if (e.pointerType !== 'touch') {
                      setHoveredBracket(item.bracket);
                    }
                  }}
                  onPointerLeave={() => setHoveredBracket(null)}
                  onTouchStart={() => setHoveredBracket(null)}
                  onClick={() => handleBarClick(item.bracket)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      handleBarClick(item.bracket);
                    }
                  }}
                  className="flex-1 flex flex-col items-center h-full justify-end relative min-w-0 cursor-pointer group touch-manipulation focus:outline-none"
                >
                  {/* Floating Micro-Tooltip on Desktop Hover (Desktop only, hidden on touch screens) */}
                  {isHovered && item.students && item.students.length > 0 && (
                    <div className="hidden md:block absolute -top-24 sm:-top-28 left-1/2 -translate-x-1/2 z-30 pointer-events-none animate-in fade-in zoom-in-95 duration-150">
                      <div className="bg-slate-900 text-slate-100 dark:bg-black/95 dark:text-slate-100 p-2.5 rounded-xl shadow-2xl border border-slate-700/80 dark:border-slate-800 text-[11px] font-sans whitespace-nowrap min-w-[160px] max-w-[240px]">
                        <div className="flex items-center justify-between gap-2 border-b border-slate-700 pb-1.5 mb-1.5 font-bold">
                          <span className="text-emerald-400 font-mono">{grade}</span>
                          <span className="text-slate-300 font-mono text-[10px]">{item.count} {item.count === 1 ? 'student' : 'students'}</span>
                        </div>
                        <div className="space-y-1 max-h-24 overflow-hidden text-[10px]">
                          {item.students.slice(0, 3).map((st) => (
                            <div key={st.student_id} className="flex items-center justify-between gap-2">
                              <span className="font-mono text-sky-400 font-bold truncate">{st.student_id}</span>
                              <span className="truncate text-slate-300 max-w-[100px]">{st.student_name}</span>
                            </div>
                          ))}
                          {item.students.length > 3 && (
                            <div className="text-[9px] text-amber-400 text-center pt-0.5 font-mono">
                              +{item.students.length - 3} more (click to view all)
                            </div>
                          )}
                        </div>
                      </div>
                      <div className="w-2.5 h-2.5 bg-slate-900 dark:bg-black/95 border-r border-b border-slate-700/80 dark:border-slate-800 rotate-45 mx-auto -mt-1.5" />
                    </div>
                  )}

                  {/* Selected Student Floating Marker */}
                  {inBracket && (
                    <div className="absolute -top-7 text-[9px] sm:text-[10px] font-black font-mono px-2 py-0.5 rounded-full bg-emerald-500 text-slate-950 shadow-md ring-2 ring-emerald-400/50 whitespace-nowrap z-10 animate-bounce">
                      You
                    </div>
                  )}

                  {/* Count label directly above bar */}
                  <div className={`text-[10px] sm:text-xs font-mono font-bold mb-1 transition-colors ${
                    isSelected
                      ? 'text-sky-600 dark:text-sky-400 scale-110 font-black'
                      : inBracket
                      ? 'text-emerald-600 dark:text-emerald-400 font-black'
                      : isHovered
                      ? 'text-slate-900 dark:text-slate-100 font-bold'
                      : 'text-slate-600 dark:text-slate-300'
                  }`}>
                    {item.count}
                  </div>

                  {/* Histogram Bar with Animated Elevation */}
                  <div
                    className={`w-full max-w-[48px] rounded-t-lg transition-all duration-200 ${
                      isSelected
                        ? 'bg-gradient-to-t from-sky-600 to-sky-400 ring-2 ring-sky-400 shadow-xl shadow-sky-500/30 scale-x-105'
                        : inBracket
                        ? 'bg-gradient-to-t from-emerald-600 to-emerald-400 ring-2 ring-emerald-400 shadow-lg shadow-emerald-500/25 group-hover:scale-x-105'
                        : isHovered
                        ? 'bg-slate-400 dark:bg-slate-600 ring-2 ring-slate-300 dark:ring-slate-600 scale-x-105 shadow-md'
                        : item.count > 0
                        ? 'bg-slate-200 dark:bg-slate-800/90 group-hover:bg-slate-300 dark:group-hover:bg-slate-700/90'
                        : 'bg-slate-100 dark:bg-slate-800/30'
                    }`}
                    style={{ height: `${Math.max(heightPct, 6)}%` }}
                  />

                  {/* X-axis Label: Grade + Range + Percentage */}
                  <div className="mt-2 text-center w-full px-0.5">
                    <div className={`text-[11px] sm:text-xs font-black font-mono tracking-tight leading-tight transition-colors ${
                      isSelected
                        ? 'text-sky-600 dark:text-sky-400'
                        : inBracket
                        ? 'text-emerald-600 dark:text-emerald-400'
                        : 'text-slate-800 dark:text-slate-200'
                    }`}>
                      {grade}
                    </div>
                    {range && (
                      <div className="text-[9px] text-slate-400 dark:text-slate-500 font-mono hidden md:block leading-tight mt-0.5">
                        {range}
                      </div>
                    )}
                    <div className={`text-[10px] sm:text-[11px] font-bold font-mono mt-0.5 ${
                      isSelected
                        ? 'text-sky-600 dark:text-sky-400 font-black'
                        : inBracket
                        ? 'text-emerald-600 dark:text-emerald-400'
                        : 'text-slate-500 dark:text-slate-400'
                    }`}>
                      {item.percentage.toFixed(0)}%
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Interactive Grade Bracket Student Roster Drawer (Pinned by Click/Touch) */}
      {selectedBracketData && (
        <div 
          ref={rosterRef}
          className="mt-4 p-4 sm:p-5 rounded-2xl bg-slate-50 dark:bg-slate-900/90 border border-slate-200 dark:border-slate-800 shadow-lg space-y-3.5 animate-in fade-in slide-in-from-top-2 duration-200"
        >
          {/* Drawer Header */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 border-b border-slate-200 dark:border-slate-800 pb-3">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-xl bg-emerald-500/10 dark:bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 flex items-center justify-center font-black font-mono text-xs shrink-0">
                <Users className="w-4 h-4" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h5 className="font-bold text-sm text-slate-900 dark:text-slate-100">
                    {selectedBracketData.bracket} Grade Bracket
                  </h5>
                  <Badge variant="emerald" size="sm">
                    {selectedBracketData.count} {selectedBracketData.count === 1 ? 'Student' : 'Students'} ({selectedBracketData.percentage.toFixed(1)}%)
                  </Badge>
                </div>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Students positioned within this grade point threshold.
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2 self-end sm:self-auto">
              <button
                type="button"
                onClick={() => setSelectedBracket(null)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-200/50 dark:hover:bg-white/5 transition-colors"
                title="Close Roster View"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Student Grid Cards */}
          {rosterStudents.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2.5 max-h-64 overflow-y-auto pr-1 custom-scrollbar">
              {rosterStudents.map((st, idx) => {
                const isCurrentStudent = selectedStudentId && st.student_id === selectedStudentId;
                return (
                  <div
                    key={st.student_id}
                    className={`p-3 rounded-xl border transition-all flex items-center justify-between gap-2 shadow-sm ${
                      isCurrentStudent
                        ? 'bg-emerald-500/10 dark:bg-emerald-500/15 border-emerald-500/40 ring-1 ring-emerald-500/30'
                        : 'bg-white dark:bg-slate-950/70 border-slate-200 dark:border-slate-800/80 hover:border-slate-300 dark:hover:border-slate-700'
                    }`}
                  >
                    <div className="flex items-center gap-2.5 min-w-0">
                      <div className="w-7 h-7 rounded-lg bg-slate-100 dark:bg-slate-800/80 text-slate-600 dark:text-slate-400 flex items-center justify-center text-[10px] font-bold shrink-0">
                        {idx + 1}
                      </div>
                      <div className="min-w-0">
                        <div className="font-mono text-xs font-bold text-sky-600 dark:text-sky-400 flex items-center gap-1.5">
                          <span>{st.student_id}</span>
                          {isCurrentStudent && (
                            <Badge variant="emerald" size="sm" className="text-[9px] px-1.5 py-0">You</Badge>
                          )}
                        </div>
                        <div className="text-xs font-medium text-slate-800 dark:text-slate-200 truncate" title={st.student_name}>
                          {st.student_name}
                        </div>
                      </div>
                    </div>

                    <div className="text-right shrink-0">
                      <span className="font-mono font-black text-xs text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-md">
                        {st.gpa.toFixed(2)}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="p-6 text-center text-xs text-slate-500 dark:text-slate-400 font-mono bg-white dark:bg-slate-950/40 rounded-xl border border-slate-200 dark:border-slate-800/60">
              {selectedBracketData.count === 0 
                ? 'No students enrolled in this grade bracket.' 
                : 'No student records available for this bracket.'}
            </div>
          )}
        </div>
      )}
    </Card>
  );
};
