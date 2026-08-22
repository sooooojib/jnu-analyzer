import React from 'react';
import { Sun, Moon } from 'lucide-react';
import { useTheme } from '../../hooks/useTheme';

export const ThemeToggle: React.FC<{ className?: string }> = ({ className = '' }) => {
  const { isDark, toggleTheme } = useTheme();

  return (
    <button
      id="themeToggleBtn"
      type="button"
      onClick={toggleTheme}
      aria-label="Toggle theme mode"
      title={`Switch to ${isDark ? 'Light' : 'Dark'} Mode`}
      className={`group relative inline-flex items-center min-h-[36px] sm:min-h-[44px] px-1 sm:px-2 py-1 rounded-full border border-slate-200 hover:border-slate-300 dark:border-slate-800 dark:hover:border-slate-700 bg-slate-100 dark:bg-slate-950 text-[10px] font-mono tracking-wider uppercase transition-all duration-200 active:scale-95 shadow-sm touch-manipulation ${className}`}
    >
      <div className="relative flex items-center h-7">
        {/* Sliding active pill indicator */}
        <div
          className={`absolute top-0 bottom-0 w-1/2 rounded-full transition-all duration-300 cubic-bezier(0.4, 0, 0.2, 1) ${
            isDark
              ? 'left-0 bg-slate-800 border border-slate-700 text-slate-100 shadow-sm'
              : 'left-1/2 bg-white border border-slate-200 text-slate-900 shadow-sm'
          }`}
        />
        {/* DARK side */}
        <span
          className={`relative z-10 flex items-center gap-1 px-2 sm:px-2.5 py-0.5 transition-colors duration-300 font-bold ${
            isDark ? 'text-white' : 'text-slate-500 hover:text-slate-800'
          }`}
        >
          <Moon className="w-3 h-3 text-sky-400" />
          <span className="hidden sm:inline">DARK</span>
        </span>
        {/* LIGHT side */}
        <span
          className={`relative z-10 flex items-center gap-1 px-2 sm:px-2.5 py-0.5 transition-colors duration-300 font-bold ${
            !isDark ? 'text-slate-900' : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <Sun className="w-3 h-3 text-amber-500" />
          <span className="hidden sm:inline">LIGHT</span>
        </span>
      </div>
    </button>
  );
};
