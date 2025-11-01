// ABOUTME: Test suite for AlignmentScoreGauge component
// ABOUTME: Tests circular gauge visualization with color gradients and accessibility

import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { AlignmentScoreGauge } from './AlignmentScoreGauge'

describe('AlignmentScoreGauge', () => {
  it('should render gauge with score', () => {
    render(<AlignmentScoreGauge score={7.5} />)

    expect(screen.getByText('7.5')).toBeInTheDocument()
    expect(screen.getByText('Strategy Alignment')).toBeInTheDocument()
  })

  it('should render low score (red) correctly', () => {
    const { container } = render(<AlignmentScoreGauge score={3} />)

    expect(screen.getByText('3.0')).toBeInTheDocument()

    const gauge = container.querySelector('.gauge-progress')
    expect(gauge).toHaveClass('gauge-low')
  })

  it('should render medium score (yellow) correctly', () => {
    const { container } = render(<AlignmentScoreGauge score={6} />)

    expect(screen.getByText('6.0')).toBeInTheDocument()

    const gauge = container.querySelector('.gauge-progress')
    expect(gauge).toHaveClass('gauge-medium')
  })

  it('should render high score (green) correctly', () => {
    const { container } = render(<AlignmentScoreGauge score={9} />)

    expect(screen.getByText('9.0')).toBeInTheDocument()

    const gauge = container.querySelector('.gauge-progress')
    expect(gauge).toHaveClass('gauge-high')
  })

  it('should handle zero score', () => {
    render(<AlignmentScoreGauge score={0} />)

    expect(screen.getByText('0.0')).toBeInTheDocument()
  })

  it('should handle perfect score', () => {
    render(<AlignmentScoreGauge score={10} />)

    expect(screen.getByText('10.0')).toBeInTheDocument()
  })

  it('should format score to one decimal place', () => {
    render(<AlignmentScoreGauge score={7.456} />)

    expect(screen.getByText('7.5')).toBeInTheDocument()
  })

  it('should have proper ARIA attributes', () => {
    const { container } = render(<AlignmentScoreGauge score={8.2} />)

    const gauge = container.querySelector('[role="progressbar"]')
    expect(gauge).toBeInTheDocument()
    expect(gauge).toHaveAttribute('aria-valuenow', '8.2')
    expect(gauge).toHaveAttribute('aria-valuemin', '0')
    expect(gauge).toHaveAttribute('aria-valuemax', '10')
    expect(gauge).toHaveAttribute('aria-label', 'Strategy alignment score: 8.2 out of 10')
  })

  it('should render custom size when provided', () => {
    const { container } = render(<AlignmentScoreGauge score={7} size={200} />)

    const gaugeContainer = container.querySelector('.alignment-gauge')
    expect(gaugeContainer).toHaveStyle({ width: '200px', height: '200px' })
  })

  it('should use default size when not provided', () => {
    const { container } = render(<AlignmentScoreGauge score={7} />)

    const gaugeContainer = container.querySelector('.alignment-gauge')
    expect(gaugeContainer).toHaveStyle({ width: '150px', height: '150px' })
  })
})
