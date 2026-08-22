/**
 * Standard UGC / University 10-tier Grading Scale
 */
export const getLetterGradeFromGP = (gp: number | null | undefined): string => {
  if (gp === null || gp === undefined || isNaN(gp)) return '—';
  if (gp >= 4.00) return 'A+';
  if (gp >= 3.75) return 'A';
  if (gp >= 3.50) return 'A-';
  if (gp >= 3.25) return 'B+';
  if (gp >= 3.00) return 'B';
  if (gp >= 2.75) return 'B-';
  if (gp >= 2.50) return 'C+';
  if (gp >= 2.25) return 'C';
  if (gp >= 2.00) return 'D';
  return 'F';
};

export const getGradeBadgeVariant = (grade: string | null | undefined): 'emerald' | 'blue' | 'amber' | 'rose' | 'slate' => {
  if (!grade) return 'slate';
  const g = grade.trim().toUpperCase();
  if (g.startsWith('A')) return 'emerald';
  if (g.startsWith('B') || g.startsWith('C')) return 'blue';
  if (g.startsWith('D')) return 'amber';
  return 'rose';
};
