import React, { useState, Suspense, lazy } from 'react';
import { Shell } from './components/layout/Shell';
import { DatasetStatusCard } from './components/upload/DatasetStatusCard';
import { ClaudeAiAssistant } from './components/upload/ClaudeAiAssistant';
import { Card } from './components/common/Card';
import { Button } from './components/common/Button';
import { Alert } from './components/common/Alert';
import { ScorecardSkeleton } from './components/common/Skeleton';
import { api } from './api/endpoints';
import { UploadSuccessData } from './types/api';

// Lazy-loaded components for optimal bundle splitting & fast initial paint
const ResultVerificationView = lazy(() =>
  import('./components/verification/ResultVerificationView').then((m) => ({ default: m.ResultVerificationView }))
);
const ResultDashboard = lazy(() =>
  import('./components/dashboard/ResultDashboard').then((m) => ({ default: m.ResultDashboard }))
);
const AnalyticsPreview = lazy(() =>
  import('./components/analytics/AnalyticsPreview').then((m) => ({ default: m.AnalyticsPreview }))
);
const ComparisonPreview = lazy(() =>
  import('./components/comparison/ComparisonPreview').then((m) => ({ default: m.ComparisonPreview }))
);
import {
  FileSpreadsheet,
  BarChart2,
  Users,
  CheckSquare,
  LayoutDashboard,
  BookOpen
} from 'lucide-react';

export type AppTabType = 'upload' | 'verify' | 'result' | 'statistics' | 'subjects' | 'comparison';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<AppTabType>('upload');
  const [isUploading, setIsUploading] = useState(false);
  const [activeSession, setActiveSession] = useState<UploadSuccessData | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Persistent Student & Comparison State (preserved across tab navigation until dataset cleared)
  const [persistentStudentId, setPersistentStudentId] = useState<string>(() => {
    try { return localStorage.getItem('result_analyzer_student_id') || ''; } catch { return ''; }
  });
  const [comparisonStudentA, setComparisonStudentA] = useState<string>(() => {
    try { return localStorage.getItem('result_analyzer_comp_a') || ''; } catch { return ''; }
  });
  const [comparisonStudentB, setComparisonStudentB] = useState<string>(() => {
    try { return localStorage.getItem('result_analyzer_comp_b') || ''; } catch { return ''; }
  });

  const handleStudentChange = (studentId: string) => {
    setPersistentStudentId(studentId);
    try { localStorage.setItem('result_analyzer_student_id', studentId); } catch { }
  };

  const handleComparisonStudentsChange = (idA: string, idB: string) => {
    setComparisonStudentA(idA);
    setComparisonStudentB(idB);
    try {
      localStorage.setItem('result_analyzer_comp_a', idA);
      localStorage.setItem('result_analyzer_comp_b', idB);
    } catch { }
  };

  const [isPurging, setIsPurging] = useState(false);

  const handleMarkdownSubmit = async (markdownText: string, filename: string = 'ai_extracted.md') => {
    setIsUploading(true);
    setErrorMessage(null);

    try {
      const res = await api.uploadMarkdownText(markdownText, filename);
      setActiveSession(res.session);
      setActiveTab('verify');
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to parse Markdown dataset.');
    } finally {
      setIsUploading(false);
    }
  };

  const handleClearSession = async () => {
    if (activeSession) {
      setIsPurging(true);
      try {
        await api.purgeSession(activeSession.id);
      } catch (err) {
        console.error("Session purge error", err);
      } finally {
        setIsPurging(false);
      }
    }
    setActiveSession(null);
    setActiveTab('upload');
    setErrorMessage(null);
    setPersistentStudentId('');
    setComparisonStudentA('');
    setComparisonStudentB('');
    try {
      localStorage.removeItem('result_analyzer_student_id');
      localStorage.removeItem('result_analyzer_comp_a');
      localStorage.removeItem('result_analyzer_comp_b');
    } catch { }
  };

  const handleVerificationConfirmed = async () => {
    if (activeSession) {
      const updated = await api.getSessionStatus(activeSession.id);
      setActiveSession(updated);
    }
    setActiveTab('result');
  };

  const handleStartComparison = (idA: string, idB: string) => {
    handleComparisonStudentsChange(idA, idB);
    setActiveTab('comparison');
  };

  const navigationTabs = (
    <nav aria-label="Main User Flow Navigation" className="flex items-center gap-1 sm:gap-2 border-b border-slate-200 dark:border-slate-800/80 pt-1 pb-3 px-1 mb-6 sm:mb-8 overflow-x-auto scrollbar-none">
      <Button
        variant={activeTab === 'upload' ? 'primary' : 'ghost'}
        size="sm"
        onClick={() => setActiveTab('upload')}
        leftIcon={<FileSpreadsheet className="w-4 h-4 shrink-0" />}
        className="shrink-0 text-xs sm:text-sm px-2 sm:px-3"
      >
        <span className="hidden sm:inline">1. Upload &amp; Dataset</span>
        <span className="sm:hidden">1</span>
      </Button>

      <Button
        variant={activeTab === 'verify' ? 'primary' : 'ghost'}
        size="sm"
        onClick={() => setActiveTab('verify')}
        disabled={!activeSession}
        leftIcon={<CheckSquare className="w-4 h-4 shrink-0" />}
        className="shrink-0 text-xs sm:text-sm px-2 sm:px-3"
      >
        <span className="hidden sm:inline">2. Tabulation Matrix</span>
        <span className="sm:hidden">2</span>
      </Button>

      <Button
        variant={activeTab === 'result' ? 'primary' : 'ghost'}
        size="sm"
        onClick={() => setActiveTab('result')}
        disabled={!activeSession}
        leftIcon={<LayoutDashboard className="w-4 h-4 shrink-0" />}
        className="shrink-0 text-xs sm:text-sm px-2 sm:px-3"
      >
        <span className="hidden sm:inline">3. Student Result</span>
        <span className="sm:hidden">3</span>
      </Button>

      <Button
        variant={activeTab === 'statistics' ? 'primary' : 'ghost'}
        size="sm"
        onClick={() => setActiveTab('statistics')}
        disabled={!activeSession}
        leftIcon={<BarChart2 className="w-4 h-4 shrink-0" />}
        className="shrink-0 text-xs sm:text-sm px-2 sm:px-3"
      >
        <span className="hidden sm:inline">4. Class Statistics</span>
        <span className="sm:hidden">4</span>
      </Button>

      <Button
        variant={activeTab === 'subjects' ? 'primary' : 'ghost'}
        size="sm"
        onClick={() => setActiveTab('subjects')}
        disabled={!activeSession}
        leftIcon={<BookOpen className="w-4 h-4 shrink-0" />}
        className="shrink-0 text-xs sm:text-sm px-2 sm:px-3"
      >
        <span className="hidden sm:inline">5. Subject Analysis</span>
        <span className="sm:hidden">5</span>
      </Button>

      <Button
        variant={activeTab === 'comparison' ? 'primary' : 'ghost'}
        size="sm"
        onClick={() => setActiveTab('comparison')}
        disabled={!activeSession}
        leftIcon={<Users className="w-4 h-4 shrink-0" />}
        className="shrink-0 text-xs sm:text-sm px-2 sm:px-3"
      >
        <span className="hidden sm:inline">6. Compare Students</span>
        <span className="sm:hidden">6</span>
      </Button>
    </nav>
  );

  return (
    <Shell
      hasActiveSession={!!activeSession}
      sessionId={activeSession?.id}
      onClearSession={handleClearSession}
    >
      {errorMessage && (
        <Alert
          type="error"
          title="Notice"
          message={errorMessage}
          onClose={() => setErrorMessage(null)}
          className="mb-6"
        />
      )}

      {/* Primary Linear Navigation Flow Bar */}
      {navigationTabs}

      {/* Tab 1: Upload & Dataset */}
      {activeTab === 'upload' && (
        <div className="space-y-8 animate-in fade-in duration-200">
          {/* User-Centric Value Prop Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            <Card glass className="p-5">
              <div className="w-9 h-9 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center mb-3">
                <LayoutDashboard className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
              </div>
              <h4 className="font-bold text-sm text-slate-900 dark:text-slate-100 mb-1.5">Instant Student Scorecard</h4>
              <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                Enter your student ID to immediately inspect your semester marks, GPA, overall CGPA, and batch ranking.
              </p>
            </Card>

            <Card glass className="p-5">
              <div className="w-9 h-9 rounded-xl bg-sky-500/10 border border-sky-500/20 flex items-center justify-center mb-3">
                <BarChart2 className="w-4 h-4 text-sky-600 dark:text-sky-400" />
              </div>
              <h4 className="font-bold text-sm text-slate-900 dark:text-slate-100 mb-1.5">Class Cohort Analytics</h4>
              <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                Explore class-wide performance metrics, GPA distributions, course toppers, and deterministic ranking percentiles.
              </p>
            </Card>

            <Card glass className="p-5">
              <div className="w-9 h-9 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center mb-3">
                <Users className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
              </div>
              <h4 className="font-bold text-sm text-slate-900 dark:text-slate-100 mb-1.5">Head-to-Head Comparison</h4>
              <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                Select any two students to compare grades course-by-course with side-by-side differentials and charts.
              </p>
            </Card>
          </div>

          {activeSession ? (
            <div className="space-y-6">
              <DatasetStatusCard
                session={activeSession}
                onProceedToVerification={() => setActiveTab('verify')}
                onProceedToScorecard={() => setActiveTab('result')}
                onPurgeDataset={handleClearSession}
                isPurging={isPurging}
              />
            </div>
          ) : (
            <div className="space-y-8">
              <ClaudeAiAssistant
                onMarkdownSubmit={handleMarkdownSubmit}
                isProcessing={isUploading}
              />
            </div>
          )}
        </div>
      )}

      {/* Suspense Boundary for Lazy-Loaded Views */}
      <Suspense fallback={<ScorecardSkeleton />}>
        {/* Tab 2: Tabulation Sheet / Verify Matrix */}
        {activeTab === 'verify' && activeSession && (
          <ResultVerificationView
            sessionId={activeSession.id}
            onVerificationConfirmed={handleVerificationConfirmed}
          />
        )}

        {/* Tab 3: Student Result Dashboard */}
        {activeTab === 'result' && (
          <ResultDashboard
            sessionId={activeSession?.id}
            initialStudentId={persistentStudentId}
            onStudentChange={handleStudentChange}
            onNavigateToTab={(tab: string) => {
              if (tab === 'analytics' || tab === 'statistics') setActiveTab('statistics');
              else if (tab === 'subjects') setActiveTab('subjects');
              else if (tab === 'comparison') setActiveTab('comparison');
              else if (tab === 'verify') setActiveTab('verify');
              else setActiveTab('result');
            }}
            onCompareStudents={handleStartComparison}
          />
        )}

        {/* Tab 4: Class Statistics */}
        {activeTab === 'statistics' && (
          <AnalyticsPreview
            sessionId={activeSession?.id}
            initialStudentId={persistentStudentId}
            initialView="class"
          />
        )}

        {/* Tab 5: Subject Analysis */}
        {activeTab === 'subjects' && (
          <AnalyticsPreview
            sessionId={activeSession?.id}
            initialStudentId={persistentStudentId}
            initialView="subjects"
          />
        )}

        {/* Tab 6: 2-Student Comparison */}
        {activeTab === 'comparison' && (
          <ComparisonPreview
            sessionId={activeSession?.id}
            defaultStudentA={comparisonStudentA}
            defaultStudentB={comparisonStudentB}
            onStudentsChange={handleComparisonStudentsChange}
          />
        )}
      </Suspense>
    </Shell>
  );
};

export default App;
