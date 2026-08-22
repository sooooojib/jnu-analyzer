import React, { useState, useEffect, useMemo, useRef } from 'react';
import { Card } from '../common/Card';
import { Button } from '../common/Button';
import { Badge } from '../common/Badge';
import { Alert } from '../common/Alert';
import { api } from '../../api/endpoints';
import { 
  VerificationDataResponse, 
  VerificationRowItem 
} from '../../types/verification';
import {
  CheckCircle2,
  Search,
  Filter,
  Check,
  Edit2,
  Users,
  BookOpen,
  ChevronLeft,
  ChevronRight,
  Info,
  ShieldCheck,
  Eye,
  X
} from 'lucide-react';

interface ResultVerificationViewProps {
  sessionId: string;
  onVerificationConfirmed: () => void;
}

export const ResultVerificationView: React.FC<ResultVerificationViewProps> = ({
  sessionId,
  onVerificationConfirmed,
}) => {
  const [data, setData] = useState<VerificationDataResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isConfirming, setIsConfirming] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successNotice, setSuccessNotice] = useState<string | null>(null);

  // Search, Filter & Pagination State
  const [searchQuery, setSearchQuery] = useState('');
  const [courseFilter, setCourseFilter] = useState<string>('ALL');
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(15);

  // Inline Editing State
  const [editingCellKey, setEditingCellKey] = useState<string | null>(null);
  const [editValue, setEditValue] = useState<string>('');
  const editInputRef = useRef<HTMLInputElement | null>(null);

  // Audit Details Modal State
  const [activeAuditRow, setActiveAuditRow] = useState<VerificationRowItem | null>(null);

  // 1. Fetch Verification Data on Mount
  const fetchData = async () => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const resp = await api.getVerificationData(sessionId);
      setData(resp);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to load extraction verification data.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [sessionId]);

  // Focus input when inline edit begins
  useEffect(() => {
    if (editingCellKey && editInputRef.current) {
      editInputRef.current.focus();
      editInputRef.current.select();
    }
  }, [editingCellKey]);

  // 2. Filter & Search Logic
  const filteredRows = useMemo(() => {
    if (!data?.rows) return [];
    return data.rows.filter((row) => {
      const q = searchQuery.trim().toLowerCase();
      const matchesSearch =
        !q ||
        row.student_id.toLowerCase().includes(q) ||
        row.student_name.toLowerCase().includes(q) ||
        row.course_code.toLowerCase().includes(q);

      const matchesCourse =
        courseFilter === 'ALL' || row.course_code === courseFilter;

      return matchesSearch && matchesCourse;
    });
  }, [data?.rows, searchQuery, courseFilter]);

  // Pagination Slice
  const totalPages = Math.max(1, Math.ceil(filteredRows.length / pageSize));
  const paginatedRows = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return filteredRows.slice(start, start + pageSize);
  }, [filteredRows, currentPage, pageSize]);

  // 3. Handle Inline Cell Edit Start
  const startEditing = (row: VerificationRowItem, fieldName: 'grade_point' | 'letter_grade' | 'student_name' | 'student_id') => {
    const key = `${row.student_id}_${row.course_code}_${fieldName}`;
    setEditingCellKey(key);

    if (fieldName === 'grade_point') {
      setEditValue(row.grade_point !== null ? String(row.grade_point) : '');
    } else if (fieldName === 'letter_grade') {
      setEditValue(row.letter_grade || '');
    } else if (fieldName === 'student_name') {
      setEditValue(row.student_name || '');
    } else if (fieldName === 'student_id') {
      setEditValue(row.student_id || '');
    }
  };

  // 4. Save Inline Cell Edit
  const saveCellEdit = async (
    row: VerificationRowItem,
    fieldName: 'grade_point' | 'letter_grade' | 'student_name' | 'student_id'
  ) => {
    setEditingCellKey(null);

    let parsedVal: any = editValue.trim();
    if (fieldName === 'grade_point') {
      parsedVal = editValue.trim() === '' ? null : parseFloat(editValue);
      if (parsedVal !== null && isNaN(parsedVal)) {
        setErrorMessage('Grade point must be a valid number.');
        return;
      }
    }

    try {
      const updatedResp = await api.updateVerificationCell(sessionId, {
        student_id: row.student_id,
        course_code: row.course_code,
        field_name: fieldName,
        new_value: parsedVal,
      });
      setData(updatedResp);
      setSuccessNotice(`Updated ${fieldName} for student ${row.student_id}`);
      setTimeout(() => setSuccessNotice(null), 3000);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to save cell edit.');
    }
  };

  // 5. Confirm Verification & Unlock Full Analytics
  const handleConfirmVerification = async () => {
    setIsConfirming(true);
    setErrorMessage(null);
    try {
      await api.confirmVerification(sessionId);
      setSuccessNotice('Dataset verified! Unlocking analysis engine...');
      setTimeout(() => {
        onVerificationConfirmed();
      }, 800);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to confirm verification.');
    } finally {
      setIsConfirming(false);
    }
  };

  if (isLoading) {
    return (
      <Card glass className="p-12 text-center space-y-4">
        <div className="w-12 h-12 border-3 border-emerald-500/30 border-t-emerald-500 rounded-full animate-spin mx-auto" />
        <h3 className="text-lg font-bold text-slate-200">Loading Result Verification Matrix...</h3>
        <p className="text-sm text-slate-400">Assembling spatial token grids and tabulation sheet records.</p>
      </Card>
    );
  }

  const summary = data?.summary || {
    total_students: 0,
    total_courses: 0,
  };

  const isVerified = data?.status === 'VERIFIED' || data?.status === 'COMPLETED';

  return (
    <div className="space-y-6">
      {/* Top Banner & Alert Notices */}
      {errorMessage && (
        <Alert
          type="error"
          title="Verification Error"
          message={errorMessage}
          onClose={() => setErrorMessage(null)}
        />
      )}

      {successNotice && (
        <Alert
          type="success"
          title="Update Successful"
          message={successNotice}
          onClose={() => setSuccessNotice(null)}
        />
      )}

      {/* Overview Counters Ribbon */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <Card glass className="p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-500 dark:text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Total Students</span>
            <Users className="w-4 h-4 text-emerald-500 dark:text-emerald-400" />
          </div>
          <div className="text-2xl font-black text-slate-900 dark:text-slate-100 mt-2">{summary.total_students}</div>
          <span className="text-[11px] text-slate-500">Detected in sheet</span>
        </Card>

        <Card glass className="p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-500 dark:text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Total Courses</span>
            <BookOpen className="w-4 h-4 text-sky-500 dark:text-sky-400" />
          </div>
          <div className="text-2xl font-black text-slate-900 dark:text-slate-100 mt-2">{summary.total_courses}</div>
          <span className="text-[11px] text-slate-500">Course columns found</span>
        </Card>

        <Card glass className="p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-500 dark:text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Total Records</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-500 dark:text-emerald-400" />
          </div>
          <div className="text-2xl font-black text-slate-900 dark:text-slate-100 mt-2">{data?.rows?.length || 0}</div>
          <span className="text-[11px] text-slate-500">Grade entries populated</span>
        </Card>
      </div>

      {/* Action Header & Verification Controls */}
      <Card glass className="p-5 flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100">Interactive Result Matrix</h2>
            <Badge variant={isVerified ? "emerald" : "amber"}>
              {isVerified ? "Verified Dataset" : "Verification Required"}
            </Badge>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Click any GP, Letter Grade, or Student ID to make corrections. Calculations re-compute instantly.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3 w-full lg:w-auto">
          <Button
            variant={isVerified ? "secondary" : "primary"}
            size="md"
            onClick={handleConfirmVerification}
            isLoading={isConfirming}
            leftIcon={isVerified ? <Check className="w-4 h-4 text-emerald-400" /> : <ShieldCheck className="w-4 h-4" />}
            className="shadow-lg shadow-emerald-950/50"
          >
            {isVerified ? "Data Verified (Re-confirm)" : "Confirm & Unlock Full Analytics"}
          </Button>
        </div>
      </Card>

      {/* Filters & Search Toolbar */}
      <Card className="p-4 bg-white dark:bg-slate-900/80 border border-slate-200 dark:border-slate-800 flex flex-col md:flex-row items-center gap-3">
        {/* Search */}
        <div className="relative flex-1 w-full">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by Student ID, Name, or Course Code..."
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value);
              setCurrentPage(1);
            }}
            className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl pl-10 pr-4 py-2 text-sm text-slate-900 dark:text-slate-100 placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:border-emerald-500 transition-colors"
          />
        </div>

        {/* Course Filter */}
        <div className="flex items-center gap-2 w-full md:w-auto">
          <Filter className="w-4 h-4 text-slate-400 hidden sm:block" />
          <select
            value={courseFilter}
            onChange={(e) => {
              setCourseFilter(e.target.value);
              setCurrentPage(1);
            }}
            aria-label="Filter by course"
            className="bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-900 dark:text-slate-200 focus:outline-none focus:border-emerald-500 w-full sm:w-auto"
          >
            <option value="ALL">All Courses</option>
            {data?.courses?.map((c) => (
              <option key={c.course_code} value={c.course_code}>
                {c.course_code} ({c.credit_hours} cr)
              </option>
            ))}
          </select>
        </div>
      </Card>

      {/* Main Verification Grid */}
      <Card glass className="overflow-hidden border-slate-200 dark:border-slate-800">
        <div className="table-scroll-wrapper overflow-x-auto max-h-[600px] relative">
          <table className="w-full text-left border-collapse text-xs min-w-[650px] sm:min-w-full">
            <thead className="sticky top-0 z-20 bg-slate-100 dark:bg-slate-950/95 backdrop-blur-md border-b border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400 font-bold uppercase tracking-wider">
              <tr>
                <th className="py-3.5 px-4">Student ID</th>
                <th className="py-3.5 px-4">Student Name</th>
                <th className="py-3.5 px-4">Course</th>
                <th className="py-3.5 px-3 text-center">Credit</th>
                <th className="py-3.5 px-3 text-center">GP</th>
                <th className="py-3.5 px-3 text-center">Letter Grade</th>
                <th className="py-3.5 px-4 text-right">Audit</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60 font-mono">
              {paginatedRows.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-slate-500 font-sans">
                    No results match the selected filter criteria.
                  </td>
                </tr>
              ) : (
                paginatedRows.map((row) => {
                  const idKey = `${row.student_id}_${row.course_code}_student_id`;
                  const nameKey = `${row.student_id}_${row.course_code}_student_name`;
                  const gpKey = `${row.student_id}_${row.course_code}_grade_point`;
                  const lgKey = `${row.student_id}_${row.course_code}_letter_grade`;

                  return (
                    <tr
                      key={`${row.student_id}_${row.course_code}`}
                      className="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors"
                    >
                      {/* Student ID */}
                      <td className="py-2.5 px-4 font-bold text-slate-900 dark:text-slate-100">
                        {editingCellKey === idKey ? (
                          <input
                            ref={editInputRef}
                            type="text"
                            value={editValue}
                            onChange={(e) => setEditValue(e.target.value)}
                            onBlur={() => saveCellEdit(row, 'student_id')}
                            onKeyDown={(e) => {
                              if (e.key === 'Enter') saveCellEdit(row, 'student_id');
                              if (e.key === 'Escape') setEditingCellKey(null);
                            }}
                            className="bg-slate-50 dark:bg-slate-950 border border-emerald-500 rounded px-2 py-1 text-xs text-slate-900 dark:text-slate-100 font-mono w-28 focus:outline-none"
                          />
                        ) : (
                          <div
                            onClick={() => startEditing(row, 'student_id')}
                            className="cursor-pointer group flex items-center gap-1.5 hover:text-emerald-500 dark:hover:text-emerald-400"
                            title="Click to edit Student ID"
                          >
                            <span>{row.student_id}</span>
                            <Edit2 className="w-2.5 h-2.5 text-slate-400 opacity-0 group-hover:opacity-100" />
                          </div>
                        )}
                      </td>

                      {/* Student Name */}
                      <td className="py-2.5 px-4 font-sans text-slate-700 dark:text-slate-300">
                        {editingCellKey === nameKey ? (
                          <input
                            ref={editInputRef}
                            type="text"
                            value={editValue}
                            onChange={(e) => setEditValue(e.target.value)}
                            onBlur={() => saveCellEdit(row, 'student_name')}
                            onKeyDown={(e) => {
                              if (e.key === 'Enter') saveCellEdit(row, 'student_name');
                              if (e.key === 'Escape') setEditingCellKey(null);
                            }}
                            className="bg-slate-50 dark:bg-slate-950 border border-emerald-500 rounded px-2 py-1 text-xs text-slate-900 dark:text-slate-100 font-sans w-48 focus:outline-none"
                          />
                        ) : (
                          <div
                            onClick={() => startEditing(row, 'student_name')}
                            className="cursor-pointer group flex items-center gap-1.5 hover:text-emerald-500 dark:hover:text-emerald-400"
                            title="Click to edit Student Name"
                          >
                            <span className="truncate max-w-xs">{row.student_name}</span>
                            <Edit2 className="w-2.5 h-2.5 text-slate-400 opacity-0 group-hover:opacity-100" />
                          </div>
                        )}
                      </td>

                      {/* Course Code */}
                      <td className="py-2.5 px-4 text-slate-700 dark:text-slate-300 font-bold">
                        <span className="bg-slate-100 dark:bg-slate-800/80 px-2 py-0.5 rounded text-sky-600 dark:text-sky-400 border border-slate-200 dark:border-slate-700/60">
                          {row.course_code}
                        </span>
                      </td>

                      {/* Credit */}
                      <td className="py-2.5 px-3 text-center text-slate-500 dark:text-slate-400">
                        {Number(row.credit_hours).toFixed(2)}
                      </td>

                      {/* GP (Grade Point) */}
                      <td className="py-2.5 px-3 text-center">
                        {editingCellKey === gpKey ? (
                          <input
                            ref={editInputRef}
                            type="text"
                            value={editValue}
                            onChange={(e) => setEditValue(e.target.value)}
                            onBlur={() => saveCellEdit(row, 'grade_point')}
                            onKeyDown={(e) => {
                              if (e.key === 'Enter') saveCellEdit(row, 'grade_point');
                              if (e.key === 'Escape') setEditingCellKey(null);
                            }}
                            className="bg-slate-50 dark:bg-slate-950 border border-emerald-500 rounded px-2 py-1 text-xs text-center text-slate-900 dark:text-slate-100 font-mono w-16 focus:outline-none"
                          />
                        ) : (
                          <div
                            onClick={() => startEditing(row, 'grade_point')}
                            className="cursor-pointer group inline-flex items-center justify-center gap-1 font-bold text-slate-900 dark:text-slate-100 hover:text-emerald-500 dark:hover:text-emerald-400"
                            title="Click to edit Grade Point"
                          >
                            <span>{row.grade_point !== null ? Number(row.grade_point).toFixed(2) : '—'}</span>
                            <Edit2 className="w-2.5 h-2.5 text-slate-400 opacity-0 group-hover:opacity-100" />
                          </div>
                        )}
                      </td>

                      {/* Letter Grade */}
                      <td className="py-2.5 px-3 text-center">
                        {editingCellKey === lgKey ? (
                          <input
                            ref={editInputRef}
                            type="text"
                            value={editValue}
                            onChange={(e) => setEditValue(e.target.value)}
                            onBlur={() => saveCellEdit(row, 'letter_grade')}
                            onKeyDown={(e) => {
                              if (e.key === 'Enter') saveCellEdit(row, 'letter_grade');
                              if (e.key === 'Escape') setEditingCellKey(null);
                            }}
                            className="bg-slate-50 dark:bg-slate-950 border border-emerald-500 rounded px-2 py-1 text-xs text-center text-slate-900 dark:text-slate-100 font-mono w-14 focus:outline-none"
                          />
                        ) : (
                          <div
                            onClick={() => startEditing(row, 'letter_grade')}
                            className="cursor-pointer group inline-flex items-center justify-center gap-1 font-extrabold text-amber-500 dark:text-amber-400 hover:text-emerald-500 dark:hover:text-emerald-400"
                            title="Click to edit Letter Grade"
                          >
                            <span>{row.letter_grade || '—'}</span>
                            <Edit2 className="w-2.5 h-2.5 text-slate-400 opacity-0 group-hover:opacity-100" />
                          </div>
                        )}
                      </td>

                      {/* Audit Details Trigger */}
                      <td className="py-2.5 px-4 text-right">
                        <button
                          onClick={() => setActiveAuditRow(row)}
                          className="text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 transition-colors p-1"
                          title="View cell diagnostic and repair log"
                        >
                          <Eye className="w-3.5 h-3.5" />
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Footer */}
        <div className="p-3 bg-slate-50 dark:bg-slate-950/80 border-t border-slate-200 dark:border-slate-800/80 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-slate-500 dark:text-slate-400 font-sans">
          <div className="flex items-center gap-2">
            <span>Showing {filteredRows.length > 0 ? (currentPage - 1) * pageSize + 1 : 0} to {Math.min(currentPage * pageSize, filteredRows.length)} of {filteredRows.length} rows</span>
            <span className="text-slate-300 dark:text-slate-600">|</span>
            <select
              value={pageSize}
              onChange={(e) => {
                setPageSize(Number(e.target.value));
                setCurrentPage(1);
              }}
              aria-label="Rows per page"
              className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded px-2 py-1 text-xs text-slate-700 dark:text-slate-300 focus:outline-none"
            >
              <option value={15}>15 per page</option>
              <option value={30}>30 per page</option>
              <option value={50}>50 per page</option>
              <option value={100}>100 per page</option>
            </select>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="secondary"
              size="sm"
              disabled={currentPage === 1}
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              className="px-2 py-1"
            >
              <ChevronLeft className="w-3.5 h-3.5" />
            </Button>
            <span>Page {currentPage} of {totalPages}</span>
            <Button
              variant="secondary"
              size="sm"
              disabled={currentPage === totalPages}
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              className="px-2 py-1"
            >
              <ChevronRight className="w-3.5 h-3.5" />
            </Button>
          </div>
        </div>
      </Card>

      {/* Audit Detail Drawer Modal */}
      {activeAuditRow && (
        <div className="modal-overlay-backdrop animate-in fade-in duration-150">
          <div className="w-full max-w-lg p-6 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-2xl rounded-2xl space-y-4 text-slate-900 dark:text-slate-100">
            <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <Info className="w-5 h-5 text-sky-500 dark:text-sky-400" />
                <h4 className="font-bold text-slate-900 dark:text-slate-100 text-sm">
                  Field Diagnostic & Audit Trail
                </h4>
              </div>
              <button 
                onClick={() => setActiveAuditRow(null)}
                className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 p-1 rounded-lg transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-3 text-xs font-mono">
              <div className="flex justify-between py-1.5 border-b border-slate-100 dark:border-slate-800/60">
                <span className="text-slate-500 dark:text-slate-400 font-sans">Student ID:</span>
                <span className="text-slate-900 dark:text-slate-100 font-bold">{activeAuditRow.student_id}</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-100 dark:border-slate-800/60">
                <span className="text-slate-500 dark:text-slate-400 font-sans">Course / Field:</span>
                <span className="text-sky-600 dark:text-sky-400 font-bold">{activeAuditRow.course_code}</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-100 dark:border-slate-800/60">
                <span className="text-slate-500 dark:text-slate-400 font-sans">Current Value:</span>
                <span className="text-emerald-600 dark:text-emerald-400 font-bold">{activeAuditRow.grade_point ?? '—'} ({activeAuditRow.letter_grade || '—'})</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-100 dark:border-slate-800/60">
                <span className="text-slate-500 dark:text-slate-400 font-sans">Extracted Value:</span>
                <span className="text-slate-800 dark:text-slate-300 font-bold">{activeAuditRow.grade_point ?? '—'} ({activeAuditRow.letter_grade || '—'})</span>
              </div>

              {activeAuditRow.applied_corrections && activeAuditRow.applied_corrections.length > 0 && (
                <div className="space-y-1 py-1.5 border-b border-slate-100 dark:border-slate-800/60">
                  <span className="text-slate-500 dark:text-slate-400 font-sans">Deterministic Text Normalization:</span>
                  <ul className="list-disc list-inside text-amber-600 dark:text-amber-300 text-[11px]">
                    {activeAuditRow.applied_corrections.map((corr: string, idx: number) => (
                      <li key={idx}>{corr}</li>
                    ))}
                  </ul>
                </div>
              )}

              {activeAuditRow.warnings && activeAuditRow.warnings.length > 0 && (
                <div className="space-y-1 py-1.5 border-b border-slate-100 dark:border-slate-800/60">
                  <span className="text-slate-500 dark:text-slate-400 font-sans">Validation Warnings:</span>
                  <ul className="list-disc list-inside text-rose-600 dark:text-rose-300 text-[11px]">
                    {activeAuditRow.warnings.map((warn: string, idx: number) => (
                      <li key={idx}>{warn}</li>
                    ))}
                  </ul>
                </div>
              )}

              {activeAuditRow.cell_coordinates && (
                <div className="flex justify-between py-1.5">
                  <span className="text-slate-500 dark:text-slate-400 font-sans">Cell Bounding Box [x, y, w, h]:</span>
                  <span className="text-slate-700 dark:text-slate-300 font-mono">
                    [{activeAuditRow.cell_coordinates.map((c: number) => Math.round(c)).join(', ')}]
                  </span>
                </div>
              )}
            </div>

            <div className="pt-2 flex justify-end">
              <Button size="sm" variant="secondary" onClick={() => setActiveAuditRow(null)}>
                Close
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
