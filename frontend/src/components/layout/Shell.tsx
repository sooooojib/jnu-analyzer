import React, { useState } from 'react';
import { Navbar } from './Navbar';
import { Footer } from './Footer';
import { PrivacyNoticeModal } from '../privacy/PrivacyNoticeModal';

export interface ShellProps {
  children: React.ReactNode;
  hasActiveSession?: boolean;
  sessionId?: string | null;
  onClearSession?: () => void;
}

export const Shell: React.FC<ShellProps> = ({
  children,
  hasActiveSession,
  sessionId,
  onClearSession,
}) => {
  const [isPrivacyOpen, setIsPrivacyOpen] = useState(false);

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 transition-colors duration-200">
      <Navbar
        hasActiveSession={hasActiveSession}
        sessionId={sessionId}
        onClearSession={onClearSession}
      />
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>
      <Footer onOpenPrivacy={() => setIsPrivacyOpen(true)} />

      {/* Privacy Notice Modal */}
      <PrivacyNoticeModal
        isOpen={isPrivacyOpen}
        onClose={() => setIsPrivacyOpen(false)}
      />
    </div>
  );
};
