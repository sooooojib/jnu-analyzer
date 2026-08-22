import React, { useRef, useState } from 'react';
import { 
  UploadCloud, 
  FileText, 
  CheckCircle, 
  ArrowUpRight,
  X,
  FileCheck2,
  Loader2,
  ShieldAlert
} from 'lucide-react';
import { Button } from '../common/Button';
import { Card } from '../common/Card';
import { Badge } from '../common/Badge';

export interface FileUploadZoneProps {
  onFileSelect: (file: File) => void;
  isUploading?: boolean;
  uploadProgress?: number;
  uploadStage?: string;
  error?: string | null;
  onClearError?: () => void;
  onCancelUpload?: () => void;
}

const ALLOWED_EXTENSIONS = ['.md', '.markdown', '.txt'];
const ALLOWED_MIME_TYPES = ['text/markdown', 'text/plain', 'text/x-markdown'];
const MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024; // 25 MB

export const FileUploadZone: React.FC<FileUploadZoneProps> = ({
  onFileSelect,
  isUploading = false,
  uploadProgress = 0,
  uploadStage = 'Uploading document...',
  error = null,
  onClearError,
  onCancelUpload,
}) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [clientValidationError, setClientValidationError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateFile = (file: File): boolean => {
    setClientValidationError(null);
    if (onClearError) onClearError();

    // 1. Check size
    if (file.size > MAX_FILE_SIZE_BYTES) {
      setClientValidationError(`File size (${(file.size / (1024 * 1024)).toFixed(1)}MB) exceeds the maximum limit of 25MB.`);
      return false;
    }

    if (file.size === 0) {
      setClientValidationError("The selected file is empty (0 bytes).");
      return false;
    }

    // 2. Check extension & MIME
    const fileNameLower = file.name.toLowerCase();
    const hasValidExtension = ALLOWED_EXTENSIONS.some((ext) => fileNameLower.endsWith(ext));
    const hasValidMime = ALLOWED_MIME_TYPES.includes(file.type) || file.type === '';

    if (!hasValidExtension && !hasValidMime) {
      setClientValidationError("Unsupported format. Please upload a Markdown (.md) or Text (.txt) result sheet.");
      return false;
    }

    return true;
  };

  const handleFiles = (files: FileList | null) => {
    if (!files || files.length === 0) return;
    const file = files[0];
    if (validateFile(file)) {
      setSelectedFile(file);
    } else {
      setSelectedFile(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!isUploading) setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
    if (isUploading) return;
    handleFiles(e.dataTransfer.files);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    handleFiles(e.target.files);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      fileInputRef.current?.click();
    }
  };

  const handleUploadSubmit = () => {
    if (selectedFile && !isUploading) {
      onFileSelect(selectedFile);
    }
  };

  const handleReset = () => {
    setSelectedFile(null);
    setClientValidationError(null);
    if (onClearError) onClearError();
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const activeError = clientValidationError || error;

  return (
    <div className="w-full max-w-4xl mx-auto space-y-6">
      {/* Upload Box */}
      <Card
        glass
        tabIndex={0}
        role="button"
        aria-label="Upload academic result sheet dropzone"
        className={`relative border-2 border-dashed transition-all duration-300 outline-none p-6 sm:p-12 text-center rounded-3xl ${
          isDragOver
            ? 'border-emerald-400 bg-emerald-950/30 scale-[1.01]'
            : 'border-slate-800 hover:border-slate-700 bg-slate-900/40 focus-visible:border-emerald-500 focus-visible:ring-2 focus-visible:ring-emerald-500/20'
        } ${isUploading ? 'pointer-events-none opacity-90' : 'cursor-pointer'}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !selectedFile && !isUploading && fileInputRef.current?.click()}
        onKeyDown={!selectedFile && !isUploading ? handleKeyDown : undefined}
      >
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleInputChange}
          accept=".md,.markdown,.txt,text/markdown,text/plain"
          className="hidden"
          disabled={isUploading}
          aria-hidden="true"
        />

        {!isUploading ? (
          <div className="flex flex-col items-center justify-center max-w-lg mx-auto">
            {/* Upload Icon */}
            <div className="w-16 h-16 sm:w-20 sm:h-20 rounded-3xl bg-gradient-to-tr from-emerald-600/20 to-teal-500/10 border border-emerald-500/30 flex items-center justify-center mb-6 shadow-inner">
              <UploadCloud className="w-8 h-8 sm:w-10 sm:h-10 text-emerald-400" />
            </div>

            <h2 className="text-xl sm:text-2xl font-extrabold text-slate-100 mb-2 tracking-tight">
              Upload Markdown (.md) Result Sheet
            </h2>
            <p className="text-xs sm:text-sm text-slate-400 mb-6 leading-relaxed max-w-md">
              Drag and drop your AI-extracted Markdown file, or click to browse. The engine parses subjects, grades, GPAs, and CGPAs universally across any institution.
            </p>

            {/* Allowed Formats Pills */}
            <div className="flex flex-wrap items-center justify-center gap-2 mb-8">
              <Badge variant="emerald" size="sm" className="gap-1.5 py-1 px-3">
                <FileText className="w-3.5 h-3.5 text-emerald-400" /> Markdown (.md / .markdown)
              </Badge>
              <Badge variant="slate" size="sm" className="gap-1.5 py-1 px-3">
                <FileText className="w-3.5 h-3.5 text-sky-400" /> Plain Text (.txt)
              </Badge>
              <Badge variant="emerald" size="sm" className="gap-1.5 py-1 px-3">
                <CheckCircle className="w-3.5 h-3.5" /> Max 25 MB
              </Badge>
            </div>

            {/* Selected File Card */}
            {selectedFile && !activeError && (
              <div 
                className="w-full mb-6 p-4 rounded-2xl bg-slate-950/80 border border-slate-800 flex items-center justify-between text-left shadow-lg"
                onClick={(e) => e.stopPropagation()}
              >
                <div className="flex items-center gap-3.5 overflow-hidden">
                  <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center flex-shrink-0">
                    <FileCheck2 className="w-5 h-5 text-emerald-400" />
                  </div>
                  <div className="truncate">
                    <div className="text-sm font-semibold text-slate-200 truncate">
                      {selectedFile.name}
                    </div>
                    <div className="text-xs text-slate-500 font-mono">
                      {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB • {selectedFile.type || 'Document'}
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <Badge variant="emerald" size="sm">Valid</Badge>
                  <button
                    type="button"
                    onClick={handleReset}
                    className="text-slate-400 hover:text-rose-400 p-1.5 rounded-lg hover:bg-white/5 transition-colors"
                    aria-label="Remove selected file"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}

            {/* Error Message Box */}
            {activeError && (
              <div 
                className="w-full mb-6 p-4 rounded-2xl bg-rose-950/40 border border-rose-800/60 flex items-start gap-3 text-rose-200 text-xs sm:text-sm text-left shadow-lg"
                onClick={(e) => e.stopPropagation()}
              >
                <ShieldAlert className="w-5 h-5 text-rose-400 flex-shrink-0 mt-0.5" />
                <div className="flex-1">{activeError}</div>
                <button
                  type="button"
                  onClick={() => {
                    setClientValidationError(null);
                    if (onClearError) onClearError();
                  }}
                  className="text-rose-400 hover:text-rose-200 p-1 rounded-lg hover:bg-rose-900/40 transition-colors"
                  aria-label="Dismiss error"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row items-center gap-3 w-full sm:w-auto" onClick={(e) => e.stopPropagation()}>
              {selectedFile ? (
                <>
                  <Button
                    size="lg"
                    onClick={handleUploadSubmit}
                    rightIcon={<ArrowUpRight className="w-4 h-4" />}
                    className="w-full sm:w-auto min-w-[200px]"
                  >
                    Upload & Process Sheet
                  </Button>
                  <Button
                    variant="outline"
                    size="lg"
                    onClick={handleReset}
                    className="w-full sm:w-auto"
                  >
                    Choose Different File
                  </Button>
                </>
              ) : (
                <Button
                  size="lg"
                  onClick={() => fileInputRef.current?.click()}
                  rightIcon={<ArrowUpRight className="w-4 h-4" />}
                  className="w-full sm:w-auto min-w-[220px]"
                >
                  Browse Files
                </Button>
              )}
            </div>
          </div>
        ) : (
          /* Multi-Stage Upload & Processing Animation */
          <div className="py-4 max-w-md mx-auto space-y-6">
            <div className="w-16 h-16 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center mx-auto">
              <Loader2 className="w-8 h-8 text-emerald-400 animate-spin" />
            </div>

            <div>
              <h3 className="text-lg font-bold text-slate-100 mb-1">
                Ingesting Result Sheet
              </h3>
              <p className="text-xs text-slate-400">
                {uploadStage}
              </p>
            </div>

            {/* Progress Bar */}
            <div className="space-y-2 text-left">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-slate-400">Upload Progress</span>
                <span className="text-emerald-400 font-bold">{uploadProgress}%</span>
              </div>
              <div className="w-full h-2.5 rounded-full bg-slate-800 overflow-hidden shadow-inner">
                <div 
                  className="h-full bg-gradient-to-r from-emerald-500 to-teal-400 rounded-full transition-all duration-300 ease-out"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
            </div>

            {/* Step Indicators */}
            <div className="grid grid-cols-3 gap-2 text-[11px] text-slate-400 text-center">
              <div className={`p-2 rounded-lg border ${uploadProgress >= 30 ? 'bg-emerald-950/40 border-emerald-800 text-emerald-300' : 'bg-slate-950/40 border-slate-800'}`}>
                1. Stream File
              </div>
              <div className={`p-2 rounded-lg border ${uploadProgress >= 70 ? 'bg-emerald-950/40 border-emerald-800 text-emerald-300' : 'bg-slate-950/40 border-slate-800'}`}>
                2. Parse Markdown
              </div>
              <div className={`p-2 rounded-lg border ${uploadProgress === 100 ? 'bg-emerald-950/40 border-emerald-800 text-emerald-300' : 'bg-slate-950/40 border-slate-800'}`}>
                3. Init Dataset
              </div>
            </div>

            {/* Cancel Button */}
            {onCancelUpload && (
              <div className="pt-2">
                <Button
                  variant="danger"
                  size="sm"
                  onClick={onCancelUpload}
                  leftIcon={<X className="w-3.5 h-3.5" />}
                  className="text-xs px-4 py-1.5"
                >
                  Cancel Upload
                </Button>
              </div>
            )}
          </div>
        )}
      </Card>
    </div>
  );
};
