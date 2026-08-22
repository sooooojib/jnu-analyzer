import { apiClient } from './client';
import { ApiResponse, UploadSuccessData } from '../types/api';
import { StudentRecord } from '../types/student';
import { CohortAnalytics } from '../types/analytics';
import { StudentComparisonResult } from '../types/comparison';
import { VerificationDataResponse, CellUpdateRequest } from '../types/verification';

export const api = {
  // File Ingestion with real-time progress and abort signal support
  uploadSheet: async (
    file: File,
    options?: {
      onProgress?: (percentage: number) => void;
      signal?: AbortSignal;
    }
  ): Promise<UploadSuccessData> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await apiClient.post<ApiResponse<UploadSuccessData>>('/upload/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      signal: options?.signal,
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total && options?.onProgress) {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          options.onProgress(percentCompleted);
        }
      },
    });
    return response.data.data;
  },

  // Trigger processing on the uploaded dataset
  processSession: async (sessionId: string, signal?: AbortSignal) => {
    const response = await apiClient.post<ApiResponse>(
      `/sessions/${sessionId}/process/`,
      {},
      { signal }
    );
    return response.data.data;
  },

  // Session lifecycle
  getSessionStatus: async (sessionId: string, signal?: AbortSignal): Promise<UploadSuccessData> => {
    const response = await apiClient.get<ApiResponse<UploadSuccessData>>(
      `/sessions/${sessionId}/status/`,
      { signal }
    );
    return response.data.data;
  },

  purgeSession: async (sessionId: string) => {
    const response = await apiClient.delete<ApiResponse>(`/sessions/${sessionId}/`);
    return response.data;
  },

  // Result Verification & Correction
  getVerificationData: async (sessionId: string, signal?: AbortSignal): Promise<VerificationDataResponse> => {
    const response = await apiClient.get<ApiResponse<VerificationDataResponse>>(
      `/sessions/${sessionId}/verification/`,
      { signal }
    );
    return response.data.data;
  },

  updateVerificationCell: async (
    sessionId: string,
    payload: CellUpdateRequest
  ): Promise<VerificationDataResponse> => {
    const response = await apiClient.patch<ApiResponse<VerificationDataResponse>>(
      `/sessions/${sessionId}/verification/update-cell/`,
      payload
    );
    return response.data.data;
  },

  confirmVerification: async (sessionId: string): Promise<UploadSuccessData> => {
    const response = await apiClient.post<ApiResponse<UploadSuccessData>>(
      `/sessions/${sessionId}/verification/confirm/`,
      {}
    );
    return response.data.data;
  },

  // Analytics queries
  getStudentScorecard: async (sessionId: string, studentId: string): Promise<StudentRecord> => {
    const response = await apiClient.get<ApiResponse<StudentRecord>>(
      `/sessions/${sessionId}/students/${encodeURIComponent(studentId)}/`
    );
    return response.data.data;
  },

  getCohortAnalytics: async (sessionId: string): Promise<CohortAnalytics> => {
    const response = await apiClient.get<ApiResponse<CohortAnalytics>>(`/sessions/${sessionId}/analytics/`);
    return response.data.data;
  },

  compareStudents: async (
    sessionId: string,
    studentA: string,
    studentB: string
  ): Promise<StudentComparisonResult> => {
    const response = await apiClient.get<ApiResponse<StudentComparisonResult>>(
      `/sessions/${sessionId}/compare/`,
      { params: { student_a: studentA, student_b: studentB } }
    );
    return response.data.data;
  },

  // Claude AI Assistance & Markdown ingestion
  getClaudePrompt: async () => {
    const response = await apiClient.get<ApiResponse<{
      prompt: string;
      claude_url: string;
      reference_courses: Array<{ code: string; title: string; credits: number }>;
    }>>('/sessions/claude-prompt/');
    return response.data.data;
  },

  uploadMarkdownText: async (markdownText: string, filename: string = 'claude_extracted.md') => {
    const response = await apiClient.post<ApiResponse<{
      session: UploadSuccessData;
      verification: VerificationDataResponse;
    }>>('/sessions/upload-markdown/', {
      markdown_text: markdownText,
      filename,
    });
    return response.data.data;
  },

  // Developer debugging visualization
  getDebugVisualization: async (sessionId: string) => {
    const response = await apiClient.get<ApiResponse<any>>(
      `/sessions/${sessionId}/debug/visualization/`
    );
    return response.data.data;
  },
};
