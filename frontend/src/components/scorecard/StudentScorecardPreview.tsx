import React, { useState, useEffect } from 'react';
import { Card } from '../common/Card';
import { Badge } from '../common/Badge';
import { Button } from '../common/Button';
import { Alert } from '../common/Alert';
import { api } from '../../api/endpoints';
import { StudentRecord } from '../../types/student';
import { getLetterGradeFromGP } from '../../utils/gradeUtils';
import { 
  Award, 
  BookOpen, 
  CheckCircle, 
  Trophy, 
  User, 
  Search, 
  GraduationCap,
  Layers
} from 'lucide-react';

export interface StudentScorecardPreviewProps {
  sessionId?: string;
  initialStudentId?: string;
}

export const StudentScorecardPreview: React.FC<StudentScorecardPreviewProps> = ({
  sessionId,
  initialStudentId = '',
}) => {
  const [searchInput, setSearchInput] = useState(initialStudentId);
  const [student, setStudent] = useState<StudentRecord | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Perform Lookup
  const fetchStudentScorecard = async (idToSearch: string) => {
    const cleanId = idToSearch.trim();
    if (!cleanId) {
      setErrorMessage('Please enter a Student ID to lookup.');
      setStudent(null);
      return;
    }

    if (!sessionId) {
      setErrorMessage('No active result sheet dataset found. Please upload and verify a dataset first.');
      setStudent(null);
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);

    try {
      const data = await api.getStudentScorecard(sessionId, cleanId);
      setStudent(data);
    } catch (err: any) {
      setStudent(null);
      if (err.response?.status === 404 || err.code === 'ERR_BAD_REQUEST') {
        setErrorMessage(
          err.response?.data?.message ||
          `Student ID "${cleanId}" was not found in the currently verified dataset.`
        );
      } else {
        setErrorMessage(err.message || `Failed to retrieve scorecard for Student ID "${cleanId}".`);
      }
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (sessionId && initialStudentId) {
      setSearchInput(initialStudentId);
      fetchStudentScorecard(initialStudentId);
    }
  }, [sessionId, initialStudentId]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchStudentScorecard(searchInput);
  };

  const getGradeBadgeVariant = (grade: string) => {
    const g = grade.toUpperCase();
    if (g.startsWith('A')) return 'emerald';
    if (g.startsWith('B') || g.startsWith('C')) return 'blue';
    if (g.startsWith('D')) return 'amber';
    return 'rose';
  };

  return (
    <div className="space-y-6">
      {/* Search Input Bar */}
      <Card className="p-4 bg-slate-900/80 border-slate-800">
        <form onSubmit={handleSearchSubmit} className="flex flex-col sm:flex-row items-center gap-3">
          <div className="relative flex-1 w-full">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Enter Student ID (e.g. B220305009)..."
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700/80 rounded-xl pl-10 pr-4 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-emerald-500 font-mono uppercase"
            />
          </div>

          <Button
            type="submit"
            size="md"
            isLoading={isLoading}
            leftIcon={<Search className="w-4 h-4" />}
            className="w-full sm:w-auto font-semibold"
          >
            Search Student
          </Button>
        </form>
      </Card>

      {/* Error Message */}
      {errorMessage && (
        <Alert
          type="error"
          title="Student Lookup Notice"
          message={errorMessage}
          onClose={() => setErrorMessage(null)}
        />
      )}

      {/* Empty State when no search executed yet */}
      {!isLoading && !student && !errorMessage && (
        <Card glass className="p-12 text-center space-y-3 border-slate-800">
          <div className="w-12 h-12 rounded-2xl bg-slate-800 flex items-center justify-center mx-auto text-slate-400">
            <GraduationCap className="w-6 h-6" />
          </div>
          <h4 className="font-bold text-slate-200 text-base">Individual Student Scorecard</h4>
          <p className="text-xs text-slate-400 max-w-md mx-auto leading-relaxed">
            Enter a Student ID above to search and display their verified semester GPA, cumulative CGPA, course grades, and cohort ranks.
          </p>
        </Card>
      )}

      {/* Student Scorecard Display */}
      {student && (
        <div className="space-y-6 animate-in fade-in zoom-in-95 duration-200">
          {/* Header Card */}
          <Card glass className="p-6 sm:p-8 border-slate-800 relative overflow-hidden">
            <div className="absolute top-0 right-0 w-64 h-64 bg-emerald-500/5 rounded-full blur-3xl pointer-events-none" />

            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
              <div className="flex items-center gap-4">
                <div className="w-16 h-16 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center flex-shrink-0 shadow-lg shadow-emerald-950/40">
                  <User className="w-8 h-8 text-emerald-400" />
                </div>
                <div>
                  <div className="flex flex-wrap items-center gap-2 mb-1">
                    <h2 className="text-xl sm:text-2xl font-extrabold text-slate-100 tracking-tight">
                      {student.student_name}
                    </h2>
                    <Badge variant="emerald" size="sm">Verified Result</Badge>
                  </div>
                  <div className="flex flex-wrap items-center gap-3 text-xs text-slate-400 font-mono">
                    <span className="text-emerald-400 font-bold">ID: {student.student_id}</span>
                    {student.serial_no && (
                      <>
                        <span>•</span>
                        <span>Serial #{student.serial_no}</span>
                      </>
                    )}
                    {student.metadata?.semester && (
                      <>
                        <span>•</span>
                        <span>{student.metadata.semester}</span>
                      </>
                    )}
                  </div>
                </div>
              </div>

              {/* GPA Display Badges */}
              <div className="flex items-center gap-4 bg-slate-950/60 p-3 rounded-2xl border border-slate-800/80">
                <div className="text-right px-2">
                  <div className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold">Semester GPA</div>
                  <div className="text-2xl font-black text-emerald-400 font-mono flex items-baseline justify-end gap-1.5">
                    <span>{student.semester_result.gpa.toFixed(2)}</span>
                    <span className="text-xs font-bold font-sans text-emerald-300 bg-emerald-500/20 px-1.5 py-0.5 rounded border border-emerald-500/30">
                      {getLetterGradeFromGP(student.semester_result.gpa)}
                    </span>
                  </div>
                </div>
                <div className="w-px h-10 bg-slate-800" />
                <div className="text-right px-2">
                  <div className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold">Cumulative CGPA</div>
                  <div className="text-2xl font-black text-sky-400 font-mono flex items-baseline justify-end gap-1.5">
                    <span>{student.cumulative_result.cgpa.toFixed(2)}</span>
                    <span className="text-xs font-bold font-sans text-sky-300 bg-sky-500/20 px-1.5 py-0.5 rounded border border-sky-500/30">
                      {getLetterGradeFromGP(student.cumulative_result.cgpa)}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </Card>

          {/* Metric Grid Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card className="p-5 bg-slate-900/60 border-slate-800">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-slate-400 font-medium">Semester Standing</span>
                <Trophy className="w-4 h-4 text-amber-400" />
              </div>
              <div className="text-2xl font-bold text-slate-100 font-mono">
                #{student.semester_result.semester_rank}
                <span className="text-xs text-emerald-400 font-sans ml-2 font-normal">
                  (Top {Math.max(1, 100 - student.semester_result.semester_percentile).toFixed(0)}%)
                </span>
              </div>
              <span className="text-[11px] text-slate-500 mt-1 block">Based on semester GPA</span>
            </Card>

            <Card className="p-5 bg-slate-900/60 border-slate-800">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-slate-400 font-medium">Cumulative Standing</span>
                <Award className="w-4 h-4 text-sky-400" />
              </div>
              <div className="text-2xl font-bold text-slate-100 font-mono">
                #{student.cumulative_result.cumulative_rank}
              </div>
              <span className="text-[11px] text-slate-500 mt-1 block">Overall cohort rank</span>
            </Card>

            <Card className="p-5 bg-slate-900/60 border-slate-800">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-slate-400 font-medium">Semester Credits</span>
                <BookOpen className="w-4 h-4 text-sky-400" />
              </div>
              <div className="text-2xl font-bold text-slate-100 font-mono">
                {student.semester_result.credits_earned.toFixed(1)} / {student.semester_result.credits_attempted.toFixed(1)}
              </div>
              <span className="text-[11px] text-slate-500 mt-1 block">Earned vs Attempted</span>
            </Card>

            <Card className="p-5 bg-slate-900/60 border-slate-800">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-slate-400 font-medium">Cumulative Credits</span>
                <Layers className="w-4 h-4 text-emerald-400" />
              </div>
              <div className="text-2xl font-bold text-slate-100 font-mono">
                {student.cumulative_result.total_credits_earned.toFixed(1)}
              </div>
              <span className="text-[11px] text-slate-500 mt-1 block">Total degree progress</span>
            </Card>
          </div>

          {/* Detailed Course Breakdown Table */}
          <Card className="overflow-hidden border-slate-800 bg-slate-900/60 shadow-xl">
            <div className="p-4 border-b border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <BookOpen className="w-4 h-4 text-emerald-400" />
                <h4 className="font-bold text-sm text-slate-200">Complete Course Grade Breakdown</h4>
              </div>
              <div className="flex items-center gap-2 text-xs text-emerald-400 font-medium">
                <CheckCircle className="w-3.5 h-3.5" />
                <span>Verified Academic Markings</span>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-950/80 text-slate-400 font-bold uppercase tracking-wider border-b border-slate-800">
                  <tr>
                    <th className="px-5 py-3">Course Code</th>
                    <th className="px-5 py-3">Course Title</th>
                    <th className="px-5 py-3 text-center">Credits</th>
                    <th className="px-5 py-3 text-center">Grade Point</th>
                    <th className="px-5 py-3 text-center">Letter Grade</th>
                    <th className="px-5 py-3 text-center">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono text-slate-300">
                  {student.course_grades.map((cg) => (
                    <tr key={cg.course_code} className="hover:bg-slate-800/30 transition-colors">
                      <td className="px-5 py-3.5 font-bold text-emerald-400">
                        {cg.course_code}
                      </td>
                      <td className="px-5 py-3.5 font-sans font-medium text-slate-200">
                        {cg.course_title}
                      </td>
                      <td className="px-5 py-3.5 text-center text-slate-400">
                        {cg.credits.toFixed(1)}
                      </td>
                      <td className="px-5 py-3.5 text-center font-bold text-slate-100">
                        {cg.grade_point !== null ? cg.grade_point.toFixed(2) : '—'}
                      </td>
                      <td className="px-5 py-3.5 text-center">
                        <Badge variant={getGradeBadgeVariant(cg.letter_grade)} size="sm">
                          {cg.letter_grade || '—'}
                        </Badge>
                      </td>
                      <td className="px-5 py-3.5 text-center font-sans">
                        <Badge variant="emerald" size="sm" className="gap-1">
                          <CheckCircle className="w-3 h-3" />
                          VALID
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
};
