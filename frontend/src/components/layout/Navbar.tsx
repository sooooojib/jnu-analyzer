import React from 'react';
import { Trash2 } from 'lucide-react';
import { Button } from '../common/Button';

import { ThemeToggle } from '../common/ThemeToggle';

export interface NavbarProps {
  hasActiveSession?: boolean;
  sessionId?: string | null;
  onClearSession?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  hasActiveSession = false,
  onClearSession,
}) => {
  return (
    <header className="sticky top-0 z-40 w-full border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-xl">
      <div className="max-w-7xl mx-auto px-3 sm:px-6 lg:px-8 h-14 sm:h-16 flex items-center justify-between gap-2">
        <div className="flex items-center gap-3 group cursor-pointer">
          <div className="w-10 h-10 rounded-xl bg-slate-900 border border-emerald-500/30 p-1 shadow-lg shadow-emerald-500/10 flex items-center justify-center transition-all duration-300 group-hover:border-emerald-400/80 group-hover:shadow-[0_0_24px_rgba(16,185,129,0.55)] group-hover:scale-105">
            <svg
              viewBox="0 0 48 48"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
              className="w-7 h-7 transition-all duration-300 group-hover:drop-shadow-[0_0_8px_rgba(16,185,129,0.9)]"
            >
              {/* Outer rounded monitor casing */}
              <rect
                x="4"
                y="6"
                width="40"
                height="30"
                rx="7"
                stroke="#10B981"
                strokeWidth="2.5"
                className="transition-colors duration-300 group-hover:stroke-emerald-400"
              />
              {/* Stand neck and base */}
              <path
                d="M20 36V41M28 36V41M15 41H33"
                stroke="#10B981"
                strokeWidth="2.5"
                strokeLinecap="round"
                className="transition-colors duration-300 group-hover:stroke-emerald-400"
              />
              {/* Subtle CRT Screen Glow Backdrop */}
              <rect
                x="8"
                y="10"
                width="32"
                height="22"
                rx="3.5"
                fill="#10B981"
                fillOpacity="0.08"
                className="transition-all duration-300 group-hover:fill-opacity-20"
              />
              {/* ECG Pulse Heartbeat Waveform */}
              <path
                d="M10 21H17L20 13L25 28L28 17L30 21H38"
                stroke="#10B981"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="transition-colors duration-300 group-hover:stroke-emerald-300"
              />
            </svg>
          </div>
          <span className="font-extrabold text-base sm:text-lg tracking-tight text-slate-900 dark:text-transparent dark:bg-gradient-to-r dark:from-slate-100 dark:to-slate-300 dark:bg-clip-text transition-colors whitespace-nowrap">
            JnU Analyzer
          </span>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <ThemeToggle />

          {hasActiveSession && (
            <>
              {/* Mobile: icon only */}
              <button
                type="button"
                onClick={onClearSession}
                aria-label="Clear Session"
                className="sm:hidden flex items-center justify-center w-8 h-8 rounded-lg border border-rose-500/30 hover:border-rose-500/50 hover:bg-rose-500/10 text-rose-400 transition-colors"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
              {/* sm+: full button */}
              <Button
                variant="outline"
                size="sm"
                onClick={onClearSession}
                leftIcon={<Trash2 className="w-3.5 h-3.5 text-rose-400" />}
                className="hidden sm:flex text-xs border-rose-500/30 hover:border-rose-500/50 hover:bg-rose-500/10 text-rose-300"
              >
                Clear Session
              </Button>
            </>
          )}
        </div>
      </div>
    </header>
  );
};
