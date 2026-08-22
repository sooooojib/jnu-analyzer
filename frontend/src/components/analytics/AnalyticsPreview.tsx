import React, { useState, useEffect, useMemo } from 'react';
import { Card } from '../common/Card';
import { Badge } from '../common/Badge';
import { Button } from '../common/Button';
import { Alert } from '../common/Alert';
import { api } from '../../api/endpoints';
import { CohortAnalytics, SubjectAnalysisItem } from '../../types/analytics';
import { 
  BarChart3, 
  TrendingUp, 
  Users, 
  Award, 
  BookOpen, 
  Trophy, 
  Layers, 
  Hash,
  ArrowUpRight,
  ArrowDownRight,
  Info,
  Download
} from 'lucide-react';

interface AnalyticsPreviewProps {
  sessionId?: string;
  initialStudentId?: string;
  initialView?: 'class' | 'cumulative' | 'subjects' | 'leaderboard';
}

export const AnalyticsPreview: React.FC<AnalyticsPreviewProps> = ({
  sessionId,
  initialView = 'subjects',
}) => {
  const [analytics, setAnalytics] = useState<CohortAnalytics | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [exportMessage, setExportMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [activeAnalysisView, setActiveAnalysisView] = useState<'class' | 'cumulative' | 'subjects' | 'leaderboard'>(initialView);
  const [rankingSortMode, setRankingSortMode] = useState<'semester' | 'cumulative'>('semester');

  // Selected Course State
  const [selectedCourseCode, setSelectedCourseCode] = useState<string | null>(null);

  // Sync with initialView prop when it changes
  useEffect(() => {
    if (initialView) {
      setActiveAnalysisView(initialView);
    }
  }, [initialView]);

  const fetchAnalytics = () => {
    if (sessionId) {
      setIsLoading(true);
      setErrorMessage(null);
      api.getCohortAnalytics(sessionId)
        .then((data) => {
          setAnalytics(data);
          if (data.subject_analysis && data.subject_analysis.length > 0 && !selectedCourseCode) {
            setSelectedCourseCode(data.subject_analysis[0].course_code);
          }
        })
        .catch((err) => {
          setErrorMessage(err.message || 'Failed to retrieve cohort analytics.');
        })
        .finally(() => setIsLoading(false));
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, [sessionId]);

  const classData = analytics?.class_analysis || {
    total_students: analytics?.summary_metrics?.count || 0,
    students_with_gpa_count: analytics?.summary_metrics?.count || 0,
    average_gpa: analytics?.summary_metrics?.mean || 0.0,
    median_gpa: analytics?.summary_metrics?.median || 0.0,
    mode_gpa: analytics?.summary_metrics?.mode || 0.0,
    highest_gpa: analytics?.summary_metrics?.max || 0.0,
    lowest_gpa: analytics?.summary_metrics?.min || 0.0,
    std_dev_gpa: analytics?.summary_metrics?.std_dev || 0.0,
    distribution: analytics?.gpa_distribution_histogram || [],
  };

  const cumulativeData = analytics?.cumulative_analysis || {
    total_students: classData.total_students,
    students_with_cgpa_count: classData.total_students,
    average_cgpa: 0.0,
    median_cgpa: 0.0,
    mode_cgpa: 0.0,
    highest_cgpa: 0.0,
    lowest_cgpa: 0.0,
    std_dev_cgpa: 0.0,
    distribution: [],
  };

  const subjects: SubjectAnalysisItem[] = analytics?.subject_analysis || [];
  const leaderboard = analytics?.student_leaderboard || [];

  // Active Subject
  const activeSubject = useMemo(() => {
    if (!subjects.length) return null;
    if (selectedCourseCode) {
      const match = subjects.find((s) => s.course_code === selectedCourseCode);
      if (match) return match;
    }
    return subjects[0];
  }, [subjects, selectedCourseCode]);

  const handleExportClassPdf = async () => {
    if (!sessionId) return;
    setIsExporting(true);
    setExportMessage(null);
    try {
      const blob = await api.exportClassPdf(sessionId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'JNU_Class_Analysis.pdf';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      setExportMessage('Class analysis exported successfully.');
      setTimeout(() => setExportMessage(null), 4000);
    } catch (err: any) {
      console.error('Class export failed', err);
      setExportMessage('Failed to export class analysis. Please try again.');
    } finally {
      setIsExporting(false);
    }
  };

  if (isLoading && !analytics) {
    return (
      <Card glass className="p-12 text-center space-y-4">
        <div className="w-12 h-12 border-3 border-emerald-500/30 border-t-emerald-500 rounded-full animate-spin mx-auto" />
        <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100">Computing Deterministic Analytics...</h3>
        <p className="text-sm text-slate-600 dark:text-slate-400">Calculating Mean, Median, Mode, and Subject rankings across verified dataset.</p>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {errorMessage && (
        <Alert
          type="error"
          title="Analytics Notice"
          message={errorMessage}
          onClose={() => setErrorMessage(null)}
        />
      )}

      {/* Export Feedback Banner */}
      {exportMessage && (
        <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-xl text-xs font-medium text-emerald-600 dark:text-emerald-400 flex items-center justify-between animate-in fade-in">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span>{exportMessage}</span>
          </div>
          <button type="button" onClick={() => setExportMessage(null)} className="text-emerald-500 hover:text-emerald-700 font-bold ml-2">✕</button>
        </div>
      )}

      {/* Header & Export Action */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 bg-white dark:bg-slate-900/90 border border-slate-200 dark:border-slate-800 p-3.5 sm:p-4 rounded-2xl shadow-sm">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-600 dark:text-emerald-400 shrink-0">
            <BarChart3 className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-sm sm:text-base font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
              <span>Class Cohort Analytics</span>
              <Badge variant="emerald" size="sm" className="font-mono">{classData.total_students} Students</Badge>
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              {subjects.length} Courses • Class Average GPA: {classData.average_gpa.toFixed(2)}
            </p>
          </div>
        </div>

        <Button
          variant="secondary"
          size="sm"
          onClick={handleExportClassPdf}
          isLoading={isExporting}
          leftIcon={<Download className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />}
          className="w-full sm:w-auto font-medium border-slate-200 dark:border-slate-700/80 hover:border-emerald-500/40 shrink-0"
        >
          {isExporting ? 'Generating class analysis...' : 'Export Class Analysis'}
        </Button>
      </div>

      {/* Nomenclature Guide Banner */}
      <Card glass className="p-4 border-slate-800 flex flex-col md:flex-row items-start md:items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-2">
          <Info className="w-4 h-4 text-emerald-400 flex-shrink-0" />
          <span className="text-slate-300">
            <strong className="text-slate-100">Deterministic Metrics Rule:</strong> Analytics use exclusively verified marks from this uploaded result sheet.
          </span>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="emerald" size="sm">GP: Single Course</Badge>
          <Badge variant="emerald" size="sm">GPA: Current Semester</Badge>
          <Badge variant="blue" size="sm">CGPA: Cumulative (From Sheet)</Badge>
        </div>
      </Card>

      {/* Top Navigation Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-200 dark:border-slate-800/80 pt-2 pb-3 px-1 overflow-x-auto scrollbar-none text-xs">
        <button
          onClick={() => setActiveAnalysisView('subjects')}
          className={`px-3 py-1.5 rounded-lg font-semibold transition-all flex items-center gap-1.5 shrink-0 whitespace-nowrap ${
            activeAnalysisView === 'subjects'
              ? 'bg-emerald-600 text-white dark:bg-emerald-500/20 dark:text-emerald-300 dark:border dark:border-emerald-500/30 shadow-sm'
              : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800/50'
          }`}
        >
          <BookOpen className="w-3.5 h-3.5" />
          1. Subject-wise Analysis ({subjects.length} Courses)
        </button>

        <button
          onClick={() => setActiveAnalysisView('class')}
          className={`px-3 py-1.5 rounded-lg font-semibold transition-all flex items-center gap-1.5 shrink-0 whitespace-nowrap ${
            activeAnalysisView === 'class'
              ? 'bg-emerald-600 text-white dark:bg-emerald-500/20 dark:text-emerald-300 dark:border dark:border-emerald-500/30 shadow-sm'
              : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800/50'
          }`}
        >
          <BarChart3 className="w-3.5 h-3.5" />
          2. Class Semester Analysis (GPA)
        </button>

        <button
          onClick={() => setActiveAnalysisView('cumulative')}
          className={`px-3 py-1.5 rounded-lg font-semibold transition-all flex items-center gap-1.5 shrink-0 whitespace-nowrap ${
            activeAnalysisView === 'cumulative'
              ? 'bg-emerald-600 text-white dark:bg-emerald-500/20 dark:text-emerald-300 dark:border dark:border-emerald-500/30 shadow-sm'
              : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800/50'
          }`}
        >
          <Layers className="w-3.5 h-3.5" />
          3. Cumulative Analysis (CGPA)
        </button>

        <button
          onClick={() => setActiveAnalysisView('leaderboard')}
          className={`px-3 py-1.5 rounded-lg font-semibold transition-all flex items-center gap-1.5 shrink-0 whitespace-nowrap ${
            activeAnalysisView === 'leaderboard'
              ? 'bg-emerald-600 text-white dark:bg-emerald-500/20 dark:text-emerald-300 dark:border dark:border-emerald-500/30 shadow-sm'
              : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800/50'
          }`}
        >
          <Trophy className="w-3.5 h-3.5" />
          4. Class Standings & Leaderboard
        </button>
      </div>

      {/* SECTION 1: DETAILED SUBJECT-WISE ANALYSIS */}
      {activeAnalysisView === 'subjects' && (
        <div className="space-y-6 animate-in fade-in duration-200">
          {/* Subject Selector Dropdown */}
          <div className="bg-white dark:bg-slate-900/80 p-3.5 sm:p-4 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 sm:gap-3 w-full">
              <span className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider flex items-center gap-1.5 flex-shrink-0">
                <BookOpen className="w-4 h-4 text-amber-500 dark:text-amber-400 shrink-0" />
                Select Course:
              </span>
              <select
                value={selectedCourseCode || ''}
                onChange={(e) => setSelectedCourseCode(e.target.value)}
                className="w-full sm:flex-1 bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 text-xs font-mono font-bold py-2.5 px-3 rounded-xl border border-slate-200 dark:border-slate-700 hover:border-amber-500/60 focus:border-amber-500 focus:outline-none transition-all cursor-pointer shadow-inner"
              >
                {subjects.map((subj) => (
                  <option key={subj.course_code} value={subj.course_code} className="bg-white dark:bg-slate-950 text-slate-900 dark:text-slate-100 py-1.5">
                    {subj.course_code}{subj.course_title ? ` — ${subj.course_title}` : ''}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Active Subject Detailed Analytics Panel */}
          {activeSubject && (
            <div className="space-y-6">
              {/* Main Course Header Card */}
              <Card glass className="p-5 sm:p-8 border-slate-200 dark:border-slate-800 relative overflow-hidden">
                <div className="absolute top-0 right-0 w-80 h-80 bg-amber-500/5 rounded-full blur-3xl pointer-events-none" />

                <div className="pb-6 border-b border-slate-200 dark:border-slate-800">
                  <div className="flex flex-wrap items-center gap-2 mb-2">
                    <span className="text-xs font-black font-mono px-2.5 py-1 rounded bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20">
                      {activeSubject.course_code}
                    </span>
                    <Badge variant="slate" size="sm">{activeSubject.credit_hours} Credits</Badge>
                    <Badge variant="blue" size="sm">{activeSubject.number_of_students} Enrolled</Badge>
                  </div>
                  <h2 className="text-lg sm:text-2xl font-extrabold text-slate-900 dark:text-slate-100 tracking-tight leading-snug break-words">
                    {activeSubject.course_title || activeSubject.course_code}
                  </h2>
                </div>

                {/* 5 GP Metric Dials */}
                <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 pt-6">
                  <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-950/60 border border-slate-200 dark:border-slate-800/80 text-center shadow-sm">
                    <span className="text-[10px] text-slate-500 dark:text-slate-400 uppercase font-semibold">Average GP</span>
                    <div className="text-xl font-black font-mono text-emerald-600 dark:text-emerald-400 mt-1">
                      {activeSubject.average_gp.toFixed(2)}
                    </div>
                    <span className="text-[10px] text-slate-400 dark:text-slate-500">Arithmetic Mean</span>
                  </div>

                  <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-950/60 border border-slate-200 dark:border-slate-800/80 text-center shadow-sm">
                    <span className="text-[10px] text-slate-500 dark:text-slate-400 uppercase font-semibold">Median GP</span>
                    <div className="text-xl font-black font-mono text-sky-600 dark:text-sky-400 mt-1">
                      {activeSubject.median_gp.toFixed(2)}
                    </div>
                    <span className="text-[10px] text-slate-400 dark:text-slate-500">50th Percentile</span>
                  </div>

                  <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-950/60 border border-slate-200 dark:border-slate-800/80 text-center shadow-sm">
                    <span className="text-[10px] text-slate-500 dark:text-slate-400 uppercase font-semibold">Mode GP</span>
                    <div className="text-xl font-black font-mono text-purple-600 dark:text-purple-400 mt-1">
                      {activeSubject.mode_gp.toFixed(2)}
                    </div>
                    <span className="text-[10px] text-slate-400 dark:text-slate-500">Most Frequent</span>
                  </div>

                  <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-950/60 border border-slate-200 dark:border-slate-800/80 text-center shadow-sm">
                    <span className="text-[10px] text-slate-500 dark:text-slate-400 uppercase font-semibold">Highest GP</span>
                    <div className="text-xl font-black font-mono text-amber-600 dark:text-amber-400 mt-1">
                      {activeSubject.highest_gp.toFixed(2)}
                    </div>
                    <span className="text-[10px] text-slate-400 dark:text-slate-500">Subject Peak</span>
                  </div>

                  <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-950/60 border border-slate-200 dark:border-slate-800/80 text-center shadow-sm col-span-2 sm:col-span-1">
                    <span className="text-[10px] text-slate-500 dark:text-slate-400 uppercase font-semibold">Lowest GP</span>
                    <div className="text-xl font-black font-mono text-rose-600 dark:text-rose-400 mt-1">
                      {activeSubject.lowest_gp.toFixed(2)}
                    </div>
                    <span className="text-[10px] text-slate-400 dark:text-slate-500">Minimum Score</span>
                  </div>
                </div>
              </Card>

              {/* 2-Column: Subject Topper Spotlight & Joint High Performers */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Card 1: Subject Topper Spotlight */}
                <Card glass className="p-4 sm:p-6 border-slate-800 space-y-4">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
                    <div className="flex items-center gap-2">
                      <Trophy className="w-4 h-4 text-amber-400 shrink-0" />
                      <h4 className="font-bold text-sm text-slate-100">
                        Subject Topper Spotlight
                      </h4>
                    </div>
                    <Badge variant="amber" size="sm" className="self-start sm:self-auto">
                      {activeSubject.highest_performing_students.length > 1
                        ? `1 of ${activeSubject.highest_performing_students.length} Joint Toppers`
                        : 'Top Scorer'}
                    </Badge>
                  </div>

                  {activeSubject.highest_performing_students.length > 0 ? (
                    (() => {
                      const topper = activeSubject.highest_performing_students[0];
                      return (
                        <div className="space-y-4">
                          <div className="p-4 bg-white dark:bg-slate-900/80 rounded-2xl border border-slate-200 dark:border-slate-800 flex items-center justify-between shadow-sm">
                            <div className="flex items-center gap-3">
                              <div className="w-10 h-10 rounded-xl bg-amber-500/10 dark:bg-amber-500/20 border border-amber-500/20 dark:border-amber-500/30 flex items-center justify-center text-amber-600 dark:text-amber-400">
                                <Award className="w-5 h-5" />
                              </div>
                              <div>
                                <div className="text-sm font-bold text-slate-900 dark:text-slate-100">{topper.student_name}</div>
                                <div className="text-xs text-amber-600 dark:text-amber-400 font-mono mt-0.5">{topper.student_id}</div>
                              </div>
                            </div>
                            <div className="text-right">
                              <div className="text-xl font-black font-mono text-emerald-600 dark:text-emerald-400">
                                {topper.gp.toFixed(2)} GP
                              </div>
                              <Badge variant="emerald" size="sm">{topper.letter_grade}</Badge>
                            </div>
                          </div>

                          <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-950/60 border border-slate-200 dark:border-slate-800/80 space-y-2 text-xs">
                            <div className="flex items-center justify-between">
                              <span className="text-slate-500 dark:text-slate-400">Lead Over Class Average:</span>
                              <span className="font-mono font-bold text-emerald-600 dark:text-emerald-400">
                                +{(activeSubject.highest_gp - activeSubject.average_gp).toFixed(2)} GP
                              </span>
                            </div>
                            <div className="flex items-center justify-between">
                              <span className="text-slate-500 dark:text-slate-400">Subject Percentile:</span>
                              <span className="font-mono font-bold text-sky-600 dark:text-sky-400">100.0% (Rank #1)</span>
                            </div>
                          </div>
                        </div>
                      );
                    })()
                  ) : (
                    <div className="text-xs text-slate-400 p-4 text-center">No student data recorded for this subject.</div>
                  )}
                </Card>

                {/* Card 2: Highest-Performing Students (Ties Handled) */}
                <Card glass className="p-6 border-slate-800 space-y-4">
                  <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                    <div className="flex items-center gap-2">
                      <Award className="w-4 h-4 text-amber-400" />
                      <h4 className="font-bold text-sm text-slate-900 dark:text-slate-100">
                        All Top Performers ({activeSubject.highest_gp.toFixed(2)} GP)
                      </h4>
                    </div>
                    <Badge variant="amber" size="sm">
                      {activeSubject.highest_performing_students.length} Total
                    </Badge>
                  </div>

                  <div className="space-y-2 max-h-56 overflow-y-auto pr-1 custom-scrollbar">
                    {activeSubject.highest_performing_students.map((topper, idx) => (
                      <div
                        key={topper.student_id}
                        className="flex items-center justify-between p-3 rounded-xl bg-slate-50 dark:bg-slate-950/60 border border-slate-200 dark:border-slate-800/80 text-xs font-mono shadow-sm"
                      >
                        <div className="flex items-center gap-2.5">
                          <span className="w-5 h-5 rounded-full bg-amber-500/20 text-amber-600 dark:text-amber-400 font-bold flex items-center justify-center text-[10px]">
                            {idx + 1}
                          </span>
                          <div>
                            <div className="font-bold text-slate-900 dark:text-slate-200">{topper.student_name}</div>
                            <div className="text-[11px] text-emerald-600 dark:text-emerald-400 font-mono">{topper.student_id}</div>
                          </div>
                        </div>

                        <div className="flex items-center gap-2">
                          <span className="text-slate-900 dark:text-slate-100 font-bold">{topper.gp.toFixed(2)} GP</span>
                          <Badge variant="emerald" size="sm">{topper.letter_grade}</Badge>
                        </div>
                      </div>
                    ))}
                  </div>
                </Card>
              </div>

              {/* Grade Distribution Bar Chart */}
              {activeSubject.grade_counts && Object.keys(activeSubject.grade_counts).length > 0 && (
                <Card glass className="p-6 border-slate-200 dark:border-slate-800">
                  <h4 className="font-bold text-sm text-slate-900 dark:text-slate-100 mb-4 flex items-center gap-2">
                    <BarChart3 className="w-4 h-4 text-amber-500 dark:text-amber-400" />
                    Letter Grade Breakdown for {activeSubject.course_code}
                  </h4>

                  <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-3">
                    {Object.entries(activeSubject.grade_counts)
                      .sort(([gradeA], [gradeB]) => {
                        const GRADE_ORDER_MAP: Record<string, number> = {
                          'A+': 1, 'A': 2, 'A-': 3,
                          'B+': 4, 'B': 5, 'B-': 6,
                          'C+': 7, 'C': 8, 'C-': 9,
                          'D+': 10, 'D': 11, 'D-': 12,
                          'F': 13, 'I': 14, 'W': 15,
                        };
                        const cleanA = gradeA.trim().toUpperCase();
                        const cleanB = gradeB.trim().toUpperCase();
                        const orderA = GRADE_ORDER_MAP[cleanA] ?? 99;
                        const orderB = GRADE_ORDER_MAP[cleanB] ?? 99;
                        if (orderA !== orderB) return orderA - orderB;
                        return cleanA.localeCompare(cleanB);
                      })
                      .map(([grade, count]) => {
                        const pct = Math.round((count / activeSubject.number_of_students) * 100);
                        const isF = grade.trim().toUpperCase() === 'F';
                        const isA = grade.trim().toUpperCase().startsWith('A');
                        const isB = grade.trim().toUpperCase().startsWith('B');
                        const isC = grade.trim().toUpperCase().startsWith('C');
                        const isD = grade.trim().toUpperCase().startsWith('D');
                        const badgeVariant = isA ? 'emerald' : isB ? 'blue' : isC ? 'purple' : isD ? 'amber' : isF ? 'rose' : 'slate';

                        return (
                          <div key={grade} className="p-3 bg-slate-50 dark:bg-slate-950/80 rounded-xl border border-slate-200 dark:border-slate-800 text-center shadow-sm">
                            <Badge variant={badgeVariant} size="sm" className="mb-1">{grade}</Badge>
                            <div className="text-lg font-black font-mono text-slate-900 dark:text-slate-100">{count}</div>
                            <span className="text-[10px] text-slate-500 dark:text-slate-400">{pct}% of class</span>
                          </div>
                        );
                      })}
                  </div>
                </Card>
              )}
            </div>
          )}
        </div>
      )}

      {/* SECTION 2: CLASS SEMESTER ANALYSIS */}
      {activeAnalysisView === 'class' && (
        <div className="space-y-6 animate-in fade-in duration-200">
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            <Card className="p-4 bg-white dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 shadow-sm">
              <div className="text-xs text-slate-500 dark:text-slate-400 mb-1 flex items-center gap-1.5">
                <Users className="w-3.5 h-3.5 text-slate-500 dark:text-slate-400" /> Total Students
              </div>
              <div className="text-2xl font-black font-mono text-slate-900 dark:text-slate-100">{classData.total_students}</div>
            </Card>

            <Card className="p-4 bg-white dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 shadow-sm">
              <div className="text-xs text-slate-500 dark:text-slate-400 mb-1 flex items-center gap-1.5">
                <TrendingUp className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" /> Average GPA
              </div>
              <div className="text-2xl font-black font-mono text-emerald-600 dark:text-emerald-400">{classData.average_gpa.toFixed(2)}</div>
            </Card>

            <Card className="p-4 bg-white dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 shadow-sm">
              <div className="text-xs text-slate-500 dark:text-slate-400 mb-1 flex items-center gap-1.5">
                <BarChart3 className="w-3.5 h-3.5 text-sky-600 dark:text-sky-400" /> Median GPA
              </div>
              <div className="text-2xl font-black font-mono text-sky-600 dark:text-sky-400">{classData.median_gpa.toFixed(2)}</div>
            </Card>

            <Card className="p-4 bg-white dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 shadow-sm">
              <div className="text-xs text-slate-500 dark:text-slate-400 mb-1 flex items-center gap-1.5">
                <Hash className="w-3.5 h-3.5 text-purple-600 dark:text-purple-400" /> Mode GPA
              </div>
              <div className="text-2xl font-black font-mono text-purple-600 dark:text-purple-400">{classData.mode_gpa.toFixed(2)}</div>
            </Card>

            <Card className="p-4 bg-white dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 shadow-sm">
              <div className="text-xs text-slate-500 dark:text-slate-400 mb-1 flex items-center gap-1.5">
                <ArrowUpRight className="w-3.5 h-3.5 text-amber-600 dark:text-amber-400" /> Highest GPA
              </div>
              <div className="text-2xl font-black font-mono text-amber-600 dark:text-amber-400">{classData.highest_gpa.toFixed(2)}</div>
            </Card>

            <Card className="p-4 bg-white dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 shadow-sm">
              <div className="text-xs text-slate-500 dark:text-slate-400 mb-1 flex items-center gap-1.5">
                <ArrowDownRight className="w-3.5 h-3.5 text-rose-600 dark:text-rose-400" /> Lowest GPA
              </div>
              <div className="text-2xl font-black font-mono text-rose-600 dark:text-rose-400">{classData.lowest_gpa.toFixed(2)}</div>
            </Card>
          </div>

          <Card glass className="p-6 border-slate-200 dark:border-slate-800">
            <h4 className="font-bold text-sm text-slate-900 dark:text-slate-100 mb-4 flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
              Current Semester GPA Distribution
            </h4>

            <div className="space-y-3.5">
              {classData.distribution.map((d) => (
                <div key={d.bracket}>
                  <div className="flex justify-between text-xs text-slate-700 dark:text-slate-300 mb-1">
                    <span>{d.bracket}</span>
                    <span className="font-mono text-emerald-600 dark:text-emerald-400 font-bold">
                      {d.count} {d.count === 1 ? 'student' : 'students'} ({d.percentage}%)
                    </span>
                  </div>
                  <div className="w-full h-2.5 rounded-full bg-slate-100 dark:bg-slate-950 overflow-hidden border border-slate-200 dark:border-slate-800/80">
                    <div
                      className="h-full bg-emerald-500 rounded-full transition-all duration-500"
                      style={{ width: `${Math.max(d.percentage > 0 ? 3 : 0, d.percentage)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>
      )}

      {/* SECTION 3: CUMULATIVE ANALYSIS */}
      {activeAnalysisView === 'cumulative' && (
        <div className="space-y-6 animate-in fade-in duration-200">
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            <Card className="p-4 bg-white dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 shadow-sm">
              <div className="text-xs text-slate-500 dark:text-slate-400 mb-1 flex items-center gap-1.5">
                <Users className="w-3.5 h-3.5 text-slate-500 dark:text-slate-400" /> Total Students
              </div>
              <div className="text-2xl font-black font-mono text-slate-900 dark:text-slate-100">{cumulativeData.total_students}</div>
            </Card>

            <Card className="p-4 bg-white dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 shadow-sm">
              <div className="text-xs text-slate-500 dark:text-slate-400 mb-1 flex items-center gap-1.5">
                <TrendingUp className="w-3.5 h-3.5 text-sky-600 dark:text-sky-400" /> Average CGPA
              </div>
              <div className="text-2xl font-black font-mono text-sky-600 dark:text-sky-400">{cumulativeData.average_cgpa.toFixed(2)}</div>
            </Card>

            <Card className="p-4 bg-white dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 shadow-sm">
              <div className="text-xs text-slate-500 dark:text-slate-400 mb-1 flex items-center gap-1.5">
                <BarChart3 className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" /> Median CGPA
              </div>
              <div className="text-2xl font-black font-mono text-emerald-600 dark:text-emerald-400">{cumulativeData.median_cgpa.toFixed(2)}</div>
            </Card>

            <Card className="p-4 bg-white dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 shadow-sm">
              <div className="text-xs text-slate-500 dark:text-slate-400 mb-1 flex items-center gap-1.5">
                <Hash className="w-3.5 h-3.5 text-purple-600 dark:text-purple-400" /> Mode CGPA
              </div>
              <div className="text-2xl font-black font-mono text-purple-600 dark:text-purple-400">{cumulativeData.mode_cgpa.toFixed(2)}</div>
            </Card>

            <Card className="p-4 bg-white dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 shadow-sm">
              <div className="text-xs text-slate-500 dark:text-slate-400 mb-1 flex items-center gap-1.5">
                <ArrowUpRight className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" /> Highest CGPA
              </div>
              <div className="text-2xl font-black font-mono text-emerald-600 dark:text-emerald-400">{cumulativeData.highest_cgpa.toFixed(2)}</div>
            </Card>

            <Card className="p-4 bg-white dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 shadow-sm">
              <div className="text-xs text-slate-500 dark:text-slate-400 mb-1 flex items-center gap-1.5">
                <ArrowDownRight className="w-3.5 h-3.5 text-rose-600 dark:text-rose-400" /> Lowest CGPA
              </div>
              <div className="text-2xl font-black font-mono text-rose-600 dark:text-rose-400">{cumulativeData.lowest_cgpa.toFixed(2)}</div>
            </Card>
          </div>

          <Card glass className="p-6 border-slate-200 dark:border-slate-800">
            <h4 className="font-bold text-sm text-slate-900 dark:text-slate-100 mb-4 flex items-center gap-2">
              <Layers className="w-4 h-4 text-sky-600 dark:text-sky-400" />
              Cumulative CGPA Distribution (Extracted Directly From Sheet)
            </h4>

            <div className="space-y-3.5">
              {cumulativeData.distribution.map((d) => (
                <div key={d.bracket}>
                  <div className="flex justify-between text-xs text-slate-700 dark:text-slate-300 mb-1">
                    <span>{d.bracket}</span>
                    <span className="font-mono text-sky-600 dark:text-sky-400 font-bold">
                      {d.count} {d.count === 1 ? 'student' : 'students'} ({d.percentage}%)
                    </span>
                  </div>
                  <div className="w-full h-2.5 rounded-full bg-slate-100 dark:bg-slate-950 overflow-hidden border border-slate-200 dark:border-slate-800/80">
                    <div
                      className="h-full bg-sky-500 rounded-full transition-all duration-500"
                      style={{ width: `${Math.max(d.percentage > 0 ? 3 : 0, d.percentage)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>
      )}

      {/* SECTION 4: CLASS LEADERBOARD WITH DUAL RANKING */}
      {activeAnalysisView === 'leaderboard' && (() => {
        let list = [...leaderboard];

        if (rankingSortMode === 'cumulative') {
          list.sort((a, b) => {
            const rankA = a.cumulative_rank ?? 9999;
            const rankB = b.cumulative_rank ?? 9999;
            if (rankA !== rankB) return rankA - rankB;
            return b.cgpa - a.cgpa;
          });
        } else {
          list.sort((a, b) => {
            const rankA = a.semester_rank ?? 9999;
            const rankB = b.semester_rank ?? 9999;
            if (rankA !== rankB) return rankA - rankB;
            return b.gpa - a.gpa;
          });
        }

        const topSemesterStudent = leaderboard.reduce<typeof leaderboard[0] | null>(
          (best, curr) => (!best || curr.gpa > best.gpa ? curr : best),
          null
        );
        const topCumulativeStudent = leaderboard.reduce<typeof leaderboard[0] | null>(
          (best, curr) => (!best || curr.cgpa > best.cgpa ? curr : best),
          null
        );

        return (
          <div className="space-y-6 animate-in fade-in duration-200">
            {/* Top Performers Podium Highlights */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {topSemesterStudent && (
                <Card className="p-5 bg-white dark:bg-slate-900/80 border border-slate-200 dark:border-slate-800 shadow-sm">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-xl bg-emerald-500/10 dark:bg-emerald-500/20 border border-emerald-500/20 dark:border-emerald-500/30 flex items-center justify-center text-emerald-600 dark:text-emerald-400">
                        <Trophy className="w-5 h-5" />
                      </div>
                      <div>
                        <span className="text-[10px] font-bold text-emerald-600 dark:text-emerald-400 uppercase tracking-wider font-mono">
                          #1 Current Semester Rank
                        </span>
                        <h4 className="font-bold text-sm text-slate-900 dark:text-slate-100">{topSemesterStudent.student_name}</h4>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-xl font-black font-mono text-emerald-600 dark:text-emerald-400">{topSemesterStudent.gpa.toFixed(2)} GPA</div>
                      <span className="text-[10px] text-slate-500 dark:text-slate-400 font-mono">ID: {topSemesterStudent.student_id}</span>
                    </div>
                  </div>
                </Card>
              )}

              {topCumulativeStudent && (
                <Card className="p-5 bg-white dark:bg-slate-900/80 border border-slate-200 dark:border-slate-800 shadow-sm">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-xl bg-sky-500/10 dark:bg-sky-500/20 border border-sky-500/20 dark:border-sky-500/30 flex items-center justify-center text-sky-600 dark:text-sky-400">
                        <TrendingUp className="w-5 h-5" />
                      </div>
                      <div>
                        <span className="text-[10px] font-bold text-sky-600 dark:text-sky-400 uppercase tracking-wider font-mono">
                          #1 Cumulative CGPA Rank
                        </span>
                        <h4 className="font-bold text-sm text-slate-900 dark:text-slate-100">{topCumulativeStudent.student_name}</h4>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-xl font-black font-mono text-sky-600 dark:text-sky-400">{topCumulativeStudent.cgpa.toFixed(2)} CGPA</div>
                      <span className="text-[10px] text-slate-500 dark:text-slate-400 font-mono">ID: {topCumulativeStudent.student_id}</span>
                    </div>
                  </div>
                </Card>
              )}
            </div>

            {/* Leaderboard Table Card */}
            <Card glass className="overflow-hidden p-0 border-slate-200 dark:border-slate-800 shadow-sm dark:shadow-xl">
              <div className="p-4 sm:p-5 border-b border-slate-200 dark:border-slate-800 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 bg-slate-50 dark:bg-slate-900/60">
                <div>
                  <h4 className="font-bold text-base text-slate-900 dark:text-slate-100 flex items-center gap-2">
                    <Trophy className="w-4 h-4 text-amber-500 dark:text-amber-400" />
                    Academic Performance Leaderboard
                  </h4>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                    Compare rankings across current semester GPA and overall cumulative CGPA.
                  </p>
                </div>

                {/* Ranking Sort Mode Switcher Buttons */}
                <div className="flex items-center bg-slate-200/70 dark:bg-slate-950 p-1 rounded-xl border border-slate-200 dark:border-slate-800 text-xs">
                  <button
                    onClick={() => setRankingSortMode('semester')}
                    className={`px-3 py-1.5 rounded-lg font-bold transition-all flex items-center gap-1.5 ${
                      rankingSortMode === 'semester'
                        ? 'bg-emerald-500/20 text-emerald-700 dark:text-emerald-300 border border-emerald-500/30 shadow-sm'
                        : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
                    }`}
                  >
                    <Trophy className="w-3 h-3 text-emerald-600 dark:text-emerald-400" />
                    Semester GPA Rank
                  </button>

                  <button
                    onClick={() => setRankingSortMode('cumulative')}
                    className={`px-3 py-1.5 rounded-lg font-bold transition-all flex items-center gap-1.5 ${
                      rankingSortMode === 'cumulative'
                        ? 'bg-sky-500/20 text-sky-700 dark:text-sky-300 border border-sky-500/30 shadow-sm'
                        : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
                    }`}
                  >
                    <Layers className="w-3 h-3 text-sky-600 dark:text-sky-400" />
                    Cumulative CGPA Rank
                  </button>
                </div>
              </div>

              {/* Table */}
              <div className="table-scroll-wrapper overflow-x-auto">
                <table className="w-full text-left text-xs min-w-[650px] sm:min-w-full">
                  <thead className="bg-slate-100/90 dark:bg-slate-950/90 text-slate-700 dark:text-slate-400 font-bold uppercase tracking-wider border-b border-slate-200 dark:border-slate-800">
                    <tr>
                      <th className={`px-5 py-3.5 ${rankingSortMode === 'semester' ? 'text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/20' : ''}`}>
                        Semester Rank
                      </th>
                      <th className={`px-5 py-3.5 ${rankingSortMode === 'cumulative' ? 'text-sky-600 dark:text-sky-400 bg-sky-50 dark:bg-sky-950/20' : ''}`}>
                        Cumulative Rank
                      </th>
                      <th className="px-5 py-3.5">Student ID</th>
                      <th className="px-5 py-3.5">Student Name</th>
                      <th className={`px-5 py-3.5 text-center ${rankingSortMode === 'semester' ? 'text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/10 font-black' : ''}`}>
                        Semester GPA
                      </th>
                      <th className={`px-5 py-3.5 text-center ${rankingSortMode === 'cumulative' ? 'text-sky-600 dark:text-sky-400 bg-sky-50 dark:bg-sky-950/10 font-black' : ''}`}>
                        Cumulative CGPA
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200/60 dark:divide-slate-800/60 font-mono text-slate-700 dark:text-slate-300">
                    {list.map((item) => {
                      const semRank = item.semester_rank ?? item.rank;
                      const cumRank = item.cumulative_rank ?? item.rank;
                      return (
                        <tr key={item.student_id} className="hover:bg-slate-50 dark:hover:bg-slate-800/30 transition-colors">
                          {/* Semester Rank Column */}
                          <td className={`px-5 py-3.5 font-bold ${rankingSortMode === 'semester' ? 'bg-emerald-50 dark:bg-emerald-950/10' : ''}`}>
                            {semRank === 1 ? (
                              <span className="text-amber-500 dark:text-amber-400 flex items-center gap-1 font-black">
                                <Trophy className="w-3.5 h-3.5" /> #1
                              </span>
                            ) : (
                              <span className={rankingSortMode === 'semester' ? 'text-emerald-600 dark:text-emerald-400 font-bold' : 'text-slate-500 dark:text-slate-400'}>
                                #{semRank}
                              </span>
                            )}
                          </td>

                          {/* Cumulative Rank Column */}
                          <td className={`px-5 py-3.5 font-bold ${rankingSortMode === 'cumulative' ? 'bg-sky-50 dark:bg-sky-950/10' : ''}`}>
                            {cumRank === 1 ? (
                              <span className="text-amber-500 dark:text-amber-400 flex items-center gap-1 font-black">
                                <Trophy className="w-3.5 h-3.5" /> #1
                              </span>
                            ) : (
                              <span className={rankingSortMode === 'cumulative' ? 'text-sky-600 dark:text-sky-400 font-bold' : 'text-slate-500 dark:text-slate-400'}>
                                #{cumRank}
                              </span>
                            )}
                          </td>

                          {/* Student ID */}
                          <td className="px-5 py-3.5 text-emerald-600 dark:text-emerald-400 font-bold">{item.student_id}</td>

                          {/* Student Name */}
                          <td className="px-5 py-3.5 font-sans font-medium text-slate-900 dark:text-slate-200">{item.student_name}</td>

                          {/* Semester GPA */}
                          <td className={`px-5 py-3.5 text-center font-bold font-mono ${rankingSortMode === 'semester' ? 'text-emerald-600 dark:text-emerald-300 font-black text-sm bg-emerald-50 dark:bg-emerald-950/10' : 'text-emerald-600 dark:text-emerald-400'}`}>
                            {item.gpa.toFixed(2)}
                          </td>

                          {/* Cumulative CGPA */}
                          <td className={`px-5 py-3.5 text-center font-bold font-mono ${rankingSortMode === 'cumulative' ? 'text-sky-600 dark:text-sky-300 font-black text-sm bg-sky-50 dark:bg-sky-950/10' : 'text-sky-600 dark:text-sky-400'}`}>
                            {item.cgpa.toFixed(2)}
                          </td>
                        </tr>
                      );
                    })}

                    {list.length === 0 && (
                      <tr>
                        <td colSpan={6} className="px-5 py-8 text-center text-slate-500 font-sans text-xs">
                          No student records available in this dataset.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </Card>
          </div>
        );
      })()}
    </div>
  );
};
