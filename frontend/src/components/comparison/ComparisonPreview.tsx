import React, { useState, useEffect } from 'react';
import { Card } from '../common/Card';
import { Badge } from '../common/Badge';
import { Button } from '../common/Button';
import { Alert } from '../common/Alert';
import { api } from '../../api/endpoints';
import { StudentComparisonResult } from '../../types/comparison';
import { StudentComparisonChart } from '../charts/StudentComparisonChart';
import {
  Scale,
  UserCheck,
  Minus,
  BookOpen,
  Download
} from 'lucide-react';

interface ComparisonPreviewProps {
  sessionId?: string;
  defaultStudentA?: string;
  defaultStudentB?: string;
  onStudentsChange?: (studentA: string, studentB: string) => void;
}

export const ComparisonPreview: React.FC<ComparisonPreviewProps> = ({
  sessionId,
  defaultStudentA = '',
  defaultStudentB = '',
  onStudentsChange,
}) => {
  const [studentAInput, setStudentAInput] = useState(defaultStudentA);
  const [studentBInput, setStudentBInput] = useState(defaultStudentB);
  const [comparison, setComparison] = useState<StudentComparisonResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [exportMessage, setExportMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Sync state if defaultStudentA / defaultStudentB props update
  useEffect(() => {
    if (defaultStudentA && defaultStudentA !== studentAInput) {
      setStudentAInput(defaultStudentA);
    }
    if (defaultStudentB && defaultStudentB !== studentBInput) {
      setStudentBInput(defaultStudentB);
    }
  }, [defaultStudentA, defaultStudentB]);

  const fetchComparison = async (idA: string, idB: string) => {
    const cleanA = idA.trim();
    const cleanB = idB.trim();

    if (!cleanA || !cleanB) {
      setErrorMessage('Please enter both Student A ID and Student B ID.');
      return;
    }

    if (!sessionId) {
      setErrorMessage('No active result sheet dataset found. Please upload a dataset first.');
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);

    try {
      const data = await api.compareStudents(sessionId, cleanA, cleanB);
      setComparison(data);
      onStudentsChange?.(cleanA, cleanB);
    } catch (err: any) {
      setComparison(null);
      const serverMsg = err.response?.data?.message;
      if (err.response?.status === 404) {
        setErrorMessage(serverMsg || 'One or both students were not found in this result sheet.');
      } else if (err.response?.status === 422) {
        setErrorMessage(serverMsg || 'Some extracted values require verification in the review table.');
      } else {
        setErrorMessage(serverMsg || 'Failed to compute student comparison. Please check the entered IDs.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (sessionId && (defaultStudentA || studentAInput) && (defaultStudentB || studentBInput)) {
      fetchComparison(defaultStudentA || studentAInput, defaultStudentB || studentBInput);
    }
  }, [sessionId]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchComparison(studentAInput, studentBInput);
  };

  const renderOutcomeBadge = (outcome: string) => {
    switch (outcome) {
      case 'STUDENT_A':
        return (
          <Badge variant="emerald" size="sm" className="gap-1 font-bold">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
            Student A
          </Badge>
        );
      case 'STUDENT_B':
        return (
          <Badge variant="blue" size="sm" className="gap-1 font-bold">
            <span className="w-1.5 h-1.5 rounded-full bg-sky-500" />
            Student B
          </Badge>
        );
      case 'TIED':
        return (
          <Badge variant="slate" size="sm" className="gap-1">
            <Minus className="w-3 h-3 text-slate-400" />
            Tied
          </Badge>
        );
      default:
        return <Badge variant="slate" size="sm">—</Badge>;
    }
  };

  const handleExportComparisonPdf = async () => {
    if (!sessionId || !comparison) return;
    setIsExporting(true);
    setExportMessage(null);
    try {
      const blob = await api.exportComparisonPdf(sessionId, comparison.student_a.id, comparison.student_b.id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      const safeA = comparison.student_a.id.replace(/[^a-zA-Z0-9_-]/g, '_');
      const safeB = comparison.student_b.id.replace(/[^a-zA-Z0-9_-]/g, '_');
      a.download = `JNU_Comparison_${safeA}_vs_${safeB}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      setExportMessage('Comparison exported successfully.');
      setTimeout(() => setExportMessage(null), 4000);
    } catch (err: any) {
      console.error('Comparison export failed', err);
      setExportMessage('Failed to export comparison report. Please try again.');
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      {/* Search Input Bar */}
      <Card className="p-4 sm:p-5 bg-white dark:bg-slate-900/80 border border-slate-200 dark:border-slate-800 shadow-md">
        <form onSubmit={handleSubmit} className="flex flex-col lg:flex-row items-center gap-4">
          <div className="flex-1 w-full flex flex-col sm:flex-row items-center gap-3">
            {/* Student A Input */}
            <div className="relative flex-1 w-full">
              <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-xs font-bold text-emerald-600 dark:text-emerald-400 font-mono">
                A:
              </span>
              <input
                type="text"
                placeholder="Student A ID (e.g. B220305018)..."
                value={studentAInput}
                onChange={(e) => setStudentAInput(e.target.value)}
                className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl pl-9 pr-4 py-2.5 text-sm text-slate-900 dark:text-slate-100 placeholder-slate-400 dark:placeholder-slate-500 font-mono uppercase focus:outline-none focus:border-emerald-500 transition-colors"
              />
            </div>

            <div className="text-slate-400 dark:text-slate-600 font-bold text-xs uppercase px-1">VS</div>

            {/* Student B Input */}
            <div className="relative flex-1 w-full">
              <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-xs font-bold text-sky-600 dark:text-sky-400 font-mono">
                B:
              </span>
              <input
                type="text"
                placeholder="Student B ID (e.g. B220305019)..."
                value={studentBInput}
                onChange={(e) => setStudentBInput(e.target.value)}
                className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl pl-9 pr-4 py-2.5 text-sm text-slate-900 dark:text-slate-100 placeholder-slate-400 dark:placeholder-slate-500 font-mono uppercase focus:outline-none focus:border-sky-500 transition-colors"
              />
            </div>
          </div>

          <Button
            type="submit"
            size="md"
            isLoading={isLoading}
            leftIcon={<Scale className="w-4 h-4" />}
            className="w-full lg:w-auto"
          >
            Compare Head-to-Head
          </Button>
        </form>
      </Card>

      {errorMessage && (
        <Alert
          type="error"
          title="Comparison Notice"
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

      {/* Empty State */}
      {!comparison && !isLoading && !errorMessage && (
        <Card className="p-12 text-center bg-white dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 flex flex-col items-center justify-center space-y-4">
          <div className="w-16 h-16 rounded-2xl bg-sky-500/10 border border-sky-500/20 flex items-center justify-center text-sky-600 dark:text-sky-400">
            <Scale className="w-8 h-8" />
          </div>
          <div className="max-w-md space-y-2">
            <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100">Select Two Students to Compare</h3>
            <p className="text-xs text-slate-600 dark:text-slate-400">
              Enter two Student IDs from the uploaded result sheet to generate a head-to-head course-by-course differential breakdown.
            </p>
          </div>
        </Card>
      )}

      {comparison && (
        <div className="space-y-6 animate-in fade-in duration-200">
          {/* Header & Export Action */}
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 bg-white dark:bg-slate-900/90 border border-slate-200 dark:border-slate-800 p-3.5 sm:p-4 rounded-2xl shadow-sm">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-sky-500/10 border border-sky-500/20 flex items-center justify-center text-sky-600 dark:text-sky-400 shrink-0">
                <Scale className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-sm sm:text-base font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
                  <span>Head-to-Head Comparison</span>
                  <Badge variant="blue" size="sm" className="font-mono">{comparison.course_comparison.length} Courses</Badge>
                </h2>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  {comparison.student_a.name} ({comparison.student_a.id}) vs {comparison.student_b.name} ({comparison.student_b.id})
                </p>
              </div>
            </div>

            <Button
              variant="secondary"
              size="sm"
              onClick={handleExportComparisonPdf}
              isLoading={isExporting}
              leftIcon={<Download className="w-4 h-4 text-sky-600 dark:text-sky-400" />}
              className="w-full sm:w-auto font-medium border-slate-200 dark:border-slate-700/80 hover:border-sky-500/40 shrink-0"
            >
              {isExporting ? 'Generating comparison...' : 'Export Comparison'}
            </Button>
          </div>

          {/* Side-by-Side Identity Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Student A Card */}
            <Card glass className="p-6 border-emerald-500/20 bg-emerald-500/5 space-y-4 relative overflow-hidden">
              <div className="flex items-start justify-between">
                <div>
                  <Badge variant="emerald" size="sm" className="mb-2 font-mono">
                    STUDENT A • {comparison.student_a.id}
                  </Badge>
                  <h3 className="text-xl font-extrabold text-slate-900 dark:text-slate-100 tracking-tight">
                    {comparison.student_a.name}
                  </h3>
                </div>
                <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
                  <UserCheck className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
                </div>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 text-center font-mono">
                <div className="p-2.5 bg-white dark:bg-slate-950/80 rounded-xl border border-slate-200 dark:border-slate-800/80">
                  <span className="text-[10px] text-slate-500 dark:text-slate-400 uppercase font-sans">Sem GPA</span>
                  <div className="text-lg font-black text-emerald-600 dark:text-emerald-400 mt-0.5">
                    {comparison.student_a.gpa.toFixed(2)}
                  </div>
                </div>

                <div className="p-2.5 bg-white dark:bg-slate-950/80 rounded-xl border border-slate-200 dark:border-slate-800/80">
                  <span className="text-[10px] text-slate-500 dark:text-slate-400 uppercase font-sans">Cum CGPA</span>
                  <div className="text-lg font-black text-sky-600 dark:text-sky-400 mt-0.5">
                    {comparison.student_a.cgpa.toFixed(2)}
                  </div>
                </div>

                <div className="p-2.5 bg-white dark:bg-slate-950/80 rounded-xl border border-slate-200 dark:border-slate-800/80">
                  <span className="text-[10px] text-slate-500 dark:text-slate-400 uppercase font-sans">Sem Rank</span>
                  <div className="text-lg font-black text-amber-600 dark:text-amber-400 mt-0.5">
                    #{comparison.student_a.semester_rank || 1}
                  </div>
                </div>

                <div className="p-2.5 bg-white dark:bg-slate-950/80 rounded-xl border border-slate-200 dark:border-slate-800/80">
                  <span className="text-[10px] text-slate-500 dark:text-slate-400 uppercase font-sans">Cum Rank</span>
                  <div className="text-lg font-black text-purple-600 dark:text-purple-400 mt-0.5">
                    #{comparison.student_a.cumulative_rank || 1}
                  </div>
                </div>
              </div>
            </Card>

            {/* Student B Card */}
            <Card glass className="p-6 border-sky-500/20 bg-sky-500/5 space-y-4 relative overflow-hidden">
              <div className="flex items-start justify-between">
                <div>
                  <Badge variant="blue" size="sm" className="mb-2 font-mono">
                    STUDENT B • {comparison.student_b.id}
                  </Badge>
                  <h3 className="text-xl font-extrabold text-slate-900 dark:text-slate-100 tracking-tight">
                    {comparison.student_b.name}
                  </h3>
                </div>
                <div className="w-10 h-10 rounded-xl bg-sky-500/10 border border-sky-500/20 flex items-center justify-center">
                  <UserCheck className="w-5 h-5 text-sky-600 dark:text-sky-400" />
                </div>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 text-center font-mono">
                <div className="p-2.5 bg-white dark:bg-slate-950/80 rounded-xl border border-slate-200 dark:border-slate-800/80">
                  <span className="text-[10px] text-slate-500 dark:text-slate-400 uppercase font-sans">Sem GPA</span>
                  <div className="text-lg font-black text-emerald-600 dark:text-emerald-400 mt-0.5">
                    {comparison.student_b.gpa.toFixed(2)}
                  </div>
                </div>

                <div className="p-2.5 bg-white dark:bg-slate-950/80 rounded-xl border border-slate-200 dark:border-slate-800/80">
                  <span className="text-[10px] text-slate-500 dark:text-slate-400 uppercase font-sans">Cum CGPA</span>
                  <div className="text-lg font-black text-sky-600 dark:text-sky-400 mt-0.5">
                    {comparison.student_b.cgpa.toFixed(2)}
                  </div>
                </div>

                <div className="p-2.5 bg-white dark:bg-slate-950/80 rounded-xl border border-slate-200 dark:border-slate-800/80">
                  <span className="text-[10px] text-slate-500 dark:text-slate-400 uppercase font-sans">Sem Rank</span>
                  <div className="text-lg font-black text-amber-600 dark:text-amber-400 mt-0.5">
                    #{comparison.student_b.semester_rank || 1}
                  </div>
                </div>

                <div className="p-2.5 bg-white dark:bg-slate-950/80 rounded-xl border border-slate-200 dark:border-slate-800/80">
                  <span className="text-[10px] text-slate-500 dark:text-slate-400 uppercase font-sans">Cum Rank</span>
                  <div className="text-lg font-black text-purple-600 dark:text-purple-400 mt-0.5">
                    #{comparison.student_b.cumulative_rank || 1}
                  </div>
                </div>
              </div>
            </Card>
          </div>

          {/* Comparative Metrics Ribbon */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 sm:gap-3">
            <Card className="p-3 sm:p-4 bg-white dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 text-center shadow-sm">
              <span className="text-[10px] text-slate-500 dark:text-slate-400 uppercase font-semibold block leading-tight">Semester GPA Diff</span>
              <div className={`text-base sm:text-xl font-black font-mono mt-1 ${comparison.deltas.gpa_diff >= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-sky-600 dark:text-sky-400'}`}>
                {comparison.deltas.gpa_diff > 0 ? `+${comparison.deltas.gpa_diff.toFixed(2)} (A)` : comparison.deltas.gpa_diff < 0 ? `${comparison.deltas.gpa_diff.toFixed(2)} (B)` : '0.00 (Tied)'}
              </div>
              <span className="text-[9px] sm:text-[10px] text-slate-400 block mt-0.5">GPA_A − GPA_B</span>
            </Card>

            <Card className="p-3 sm:p-4 bg-white dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 text-center shadow-sm">
              <span className="text-[10px] text-slate-500 dark:text-slate-400 uppercase font-semibold block leading-tight">Cumulative CGPA Diff</span>
              <div className={`text-base sm:text-xl font-black font-mono mt-1 ${comparison.deltas.cgpa_diff >= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-sky-600 dark:text-sky-400'}`}>
                {comparison.deltas.cgpa_diff > 0 ? `+${comparison.deltas.cgpa_diff.toFixed(2)} (A)` : comparison.deltas.cgpa_diff < 0 ? `${comparison.deltas.cgpa_diff.toFixed(2)} (B)` : '0.00 (Tied)'}
              </div>
              <span className="text-[9px] sm:text-[10px] text-slate-400 block mt-0.5">CGPA_A − CGPA_B</span>
            </Card>

            <Card className="p-3 sm:p-4 bg-white dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 text-center shadow-sm">
              <span className="text-[10px] text-slate-500 dark:text-slate-400 uppercase font-semibold block leading-tight">Average GP Diff</span>
              <div className={`text-base sm:text-xl font-black font-mono mt-1 ${comparison.deltas.average_gp_diff >= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-sky-600 dark:text-sky-400'}`}>
                {comparison.deltas.average_gp_diff > 0 ? `+${comparison.deltas.average_gp_diff.toFixed(2)} (A)` : comparison.deltas.average_gp_diff < 0 ? `${comparison.deltas.average_gp_diff.toFixed(2)} (B)` : '0.00'}
              </div>
              <span className="text-[9px] sm:text-[10px] text-slate-400 block mt-0.5">Subject Mean GP</span>
            </Card>

            <Card className="p-3 sm:p-4 bg-white dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 text-center shadow-sm">
              <span className="text-[10px] text-slate-500 dark:text-slate-400 uppercase font-semibold block leading-tight">Subject Head-to-Head</span>
              <div className="text-xs sm:text-sm font-black font-mono mt-1.5 flex flex-wrap items-center justify-center gap-1 sm:gap-1.5">
                <span className="text-emerald-600 dark:text-emerald-400">A: {comparison.subject_tally.a_better_count}</span>
                <span className="text-slate-300 dark:text-slate-600">•</span>
                <span className="text-sky-600 dark:text-sky-400">B: {comparison.subject_tally.b_better_count}</span>
                <span className="text-slate-300 dark:text-slate-600">•</span>
                <span className="text-slate-500 dark:text-slate-400">Tied: {comparison.subject_tally.tied_count}</span>
              </div>
              <span className="text-[9px] sm:text-[10px] text-slate-400 block mt-0.5">Outcome Tally</span>
            </Card>
          </div>

          {/* Subject Breakdown Delta Matrix */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <Card glass className="p-4 border-emerald-500/20 bg-emerald-500/5">
              <span className="text-xs font-bold text-emerald-600 dark:text-emerald-400 uppercase tracking-wider block mb-2">
                Student A Higher ({comparison.subject_tally.a_better_count} Subjects)
              </span>
              <div className="flex flex-wrap gap-1.5">
                {comparison.subject_tally.subjects_a_better.length > 0 ? (
                  comparison.subject_tally.subjects_a_better.map((c) => (
                    <span key={c} className="font-mono text-xs px-2 py-0.5 rounded bg-emerald-50 dark:bg-emerald-500/20 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-500/30">
                      {c}
                    </span>
                  ))
                ) : (
                  <span className="text-xs text-slate-400">None</span>
                )}
              </div>
            </Card>

            <Card glass className="p-4 border-sky-500/20 bg-sky-500/5">
              <span className="text-xs font-bold text-sky-600 dark:text-sky-400 uppercase tracking-wider block mb-2">
                Student B Higher ({comparison.subject_tally.b_better_count} Subjects)
              </span>
              <div className="flex flex-wrap gap-1.5">
                {comparison.subject_tally.subjects_b_better.length > 0 ? (
                  comparison.subject_tally.subjects_b_better.map((c) => (
                    <span key={c} className="font-mono text-xs px-2 py-0.5 rounded bg-sky-50 dark:bg-sky-500/20 text-sky-700 dark:text-sky-300 border border-sky-200 dark:border-sky-500/30">
                      {c}
                    </span>
                  ))
                ) : (
                  <span className="text-xs text-slate-400">None</span>
                )}
              </div>
            </Card>

            <Card glass className="p-4 border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/40">
              <span className="text-xs font-bold text-slate-600 dark:text-slate-400 uppercase tracking-wider block mb-2">
                Equal Performance ({comparison.subject_tally.tied_count} Subjects)
              </span>
              <div className="flex flex-wrap gap-1.5">
                {comparison.subject_tally.subjects_tied.length > 0 ? (
                  comparison.subject_tally.subjects_tied.map((c) => (
                    <span key={c} className="font-mono text-xs px-2 py-0.5 rounded bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
                      {c}
                    </span>
                  ))
                ) : (
                  <span className="text-xs text-slate-400">None</span>
                )}
              </div>
            </Card>
          </div>

          {/* Visual Head-to-Head Comparative Bar Chart */}
          <StudentComparisonChart
            studentA={comparison.student_a}
            studentB={comparison.student_b}
            deltas={comparison.deltas}
            courseComparisons={comparison.course_comparison}
          />

          {/* Subject-by-Subject Comparative Table */}
          <Card glass className="overflow-hidden p-0 border-slate-200 dark:border-slate-800 shadow-md">
            <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
              <h4 className="font-bold text-sm text-slate-900 dark:text-slate-100 flex items-center gap-2">
                <BookOpen className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                Course-by-Course Head-to-Head Comparison
              </h4>
              <span className="text-xs text-slate-500 dark:text-slate-400 font-mono">
                {comparison.course_comparison.length} Courses Analyzed
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 dark:bg-slate-950/80 text-slate-600 dark:text-slate-400 font-bold uppercase tracking-wider border-b border-slate-200 dark:border-slate-800">
                  <tr>
                    <th className="px-5 py-3.5">Course</th>
                    <th className="px-5 py-3.5 text-center">Credit</th>
                    <th className="px-5 py-3.5 text-center">Student A ({comparison.student_a.id})</th>
                    <th className="px-5 py-3.5 text-center">Student B ({comparison.student_b.id})</th>
                    <th className="px-5 py-3.5 text-center">Difference (Delta GP)</th>
                    <th className="px-5 py-3.5 text-center">Outcome</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60 font-mono text-slate-700 dark:text-slate-300">
                  {comparison.course_comparison.map((item) => {
                    const delta = item.delta_gp;
                    return (
                      <tr key={item.course_code} className="hover:bg-slate-50 dark:hover:bg-slate-800/30 transition-colors">
                        <td className="px-5 py-3.5">
                          <div className="font-bold text-slate-900 dark:text-slate-200">{item.course_code}</div>
                          <div className="text-[11px] text-slate-500 dark:text-slate-400 font-sans">{item.course_title}</div>
                        </td>
                        <td className="px-5 py-3.5 text-center text-slate-500 dark:text-slate-400">{item.credits.toFixed(1)}</td>
                        <td className="px-5 py-3.5 text-center">
                          <span className="font-bold text-emerald-600 dark:text-emerald-400 mr-1.5">
                            {item.student_a_gp !== null ? item.student_a_gp.toFixed(2) : '—'}
                          </span>
                          <Badge variant="emerald" size="sm">{item.student_a_grade || '—'}</Badge>
                        </td>
                        <td className="px-5 py-3.5 text-center">
                          <span className="font-bold text-sky-600 dark:text-sky-400 mr-1.5">
                            {item.student_b_gp !== null ? item.student_b_gp.toFixed(2) : '—'}
                          </span>
                          <Badge variant="blue" size="sm">{item.student_b_grade || '—'}</Badge>
                        </td>
                        <td className="px-5 py-3.5 text-center">
                          {delta !== null ? (
                            <span className={`font-bold ${delta > 0 ? 'text-emerald-600 dark:text-emerald-400' : delta < 0 ? 'text-sky-600 dark:text-sky-400' : 'text-slate-500 dark:text-slate-400'}`}>
                              {delta > 0 ? `+${delta.toFixed(2)}` : delta.toFixed(2)} GP
                            </span>
                          ) : (
                            '—'
                          )}
                        </td>
                        <td className="px-5 py-3.5 text-center font-sans">
                          {renderOutcomeBadge(item.better_performer)}
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
    </div>
  );
};
