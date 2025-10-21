// ABOUTME: Progress bar component for displaying upload progress
// ABOUTME: Supports determinate and indeterminate modes with accessibility features

import React from 'react';
import './ProgressBar.css';

interface ProgressBarProps {
  progress: number; // 0-100
  label?: string;
  showPercentage?: boolean;
  indeterminate?: boolean;
  color?: 'primary' | 'success' | 'warning' | 'error';
  size?: 'small' | 'medium' | 'large';
}

const ProgressBar: React.FC<ProgressBarProps> = ({
  progress,
  label,
  showPercentage = true,
  indeterminate = false,
  color = 'primary',
  size = 'medium',
}) => {
  const clampedProgress = Math.min(100, Math.max(0, progress));
  const progressText = `${Math.round(clampedProgress)}%`;

  const ariaLabel = label
    ? `${label}: ${indeterminate ? 'Processing' : progressText}`
    : `Progress: ${indeterminate ? 'Processing' : progressText}`;

  return (
    <div className={`progress-container progress-${size}`}>
      {label && (
        <div className="progress-label">
          <span>{label}</span>
          {showPercentage && !indeterminate && (
            <span className="progress-percentage">{progressText}</span>
          )}
        </div>
      )}
      <div
        className={`progress-bar progress-${color}`}
        role="progressbar"
        aria-label={ariaLabel}
        aria-valuenow={indeterminate ? undefined : clampedProgress}
        aria-valuemin={0}
        aria-valuemax={100}
      >
        <div
          className={`progress-fill ${indeterminate ? 'progress-indeterminate' : ''}`}
          style={!indeterminate ? { width: `${clampedProgress}%` } : undefined}
        />
      </div>
      {!label && showPercentage && !indeterminate && (
        <div className="progress-percentage-standalone">{progressText}</div>
      )}
    </div>
  );
};

export default ProgressBar;