import React from 'react';
import { Terminal } from 'lucide-react';

interface FooterProps {
  onOpenPrivacy?: () => void;
}

export const Footer: React.FC<FooterProps> = () => {
  return (
    <footer className="border-t border-slate-200 dark:border-slate-800/60 bg-slate-50/80 dark:bg-slate-950/60 py-6 mt-20 transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex items-center justify-center">
        <span className="flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400 font-mono hover:text-slate-800 dark:hover:text-slate-200 transition-colors">
          <Terminal className="w-3.5 h-3.5 text-sky-500 dark:text-sky-400" />
          Django 5 + React 19
        </span>
      </div>
    </footer>
  );
};
