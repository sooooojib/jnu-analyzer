import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ResultDashboard } from '../components/dashboard/ResultDashboard';
import { GPADistributionChart } from '../components/charts/GPADistributionChart';
import { StudentVsClassAverageChart } from '../components/charts/StudentVsClassAverageChart';
import { CurrentVsCumulativeSummaryChart } from '../components/charts/CurrentVsCumulativeSummaryChart';

describe('ResultDashboard Component Tests', () => {
  it('renders search input and initial controls', () => {
    render(<ResultDashboard sessionId="test-session-123" initialStudentId="2102045" />);
    expect(screen.getByPlaceholderText(/Enter Student ID/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Lookup/i })).toBeInTheDocument();
  });

  it('renders CurrentVsCumulativeSummaryChart with correct dual scope metrics', () => {
    render(
      <CurrentVsCumulativeSummaryChart
        semesterGPA={3.85}
        semesterRank={2}
        semesterPercentile={95.0}
        semesterCreditsEarned={18.0}
        semesterCreditsAttempted={18.0}
        semesterStatus="PASSED"
        cumulativeCGPA={3.80}
        cumulativeRank={3}
        cumulativePercentile={92.5}
        cumulativeCreditsEarned={60.0}
        cumulativeStatus="PASSED"
      />
    );

    expect(screen.getByText('3.85')).toBeInTheDocument();
    expect(screen.getByText('3.80')).toBeInTheDocument();
    expect(screen.getByText('#2')).toBeInTheDocument();
    expect(screen.getByText('#3')).toBeInTheDocument();
    expect(screen.getByText(/Current Semester vs. Cumulative Academic Summary/i)).toBeInTheDocument();
  });

  it('renders StudentVsClassAverageChart with comparative mean and median', () => {
    render(
      <StudentVsClassAverageChart
        studentGPA={3.85}
        studentName="ALICE JOHNSON"
        studentId="2102045"
        classMeanGPA={3.62}
        classMedianGPA={3.75}
        classHighestGPA={4.00}
        classLowestGPA={3.00}
        classStdDev={0.28}
        totalStudents={24}
      />
    );

    expect(screen.getByText(/ALICE JOHNSON/i)).toBeInTheDocument();
    expect(screen.getAllByText(/3\.62/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/3\.75/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/±0\.28/i)).toBeInTheDocument();
    expect(screen.getByText(/\+0\.23 GPA vs Class Mean/i)).toBeInTheDocument();
  });

  it('renders GPADistributionChart with brackets and table view toggle', () => {
    const distribution = [
      { bracket: '3.75 - 4.00', count: 8, percentage: 33.3 },
      { bracket: '3.50 - 3.74', count: 10, percentage: 41.7 },
      { bracket: '3.00 - 3.49', count: 4, percentage: 16.7 },
      { bracket: '2.50 - 2.99', count: 2, percentage: 8.3 },
      { bracket: '2.00 - 2.49', count: 0, percentage: 0.0 },
      { bracket: '< 2.00', count: 0, percentage: 0.0 },
    ];

    render(
      <GPADistributionChart
        distribution={distribution}
        selectedStudentGPA={3.85}
        classMeanGPA={3.62}
        classMedianGPA={3.75}
        totalStudents={24}
      />
    );

    expect(screen.getByText(/Class GPA Distribution/i)).toBeInTheDocument();
    expect(screen.getAllByText(/3.75/).length).toBeGreaterThan(0);

    // Toggle table view
    const toggleBtn = screen.getByRole('button', { name: /Table View/i });
    fireEvent.click(toggleBtn);
    expect(screen.getByText(/Score Bracket/i)).toBeInTheDocument();
    expect(screen.getByText(/Cohort Percentage/i)).toBeInTheDocument();
  });
});
