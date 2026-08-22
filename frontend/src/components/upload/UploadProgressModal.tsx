import React from 'react';
import { Card } from '../common/Card';
import { Spinner } from '../common/Spinner';
import { Badge } from '../common/Badge';

export interface UploadProgressModalProps {
  status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
  filename: string;
  stepMessage: string;
}

export const UploadProgressModal: React.FC<UploadProgressModalProps> = ({
  status,
  filename,
  stepMessage,
}) => {
  return (
    <Card glass className="p-6 max-w-lg mx-auto border-slate-200 dark:border-slate-800">
      <div className="flex items-center gap-4">
        <Spinner size="lg" />
        <div className="flex-1">
          <div className="flex items-center justify-between mb-1">
            <span className="text-sm font-semibold text-slate-900 dark:text-slate-100 truncate max-w-[240px]">
              {filename}
            </span>
            <Badge variant="blue" size="sm">
              {status}
            </Badge>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400">{stepMessage}</p>
        </div>
      </div>
    </Card>
  );
};
