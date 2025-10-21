// ABOUTME: Unit tests for the ProgressBar component
// ABOUTME: Tests rendering, progress calculation, modes, and accessibility

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import ProgressBar from './ProgressBar';

describe('ProgressBar Component', () => {
  it('should render progress bar with default props', () => {
    render(<ProgressBar progress={50} />);

    const progressBar = screen.getByRole('progressbar');
    expect(progressBar).toBeInTheDocument();
    expect(progressBar).toHaveAttribute('aria-valuenow', '50');
    expect(progressBar).toHaveAttribute('aria-valuemin', '0');
    expect(progressBar).toHaveAttribute('aria-valuemax', '100');
  });

  it('should display percentage by default', () => {
    render(<ProgressBar progress={75} />);

    expect(screen.getByText('75%')).toBeInTheDocument();
  });

  it('should hide percentage when showPercentage is false', () => {
    render(<ProgressBar progress={75} showPercentage={false} />);

    expect(screen.queryByText('75%')).not.toBeInTheDocument();
  });

  it('should display label when provided', () => {
    render(<ProgressBar progress={30} label="Uploading..." />);

    expect(screen.getByText('Uploading...')).toBeInTheDocument();
    expect(screen.getByText('30%')).toBeInTheDocument();
  });

  it('should clamp progress to 0-100 range', () => {
    const { rerender } = render(<ProgressBar progress={-10} />);
    let progressBar = screen.getByRole('progressbar');
    expect(progressBar).toHaveAttribute('aria-valuenow', '0');
    expect(screen.getByText('0%')).toBeInTheDocument();

    rerender(<ProgressBar progress={150} />);
    progressBar = screen.getByRole('progressbar');
    expect(progressBar).toHaveAttribute('aria-valuenow', '100');
    expect(screen.getByText('100%')).toBeInTheDocument();
  });

  it('should round percentage to nearest integer', () => {
    render(<ProgressBar progress={33.7} />);

    expect(screen.getByText('34%')).toBeInTheDocument();
  });

  it('should apply correct size class', () => {
    const { container, rerender } = render(<ProgressBar progress={50} size="small" />);
    expect(container.firstChild).toHaveClass('progress-small');

    rerender(<ProgressBar progress={50} size="medium" />);
    expect(container.firstChild).toHaveClass('progress-medium');

    rerender(<ProgressBar progress={50} size="large" />);
    expect(container.firstChild).toHaveClass('progress-large');
  });

  it('should apply correct color class', () => {
    const { container, rerender } = render(<ProgressBar progress={50} color="primary" />);
    expect(container.querySelector('.progress-bar')).toHaveClass('progress-primary');

    rerender(<ProgressBar progress={50} color="success" />);
    expect(container.querySelector('.progress-bar')).toHaveClass('progress-success');

    rerender(<ProgressBar progress={50} color="warning" />);
    expect(container.querySelector('.progress-bar')).toHaveClass('progress-warning');

    rerender(<ProgressBar progress={50} color="error" />);
    expect(container.querySelector('.progress-bar')).toHaveClass('progress-error');
  });

  it('should render indeterminate mode', () => {
    render(<ProgressBar progress={50} indeterminate={true} />);

    const progressBar = screen.getByRole('progressbar');
    expect(progressBar).not.toHaveAttribute('aria-valuenow');
    expect(screen.queryByText('50%')).not.toBeInTheDocument();

    const fill = progressBar.querySelector('.progress-indeterminate');
    expect(fill).toBeInTheDocument();
  });

  it('should hide percentage in indeterminate mode with label', () => {
    render(<ProgressBar progress={50} label="Processing..." indeterminate={true} />);

    expect(screen.getByText('Processing...')).toBeInTheDocument();
    expect(screen.queryByText('50%')).not.toBeInTheDocument();
  });

  it('should set correct aria-label with label', () => {
    render(<ProgressBar progress={75} label="Upload progress" />);

    const progressBar = screen.getByRole('progressbar');
    expect(progressBar).toHaveAttribute('aria-label', 'Upload progress: 75%');
  });

  it('should set correct aria-label without label', () => {
    render(<ProgressBar progress={60} />);

    const progressBar = screen.getByRole('progressbar');
    expect(progressBar).toHaveAttribute('aria-label', 'Progress: 60%');
  });

  it('should set aria-label for indeterminate mode', () => {
    render(<ProgressBar progress={50} label="Loading" indeterminate={true} />);

    const progressBar = screen.getByRole('progressbar');
    expect(progressBar).toHaveAttribute('aria-label', 'Loading: Processing');
  });

  it('should render progress fill with correct width', () => {
    const { container } = render(<ProgressBar progress={65} />);

    const fill = container.querySelector('.progress-fill');
    expect(fill).toHaveStyle({ width: '65%' });
  });

  it('should not set width style in indeterminate mode', () => {
    const { container } = render(<ProgressBar progress={50} indeterminate={true} />);

    const fill = container.querySelector('.progress-fill');
    expect(fill).not.toHaveStyle({ width: '50%' });
  });

  it('should handle 0 progress', () => {
    render(<ProgressBar progress={0} />);

    const progressBar = screen.getByRole('progressbar');
    expect(progressBar).toHaveAttribute('aria-valuenow', '0');
    expect(screen.getByText('0%')).toBeInTheDocument();
  });

  it('should handle 100 progress', () => {
    render(<ProgressBar progress={100} />);

    const progressBar = screen.getByRole('progressbar');
    expect(progressBar).toHaveAttribute('aria-valuenow', '100');
    expect(screen.getByText('100%')).toBeInTheDocument();
  });
});