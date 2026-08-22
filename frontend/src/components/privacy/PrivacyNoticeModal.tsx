import React from 'react';
import { Badge } from '../common/Badge';
import { Button } from '../common/Button';
import { Shield, Lock, Trash2, Clock, EyeOff, X, CheckCircle2 } from 'lucide-react';

interface PrivacyNoticeModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const PrivacyNoticeModal: React.FC<PrivacyNoticeModalProps> = ({
  isOpen,
  onClose,
}) => {
  if (!isOpen) return null;

  return (
    <div className="modal-overlay-backdrop animate-in fade-in duration-200">
      <div className="relative w-full max-w-2xl">
        <div className="p-6 sm:p-8 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-2xl space-y-6 text-slate-900 dark:text-slate-100">
          {/* Header */}
          <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
                <Shield className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100">Privacy & Data Security Notice</h3>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Privacy-first academic result tabulation and analytics architecture.
                </p>
              </div>
            </div>

            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-100 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Privacy Commitments Grid */}
          <div className="space-y-4 text-xs text-slate-600 dark:text-slate-300">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-950/60 border border-slate-200 dark:border-slate-800 space-y-2">
                <div className="flex items-center gap-2 font-bold text-slate-900 dark:text-slate-100">
                  <Lock className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                  <span>No Public File Access</span>
                </div>
                <p className="text-slate-500 dark:text-slate-400 leading-relaxed">
                  Uploaded files are never exposed to public static URLs or media endpoints. Only the temporary processing session can access raw files.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-950/60 border border-slate-200 dark:border-slate-800 space-y-2">
                <div className="flex items-center gap-2 font-bold text-slate-900 dark:text-slate-100">
                  <Clock className="w-4 h-4 text-sky-600 dark:text-sky-400" />
                  <span>Automatic 60-Min Expiration</span>
                </div>
                <p className="text-slate-500 dark:text-slate-400 leading-relaxed">
                  All uploaded sheets and extracted datasets are assigned an ephemeral 60-minute TTL and automatically purged upon expiration.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-950/60 border border-slate-200 dark:border-slate-800 space-y-2">
                <div className="flex items-center gap-2 font-bold text-slate-900 dark:text-slate-100">
                  <Trash2 className="w-4 h-4 text-rose-600 dark:text-rose-400" />
                  <span>Instant Manual Purge</span>
                </div>
                <p className="text-slate-500 dark:text-slate-400 leading-relaxed">
                  You can immediately wipe and purge your dataset and disk files at any time with a single click on "Delete & Purge Dataset".
                </p>
              </div>

              <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-950/60 border border-slate-200 dark:border-slate-800 space-y-2">
                <div className="flex items-center gap-2 font-bold text-slate-900 dark:text-slate-100">
                  <EyeOff className="w-4 h-4 text-sky-600 dark:text-sky-400" />
                  <span>Zero Data Sharing or Training</span>
                </div>
                <p className="text-slate-500 dark:text-slate-400 leading-relaxed">
                  All parsing and calculations run locally and deterministically. Uploaded markdown is never used for training or persisted beyond your session.
                </p>
              </div>
            </div>

            {/* Technical Security Measures */}
            <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-950/80 border border-slate-200 dark:border-slate-800 space-y-2">
              <span className="font-bold text-slate-900 dark:text-slate-200 block text-xs">Technical Hardening Applied:</span>
              <ul className="grid grid-cols-1 sm:grid-cols-2 gap-1.5 text-[11px] text-slate-600 dark:text-slate-400">
                <li className="flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" /> Unpredictable UUIDv4 session identifiers
                </li>
                <li className="flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" /> Magic-byte & MIME sniffing verification
                </li>
                <li className="flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" /> Path traversal & filename sanitization
                </li>
                <li className="flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" /> Redacted student IDs in audit logs
                </li>
                <li className="flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" /> X-Frame-Options: DENY & nosniff
                </li>
                <li className="flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" /> Strict cache-control headers on API responses
                </li>
              </ul>
            </div>
          </div>

          {/* Footer Action */}
          <div className="flex items-center justify-between pt-2 border-t border-slate-200 dark:border-slate-800">
            <Badge variant="emerald" size="sm">Privacy Policy Standard 2026</Badge>
            <Button size="sm" variant="primary" onClick={onClose}>
              I Understand & Agree
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};
