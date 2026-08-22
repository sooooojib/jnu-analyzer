import React from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  glass?: boolean;
  hoverable?: boolean;
}

export const Card: React.FC<CardProps> = ({
  children,
  className,
  glass = false,
  hoverable = false,
  ...props
}) => {
  return (
    <div
      className={twMerge(
        clsx(
          "rounded-2xl border transition-all duration-200",
          glass
            ? "bg-white/90 dark:bg-slate-900/60 backdrop-blur-xl border-slate-200 dark:border-slate-800/80 shadow-sm dark:shadow-xl"
            : "bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 shadow-sm dark:shadow-md",
          hoverable && "hover:border-slate-300 dark:hover:border-slate-700 hover:shadow-md dark:hover:shadow-lg hover:-translate-y-0.5",
          className
        )
      )}
      {...props}
    >
      {children}
    </div>
  );
};
