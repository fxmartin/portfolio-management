// ABOUTME: Circular gauge component to display strategy alignment score (0-10)
// ABOUTME: Features color gradient (red/yellow/green) based on score ranges

import React from 'react'
import './AlignmentScoreGauge.css'

interface AlignmentScoreGaugeProps {
  score: number
  size?: number
}

export const AlignmentScoreGauge: React.FC<AlignmentScoreGaugeProps> = ({
  score,
  size = 150
}) => {
  const formattedScore = score.toFixed(1)
  const percentage = (score / 10) * 100

  const getScoreClass = (): string => {
    if (score < 5) return 'gauge-low'
    if (score < 8) return 'gauge-medium'
    return 'gauge-high'
  }

  const getColor = (): string => {
    if (score < 5) return '#ef4444' // red
    if (score < 8) return '#f59e0b' // yellow
    return '#10b981' // green
  }

  const strokeWidth = 12
  const radius = (size / 2) - (strokeWidth / 2)
  const circumference = 2 * Math.PI * radius
  const strokeDashoffset = circumference - (percentage / 100) * circumference

  return (
    <div
      className="alignment-gauge"
      style={{ width: size, height: size }}
      role="progressbar"
      aria-valuenow={score}
      aria-valuemin={0}
      aria-valuemax={10}
      aria-label={`Strategy alignment score: ${formattedScore} out of 10`}
    >
      <svg width={size} height={size} className="gauge-svg">
        {/* Background circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="#e5e7eb"
          strokeWidth={strokeWidth}
        />
        {/* Progress circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={getColor()}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          className={`gauge-progress ${getScoreClass()}`}
          style={{
            transform: 'rotate(-90deg)',
            transformOrigin: '50% 50%',
            transition: 'stroke-dashoffset 0.5s ease'
          }}
        />
      </svg>

      {/* Score display */}
      <div className="gauge-content">
        <div className="gauge-score">{formattedScore}</div>
        <div className="gauge-label">Alignment</div>
      </div>
    </div>
  )
}
