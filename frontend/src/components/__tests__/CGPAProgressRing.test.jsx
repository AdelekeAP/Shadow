import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import CGPAProgressRing from '../CGPAProgressRing';

describe('CGPAProgressRing', () => {
  it('renders SVG element', () => {
    render(<CGPAProgressRing currentCGPA={3.5} targetCGPA={4.5} />);
    expect(screen.getByTestId('cgpa-ring-svg')).toBeTruthy();
  });

  it('displays current CGPA text', () => {
    render(<CGPAProgressRing currentCGPA={3.50} targetCGPA={4.5} />);
    expect(screen.getByText('3.50')).toBeTruthy();
  });

  it('displays max scale text', () => {
    render(<CGPAProgressRing currentCGPA={3.5} targetCGPA={4.5} maxScale={5.0} />);
    expect(screen.getByText('/ 5.0')).toBeTruthy();
  });

  it('applies green color when on track (>=90% of target)', () => {
    render(<CGPAProgressRing currentCGPA={4.2} targetCGPA={4.5} />);
    const progress = screen.getByTestId('cgpa-ring-progress');
    expect(progress.getAttribute('stroke')).toBe('#10b981');
  });

  it('applies amber color when close (75-89% of target)', () => {
    render(<CGPAProgressRing currentCGPA={3.5} targetCGPA={4.5} />);
    const progress = screen.getByTestId('cgpa-ring-progress');
    expect(progress.getAttribute('stroke')).toBe('#f59e0b');
  });

  it('applies red color when behind (<75% of target)', () => {
    render(<CGPAProgressRing currentCGPA={2.0} targetCGPA={4.5} />);
    const progress = screen.getByTestId('cgpa-ring-progress');
    expect(progress.getAttribute('stroke')).toBe('#ef4444');
  });

  it('handles zero CGPA', () => {
    render(<CGPAProgressRing currentCGPA={0} targetCGPA={4.5} />);
    expect(screen.getByText('0.00')).toBeTruthy();
  });

  it('handles max CGPA of 5.0', () => {
    render(<CGPAProgressRing currentCGPA={5.0} targetCGPA={5.0} />);
    expect(screen.getByText('5.00')).toBeTruthy();
    const progress = screen.getByTestId('cgpa-ring-progress');
    expect(progress.getAttribute('stroke')).toBe('#10b981');
  });
});
