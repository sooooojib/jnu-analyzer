import React, { useState, useEffect } from 'react';
import { Card } from '../common/Card';
import { Badge } from '../common/Badge';
import { Button } from '../common/Button';
import { Alert } from '../common/Alert';
import { Tooltip } from '../common/Tooltip';
import { ScorecardSkeleton } from '../common/Skeleton';
import { api } from '../../api/endpoints';
import { StudentRecord } from '../../types/student';
import { CohortAnalytics } from '../../types/analytics';
import { 
  Award, 
  BookOpen, 
  BarChart3, 
  Users, 
  Trophy, 
  Search, 
  GraduationCap,
  Scale, 
  Info,
  Download,
  X
} from 'lucide-react';

// Charts
import { GPADistributionChart } from '../charts/GPADistributionChart';
import { StudentVsClassAverageChart } from '../charts/StudentVsClassAverageChart';
import { SubjectGPComparisonChart } from '../charts/SubjectGPComparisonChart';
import { CurrentVsCumulativeSummaryChart } from '../charts/CurrentVsCumulativeSummaryChart';
import { getLetterGradeFromGP } from '../../utils/gradeUtils';

interface ResultDashboardProps {
  sessionId?: string;
  initialStudentId?: string;
  onStudentChange?: (studentId: string) => void;
  onNavigateToTab?: (tab: string) => void;
  onCompareStudents?: (studentA: string, studentB: string) => void;
}

export const ResultDashboard: React.FC<ResultDashboardProps> = ({
  sessionId,
  initialStudentId = '',
  onStudentChange,
  onNavigateToTab,
  onCompareStudents,
}) => {
  // State
  const [searchInput, setSearchInput] = useState(initialStudentId);
  const [activeStudentId, setActiveStudentId] = useState(initialStudentId);
  const [student, setStudent] = useState<StudentRecord | null>(null);
  const [analytics, setAnalytics] = useState<CohortAnalytics | null>(null);
  const [isLoadingStudent, setIsLoadingStudent] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [exportMessage, setExportMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  
  // Dashboard Sub-tabs
  const [activeSection, setActiveSection] = useState<'overview' | 'subjects' | 'cohort_stats'>('overview');

  // Quick Comparison Drawer State
  const [compareTargetId, setCompareTargetId] = useState('');

  // Sync with initialStudentId if prop changes
  useEffect(() => {
    if (initialStudentId && initialStudentId !== activeStudentId) {
      setSearchInput(initialStudentId);
      setActiveStudentId(initialStudentId);
      if (sessionId) {
        fetchStudentData(initialStudentId);
      }
    }
  }, [initialStudentId, sessionId]);

  // Fetch Student Scorecard
  const fetchStudentData = async (studentIdToFetch: string) => {
    const cleanId = studentIdToFetch.trim();
    if (!cleanId || !sessionId) return;

    setIsLoadingStudent(true);
    setErrorMessage(null);

    try {
      const data = await api.getStudentScorecard(sessionId, cleanId);
      setStudent(data);
      setActiveStudentId(cleanId);
      onStudentChange?.(cleanId);
    } catch (err: any) {
      setStudent(null);
      const serverMsg = err.response?.data?.message;
      if (err.response?.status === 404) {
        setErrorMessage(serverMsg || `The Student ID was not found in this result sheet.`);
      } else if (err.response?.status === 422) {
        setErrorMessage(serverMsg || 'Some extracted values require verification in the review table.');
      } else {
        setErrorMessage(serverMsg || 'Could not retrieve student result. Please ensure the result sheet is uploaded.');
      }
    } finally {
      setIsLoadingStudent(false);
    }
  };

  // Fetch Cohort Analytics
  const fetchCohortAnalytics = async () => {
    if (!sessionId) return;
    try {
      const data = await api.getCohortAnalytics(sessionId);
      setAnalytics(data);
    } catch (err: any) {
      console.error('Failed to load cohort analytics', err);
    }
  };

  useEffect(() => {
    if (sessionId) {
      fetchCohortAnalytics();
      if (activeStudentId) {
        fetchStudentData(activeStudentId);
      }
    }
  }, [sessionId]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchInput.trim()) {
      fetchStudentData(searchInput.trim());
    }
  };

  const handleQuickCompare = (e: React.FormEvent) => {
    e.preventDefault();
    if (onCompareStudents && activeStudentId && compareTargetId.trim()) {
      onCompareStudents(activeStudentId, compareTargetId.trim());
    } else if (onNavigateToTab) {
      onNavigateToTab('comparison');
    }
  };

  const handleExportStudentPdf = async () => {
    if (!sessionId || !student?.student_id) return;
    setIsExporting(true);
    setExportMessage(null);
    try {
      const blob = await api.exportStudentPdf(sessionId, student.student_id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      const cleanId = student.student_id.replace(/[^a-zA-Z0-9_-]/g, '_');
      a.download = `JNU_Student_Analysis_${cleanId}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      setExportMessage('Student analysis exported successfully.');
      setTimeout(() => setExportMessage(null), 4000);
    } catch (err: any) {
      console.error('Student export failed', err);
      setExportMessage('Failed to export student analysis. Please try again.');
    } finally {
      setIsExporting(false);
    }
  };

  // Helper badge for letter grade
  const getGradeBadgeVariant = (grade: string) => {
    const g = grade.toUpperCase();
    if (g.startsWith('A')) return 'emerald';
    if (g.startsWith('B') || g.startsWith('C')) return 'blue';
    if (g.startsWith('D')) return 'amber';
    return 'rose';
  };

  // Class & Cumulative stats shortcuts
  const classData = analytics?.class_analysis;
  const cumulativeData = analytics?.cumulative_analysis;
  const sampleStudents = analytics?.student_leaderboard?.slice(0, 5) || [];

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      {/* Top Academic Context & Search Header */}
      <Card className="p-4 sm:p-5 bg-white dark:bg-slate-900/90 border border-slate-200 dark:border-slate-800 shadow-md space-y-3">
        <div className="flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-3">
          {/* Search Bar */}
          <form onSubmit={handleSearchSubmit} className="flex-1 flex items-center gap-2">
            <div className="relative flex-1 min-w-0">
              <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Enter Student ID (e.g. B220305009)..."
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl pl-10 pr-3 py-2 text-xs sm:text-sm text-slate-900 dark:text-slate-100 placeholder-slate-400 dark:placeholder-slate-500 font-mono uppercase focus:outline-none focus:border-emerald-500 transition-colors"
              />
            </div>
            <Button
              type="submit"
              size="sm"
              isLoading={isLoadingStudent}
              leftIcon={<Search className="w-4 h-4" />}
              className="shrink-0"
            >
              Lookup
            </Button>
          </form>

          {/* Quick Compare */}
          {student && (
            <div className="flex items-center text-xs">
              <form onSubmit={handleQuickCompare} className="flex items-center gap-2 w-full sm:w-auto">
                <div className="relative flex-1 sm:w-44">
                  <input
                    type="text"
                    placeholder="Compare Student ID..."
                    value={compareTargetId}
                    onChange={(e) => setCompareTargetId(e.target.value)}
                    className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-900 dark:text-slate-200 font-mono uppercase focus:outline-none focus:border-sky-500"
                  />
                </div>
                <Button type="submit" size="sm" variant="secondary" leftIcon={<Scale className="w-3.5 h-3.5" />} className="shrink-0">
                  Compare
                </Button>
              </form>
            </div>
          )}
        </div>

        {/* Quick Sample IDs Clickable Chips */}
        {sampleStudents.length > 0 && !student && (
          <div className="flex flex-wrap items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400 pt-1 border-t border-slate-100 dark:border-slate-800/60">
            <span className="font-medium">Quick Select from Dataset:</span>
            {sampleStudents.map((s) => (
              <button
                key={s.student_id}
                type="button"
                onClick={() => {
                  setSearchInput(s.student_id);
                  fetchStudentData(s.student_id);
                }}
                className="px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800/80 hover:bg-emerald-500/10 hover:text-emerald-600 dark:hover:text-emerald-400 font-mono text-[11px] font-semibold transition-colors border border-slate-200 dark:border-slate-700/60"
              >
                {s.student_id} ({s.student_name.split(' ')[0]})
              </button>
            ))}
          </div>
        )}
      </Card>

      {/* Error State */}
      {errorMessage && (
        <Alert
          type="error"
          title="Student Lookup Notice"
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
          <button type="button" onClick={() => setExportMessage(null)} className="text-emerald-600 dark:text-emerald-400 hover:opacity-80 p-0.5 rounded transition-opacity ml-2" aria-label="Dismiss message">
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Loading Skeleton */}
      {isLoadingStudent && !student && <ScorecardSkeleton />}

      {/* Empty State when no student is looked up yet */}
      {!student && !isLoadingStudent && !errorMessage && (
        <Card className="p-12 text-center bg-white dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 flex flex-col items-center justify-center space-y-4">
          <div className="w-16 h-16 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-600 dark:text-emerald-400">
            <Search className="w-8 h-8" />
          </div>
          <div className="max-w-md space-y-2">
            <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100">Enter a Student ID to View Results</h3>
            <p className="text-xs text-slate-600 dark:text-slate-400">
              Type a Student ID (e.g. <span className="font-mono text-emerald-600 dark:text-emerald-400 font-bold">B220305009</span>) in the search bar above to inspect complete academic scorecards, GPA, rank, and subject breakdown.
            </p>
          </div>
        </Card>
      )}

      {/* MAIN DASHBOARD CONTENT */}
      {student && (
        <div className="space-y-6 animate-in fade-in duration-200">
          {/* Action Bar with Student Export Button */}
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 bg-white dark:bg-slate-900/90 border border-slate-200 dark:border-slate-800 p-3.5 sm:p-4 rounded-2xl shadow-sm">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-600 dark:text-emerald-400 shrink-0">
                <GraduationCap className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-sm sm:text-base font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
                  <span>{student.student_name}</span>
                  <Badge variant="emerald" size="sm" className="font-mono">{student.student_id}</Badge>
                </h2>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Class Rank #{student.semester_result.semester_rank} • {student.course_grades.length} Courses Analyzed
                </p>
              </div>
            </div>

            <Button
              variant="secondary"
              size="sm"
              onClick={handleExportStudentPdf}
              isLoading={isExporting}
              leftIcon={<Download className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />}
              className="w-full sm:w-auto font-medium border-slate-200 dark:border-slate-700/80 hover:border-emerald-500/40 shrink-0"
            >
              {isExporting ? 'Generating student analysis...' : 'Export Student Analysis'}
            </Button>
          </div>

          {/* SECTION 1: 5 PRIMARY KPI TILES */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3.5">
            {/* Tile 1: Student Identity */}
            <Card className="p-4 bg-white dark:bg-slate-900/80 border border-slate-200 dark:border-slate-800 relative overflow-hidden flex flex-col justify-between shadow-sm">
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[11px] font-mono text-emerald-600 dark:text-emerald-400 font-bold">
                    SL #{student.serial_no || '1'}
                  </span>
                  <span className="text-[10px] font-medium text-slate-500 uppercase tracking-wider">Student Profile</span>
                </div>
                <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 truncate" title={student.student_name}>
                  {student.student_name}
                </h3>
              </div>
              <div className="mt-3 pt-2 border-t border-slate-100 dark:border-slate-800/80 flex items-center justify-between text-xs font-mono">
                <span className="text-slate-500 dark:text-slate-400">ID:</span>
                <span className="text-slate-900 dark:text-slate-200 font-bold">{student.student_id}</span>
              </div>
            </Card>

            {/* Tile 2: Current Semester GPA */}
            <Card className="p-4 bg-white dark:bg-slate-900/80 border border-slate-200 dark:border-slate-800 flex flex-col justify-between shadow-sm">
              <div>
                <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400 mb-1">
                  <span className="flex items-center gap-1 font-sans">
                    Semester GPA
                    <Tooltip content="Current semester grade point average (Credit-weighted)">
                      <Info className="w-3 h-3 text-slate-400 cursor-help" />
                    </Tooltip>
                  </span>
                  <Badge variant="emerald" size="sm">{student.semester_result.result_status || 'PASSED'}</Badge>
                </div>
                <div className="flex items-baseline gap-2">
                  <span className="text-2xl sm:text-3xl font-black font-mono text-emerald-600 dark:text-emerald-400">
                    {student.semester_result.gpa.toFixed(2)}
                  </span>
                  <span className="text-xs sm:text-sm font-bold font-sans text-emerald-700 dark:text-emerald-300 bg-emerald-500/10 dark:bg-emerald-500/20 px-2 py-0.5 rounded-lg border border-emerald-500/20 dark:border-emerald-500/30">
                    {getLetterGradeFromGP(student.semester_result.gpa)}
                  </span>
                </div>
              </div>
              <div className="mt-3 pt-2 border-t border-slate-100 dark:border-slate-800/80 flex items-center justify-between text-[11px] text-slate-500 dark:text-slate-400">
                <span>Credits: {student.semester_result.credits_earned.toFixed(1)} / {student.semester_result.credits_attempted.toFixed(1)}</span>
              </div>
            </Card>

            {/* Tile 3: Semester Rank */}
            <Card className="p-4 bg-white dark:bg-slate-900/80 border border-slate-200 dark:border-slate-800 flex flex-col justify-between shadow-sm">
              <div>
                <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400 mb-1">
                  <span className="flex items-center gap-1 font-sans">
                    Semester Rank
                    <Tooltip content="Standard Competition Rank (1224 rule) in current sheet">
                      <Info className="w-3 h-3 text-slate-400 cursor-help" />
                    </Tooltip>
                  </span>
                  <Trophy className="w-3.5 h-3.5 text-amber-500 dark:text-amber-400" />
                </div>
                <div className="text-2xl sm:text-3xl font-black font-mono text-amber-600 dark:text-amber-400">
                  {student.semester_result.semester_rank != null ? `#${student.semester_result.semester_rank}` : '—'}
                </div>
              </div>
              <div className="mt-3 pt-2 border-t border-slate-100 dark:border-slate-800/80 flex items-center justify-between text-[11px] text-slate-500 dark:text-slate-400">
                <span>Percentile: <strong className="text-sky-600 dark:text-sky-400 font-mono">{student.semester_result.semester_percentile != null ? `${student.semester_result.semester_percentile}%` : '—'}</strong></span>
              </div>
            </Card>

            {/* Tile 4: Cumulative CGPA */}
            <Card className="p-4 bg-white dark:bg-slate-900/80 border border-slate-200 dark:border-slate-800 flex flex-col justify-between shadow-sm">
              <div>
                <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400 mb-1">
                  <span className="flex items-center gap-1 font-sans">
                    Cumulative CGPA
                    <Tooltip content="Extracted cumulative CGPA from tabulation sheet">
                      <Info className="w-3 h-3 text-slate-400 cursor-help" />
                    </Tooltip>
                  </span>
                  <Badge variant="blue" size="sm">{student.cumulative_result.result_status || 'PASSED'}</Badge>
                </div>
                <div className="flex items-baseline gap-2">
                  <span className="text-2xl sm:text-3xl font-black font-mono text-sky-600 dark:text-sky-400">
                    {student.cumulative_result.cgpa.toFixed(2)}
                  </span>
                  <span className="text-xs sm:text-sm font-bold font-sans text-sky-700 dark:text-sky-300 bg-sky-500/10 dark:bg-sky-500/20 px-2 py-0.5 rounded-lg border border-sky-500/20 dark:border-sky-500/30">
                    {getLetterGradeFromGP(student.cumulative_result.cgpa)}
                  </span>
                </div>
              </div>
              <div className="mt-3 pt-2 border-t border-slate-100 dark:border-slate-800/80 flex items-center justify-between text-[11px] text-slate-500 dark:text-slate-400">
                <span>Earned Cr: {student.cumulative_result.total_credits_earned.toFixed(1)}</span>
              </div>
            </Card>

            {/* Tile 5: Cumulative Rank */}
            <Card className="p-4 bg-white dark:bg-slate-900/80 border border-slate-200 dark:border-slate-800 flex flex-col justify-between shadow-sm">
              <div>
                <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400 mb-1">
                  <span className="flex items-center gap-1 font-sans">
                    Cumulative Rank
                    <Tooltip content="Cumulative rank calculated across cohort">
                      <Info className="w-3 h-3 text-slate-400 cursor-help" />
                    </Tooltip>
                  </span>
                  <Award className="w-3.5 h-3.5 text-sky-500 dark:text-sky-400" />
                </div>
                <div className="text-2xl sm:text-3xl font-black font-mono text-sky-600 dark:text-sky-400">
                  {student.cumulative_result.cumulative_rank != null ? `#${student.cumulative_result.cumulative_rank}` : '—'}
                </div>
              </div>
              <div className="mt-3 pt-2 border-t border-slate-100 dark:border-slate-800/80 flex items-center justify-between text-[11px] text-slate-500 dark:text-slate-400">
                <span>Percentile: <strong className="text-sky-600 dark:text-sky-400 font-mono">{student.cumulative_result.cumulative_percentile != null ? `${student.cumulative_result.cumulative_percentile}%` : '—'}</strong></span>
              </div>
            </Card>
          </div>

          {/* DASHBOARD NAVIGATION PILLS */}
          <div className="flex items-center gap-2 border-b border-slate-200 dark:border-slate-800/80 pt-2 pb-3 px-1 text-xs overflow-x-auto">
            <button
              onClick={() => setActiveSection('overview')}
              className={`px-3 py-1.5 rounded-lg font-semibold transition-all flex items-center gap-1.5 ${
                activeSection === 'overview'
                  ? 'bg-emerald-600 text-white dark:bg-emerald-500/20 dark:text-emerald-300 dark:border dark:border-emerald-500/30 shadow-sm'
                  : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800/50'
              }`}
            >
              <BookOpen className="w-3.5 h-3.5" />
              1. Student Scorecard & Comparative Breakdown
            </button>

            <button
              onClick={() => setActiveSection('subjects')}
              className={`px-3 py-1.5 rounded-lg font-semibold transition-all flex items-center gap-1.5 ${
                activeSection === 'subjects'
                  ? 'bg-emerald-600 text-white dark:bg-emerald-500/20 dark:text-emerald-300 dark:border dark:border-emerald-500/30 shadow-sm'
                  : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800/50'
              }`}
            >
              <BarChart3 className="w-3.5 h-3.5" />
              2. Subject GP vs Class Averages
            </button>

            <button
              onClick={() => setActiveSection('cohort_stats')}
              className={`px-3 py-1.5 rounded-lg font-semibold transition-all flex items-center gap-1.5 ${
                activeSection === 'cohort_stats'
                  ? 'bg-emerald-600 text-white dark:bg-emerald-500/20 dark:text-emerald-300 dark:border dark:border-emerald-500/30 shadow-sm'
                  : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800/50'
              }`}
            >
              <Users className="w-3.5 h-3.5" />
              3. GPA Distribution Position
            </button>
          </div>

          {/* SECTION A: STUDENT OVERVIEW & COMPARATIVE CHARTS */}
          {activeSection === 'overview' && (
            <div className="space-y-6 animate-in fade-in duration-150">
              {/* Chart 1: Current vs Cumulative Summary Alignment */}
              <CurrentVsCumulativeSummaryChart
                semesterGPA={student.semester_result.gpa}
                semesterRank={student.semester_result.semester_rank}
                semesterPercentile={student.semester_result.semester_percentile}
                semesterCreditsEarned={student.semester_result.credits_earned}
                semesterCreditsAttempted={student.semester_result.credits_attempted}
                semesterStatus={student.semester_result.result_status}
                cumulativeCGPA={student.cumulative_result.cgpa}
                cumulativeRank={student.cumulative_result.cumulative_rank}
                cumulativePercentile={student.cumulative_result.cumulative_percentile}
                cumulativeCreditsEarned={student.cumulative_result.total_credits_earned}
                cumulativeStatus={student.cumulative_result.result_status}
              />

              {/* Chart 2: Student GPA vs Class Average Chart */}
              {classData && (
                <StudentVsClassAverageChart
                  studentGPA={student.semester_result.gpa}
                  studentName={student.student_name}
                  studentId={student.student_id}
                  classMeanGPA={classData.average_gpa}
                  classMedianGPA={classData.median_gpa}
                  classHighestGPA={classData.highest_gpa}
                  classLowestGPA={classData.lowest_gpa}
                  classStdDev={classData.std_dev_gpa}
                  totalStudents={classData.total_students}
                />
              )}

              {/* Academic Grade Sheet Table */}
              <Card glass className="overflow-hidden p-0 border-slate-200 dark:border-slate-800 shadow-md">
                <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <GraduationCap className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0" />
                    <h4 className="font-bold text-sm text-slate-900 dark:text-slate-100">
                      Academic Course Breakdown ({student.student_id})
                    </h4>
                  </div>
                  <Badge variant="emerald" size="sm" className="self-start sm:self-auto">Deterministic Calculations</Badge>
                </div>

                <div className="table-scroll-wrapper overflow-x-auto">
                  <table className="w-full text-left text-xs min-w-[550px] sm:min-w-full">
                    <thead className="bg-slate-50 dark:bg-slate-950/80 text-slate-600 dark:text-slate-400 font-bold uppercase tracking-wider border-b border-slate-200 dark:border-slate-800">
                      <tr>
                        <th className="px-5 py-3.5">Course Code</th>
                        <th className="px-5 py-3.5">Course Title</th>
                        <th className="px-5 py-3.5 text-center">Credit Hours</th>
                        <th className="px-5 py-3.5 text-center">
                          <span className="flex items-center justify-center gap-1">
                            Grade Point (GP)
                            <Tooltip content="Single-subject GP (0.00 – 4.00)">
                              <Info className="w-3 h-3 text-slate-400 cursor-help" />
                            </Tooltip>
                          </span>
                        </th>
                        <th className="px-5 py-3.5 text-center">Letter Grade</th>
                        <th className="px-5 py-3.5 text-center">Subject Rank</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60 font-mono text-slate-700 dark:text-slate-300">
                      {student.course_grades.map((cg, idx) => {
                        const gpVal = cg.grade_point;
                        return (
                          <tr key={cg.course_code || idx} className="hover:bg-slate-50 dark:hover:bg-slate-800/30 transition-colors">
                            <td className="px-5 py-3.5 font-bold text-sky-600 dark:text-sky-400">{cg.course_code}</td>
                            <td className="px-5 py-3.5 font-sans font-medium text-slate-800 dark:text-slate-200">
                              {cg.course_title || cg.course_code}
                            </td>
                            <td className="px-5 py-3.5 text-center text-slate-500 dark:text-slate-400">{cg.credits.toFixed(1)}</td>
                            <td className="px-5 py-3.5 text-center font-bold text-slate-900 dark:text-slate-100 text-sm">
                              {gpVal !== null ? gpVal.toFixed(2) : '—'}
                            </td>
                            <td className="px-5 py-3.5 text-center">
                              <Badge variant={getGradeBadgeVariant(cg.letter_grade)} size="sm">
                                {cg.letter_grade || '—'}
                              </Badge>
                            </td>
                            <td className="px-5 py-3.5 text-center">
                              {cg.subject_rank != null ? (
                                <Badge variant={cg.subject_rank === 1 ? 'amber' : 'slate'} size="sm">
                                  #{cg.subject_rank}
                                </Badge>
                              ) : (
                                <span className="text-slate-400">—</span>
                              )}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </Card>
            </div>
          )}

          {/* SECTION B: DETAILED SUBJECT ANALYSIS & RANKING CHARTS */}
          {activeSection === 'subjects' && (
            <div className="space-y-6 animate-in fade-in duration-150">
              <SubjectGPComparisonChart
                courseGrades={student.course_grades}
                subjectAnalytics={analytics?.subject_analysis}
              />
            </div>
          )}

          {/* SECTION C: CLASS STATISTICS & GPA DISTRIBUTION */}
          {activeSection === 'cohort_stats' && (
            <div className="space-y-6 animate-in fade-in duration-150">
              {classData?.distribution && (
                <GPADistributionChart
                  distribution={classData.distribution}
                  selectedStudentGPA={student.semester_result.gpa}
                  classMeanGPA={classData.average_gpa}
                  classMedianGPA={classData.median_gpa}
                  totalStudents={classData.total_students}
                  title="Class GPA Distribution (Current Semester)"
                  metricLabel="Current-Semester GPA"
                />
              )}

              {cumulativeData?.distribution && (
                <GPADistributionChart
                  distribution={cumulativeData.distribution}
                  selectedStudentGPA={student.cumulative_result.cgpa}
                  classMeanGPA={cumulativeData.average_cgpa}
                  classMedianGPA={cumulativeData.median_cgpa}
                  totalStudents={cumulativeData.total_students}
                  title="Cumulative GPA Distribution (CGPA)"
                  metricLabel="Cumulative GPA (CGPA)"
                />
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
