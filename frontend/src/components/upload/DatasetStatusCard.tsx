import React from 'react';
import { Card } from '../common/Card';
import { Badge } from '../common/Badge';
import { Button } from '../common/Button';
import { UploadSuccessData } from '../../types/api';
import { 
  FileText, 
  Trash2, 
  ArrowRight,
  CheckCircle2,
  AlertTriangle,
  Edit3
} from 'lucide-react';

export interface DatasetStatusCardProps {
  session: UploadSuccessData;
  onProceedToVerification: () => void;
  onProceedToScorecard: () => void;
  onPurgeDataset: () => void;
  isPurging?: boolean;
}

export const DatasetStatusCard: React.FC<DatasetStatusCardProps> = ({
  session,
  onProceedToVerification,
  onProceedToScorecard,
  onPurgeDataset,
  isPurging = false,
}) => {
  const isVerified = session.status === 'VERIFIED' || session.status === 'COMPLETED';

  const getStatusBadge = () => {
    switch (session.status) {
      case 'COMPLETED':
      case 'VERIFIED':
        return <Badge variant="emerald" size="md" className="gap-1.5"><CheckCircle2 className="w-3.5 h-3.5" /> Verified & Ready</Badge>;
      case 'PENDING_VERIFICATION':
        return <Badge variant="amber" size="md" className="gap-1.5"><AlertTriangle className="w-3.5 h-3.5" /> Ready for Review</Badge>;
      case 'PROCESSING':
        return <Badge variant="blue" size="md" className="gap-1.5 animate-pulse">Processing...</Badge>;
      case 'FAILED':
        return <Badge variant="rose" size="md" className="gap-1.5"><AlertTriangle className="w-3.5 h-3.5" /> Please Re-upload</Badge>;
      default:
        return <Badge variant="amber" size="md">{session.status}</Badge>;
    }
  };

  return (
    <Card glass className="p-6 sm:p-7 border-slate-800 space-y-5">
      {/* Header Info */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center flex-shrink-0">
            <FileText className="w-6 h-6 text-emerald-400" />
          </div>
          <div>
            <div className="flex flex-wrap items-center gap-2 mb-1">
              <h3 className="text-base font-bold text-slate-100 truncate max-w-md">
                {session.original_filename}
              </h3>
              {getStatusBadge()}
            </div>
            <p className="text-xs text-slate-400">
              Result sheet loaded successfully. You can verify marks, look up individual scorecards, or view class rankings.
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3 w-full sm:w-auto">
          <Button
            variant="secondary"
            size="md"
            onClick={onProceedToVerification}
            leftIcon={<Edit3 className="w-4 h-4 text-emerald-400" />}
            className="w-full sm:w-auto"
          >
            Verify & Edit Data
          </Button>

          <Button
            variant={isVerified ? "primary" : "secondary"}
            size="md"
            onClick={onProceedToScorecard}
            rightIcon={<ArrowRight className="w-4 h-4" />}
            className="w-full sm:w-auto bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold"
          >
            Explore Students →
          </Button>
        </div>
      </div>

      {/* Footer Actions */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-3 border-t border-slate-800/60 text-xs text-slate-400">
        <div className="flex items-center gap-2 text-emerald-400">
          <div className="w-2 h-2 rounded-full bg-emerald-400" />
          <span className="text-slate-300">Active dataset in session</span>
        </div>

        <button
          type="button"
          onClick={onPurgeDataset}
          disabled={isPurging}
          className="text-rose-400 hover:text-rose-300 hover:underline flex items-center gap-1.5 disabled:opacity-50 transition-colors"
        >
          <Trash2 className="w-3.5 h-3.5" />
          {isPurging ? "Removing..." : "Upload Different Sheet"}
        </button>
      </div>
    </Card>
  );
};
