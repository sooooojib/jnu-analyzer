export interface ApiResponse<T = unknown> {
  success: boolean;
  message: string;
  data: T;
  meta?: Record<string, unknown>;
  error_code?: string;
  errors?: string[];
}

export interface UploadSuccessData {
  id: string;
  original_filename: string;
  file_type: 'pdf' | 'png' | 'jpeg';
  file_size_bytes: number;
  status: 'PENDING' | 'PROCESSING' | 'PENDING_VERIFICATION' | 'VERIFIED' | 'COMPLETED' | 'FAILED' | 'EXPIRED';
  error_message: string;
  meta_info: Record<string, unknown>;
  created_at: string;
  expires_at: string;
  is_expired: boolean;
}
