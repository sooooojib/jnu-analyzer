import React from 'react';
import { AlertCircle, CheckCircle2, Info, AlertTriangle, X } from 'lucide-react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export interface AlertProps {
  type?: 'info' | 'success' | 'warning' | 'error';
  title?: string;
  message: string;
  onClose?: () => void;
  className?: string;
}

export const Alert: React.FC<AlertProps> = ({
  type = 'info',
  title,
  message,
  onClose,
  className,
}) => {
  const configs = {
    info: {
      icon: Info,
      wrapper: "bg-sky-50 dark:bg-sky-950/40 border-sky-200 dark:border-sky-800/60 text-sky-900 dark:text-sky-200",
      iconColor: "text-sky-600 dark:text-sky-400",
    },
    success: {
      icon: CheckCircle2,
      wrapper: "bg-emerald-50 dark:bg-emerald-950/40 border-emerald-200 dark:border-emerald-800/60 text-emerald-900 dark:text-emerald-200",
      iconColor: "text-emerald-600 dark:text-emerald-400",
    },
    warning: {
      icon: AlertTriangle,
      wrapper: "bg-amber-50 dark:bg-amber-950/40 border-amber-200 dark:border-amber-800/60 text-amber-900 dark:text-amber-200",
      iconColor: "text-amber-600 dark:text-amber-400",
    },
    error: {
      icon: AlertCircle,
      wrapper: "bg-rose-50 dark:bg-rose-950/40 border-rose-200 dark:border-rose-800/60 text-rose-900 dark:text-rose-200",
      iconColor: "text-rose-600 dark:text-rose-400",
    },
  };

  const current = configs[type];
  const IconComponent = current.icon;

  return (
    <div className={twMerge(clsx("relative flex items-start gap-3 p-4 rounded-xl border shadow-sm", current.wrapper, className))}>
      <IconComponent className={clsx("w-5 h-5 flex-shrink-0 mt-0.5", current.iconColor)} />
      <div className="flex-1 text-sm">
        {title && <div className="font-bold mb-0.5 text-slate-900 dark:text-slate-100">{title}</div>}
        <div className="opacity-95">{message}</div>
      </div>
      {onClose && (
        <button
          onClick={onClose}
          className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 p-1 rounded-lg hover:bg-slate-200/50 dark:hover:bg-white/5 transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      )}
    </div>
  );
};
