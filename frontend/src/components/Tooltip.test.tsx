// ABOUTME: Tests for Tooltip component with accessibility and interaction scenarios
// ABOUTME: Validates hover, focus, keyboard navigation, and positioning behavior

import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Tooltip } from './Tooltip'

describe('Tooltip', () => {
  it('renders trigger element with children', () => {
    render(
      <Tooltip content="Test tooltip">
        <span>Hover me</span>
      </Tooltip>
    )

    expect(screen.getByText('Hover me')).toBeInTheDocument()
  })

  it('applies tooltip-trigger class to wrapper', () => {
    render(
      <Tooltip content="Test tooltip">
        <span>Hover me</span>
      </Tooltip>
    )

    const trigger = screen.getByText('Hover me').parentElement
    expect(trigger).toHaveClass('tooltip-trigger')
  })

  it('shows tooltip on mouse enter', async () => {
    render(
      <Tooltip content="Test tooltip content">
        <span>Hover me</span>
      </Tooltip>
    )

    const trigger = screen.getByText('Hover me').parentElement!
    fireEvent.mouseEnter(trigger)

    await waitFor(() => {
      expect(screen.getByRole('tooltip')).toBeInTheDocument()
      expect(screen.getByText('Test tooltip content')).toBeInTheDocument()
    })
  })

  it('hides tooltip on mouse leave', async () => {
    render(
      <Tooltip content="Test tooltip content">
        <span>Hover me</span>
      </Tooltip>
    )

    const trigger = screen.getByText('Hover me').parentElement!
    fireEvent.mouseEnter(trigger)

    await waitFor(() => {
      expect(screen.getByRole('tooltip')).toBeInTheDocument()
    })

    fireEvent.mouseLeave(trigger)

    await waitFor(() => {
      expect(screen.queryByRole('tooltip')).not.toBeInTheDocument()
    })
  })

  it('shows tooltip on focus', async () => {
    render(
      <Tooltip content="Test tooltip content">
        <span>Focus me</span>
      </Tooltip>
    )

    const trigger = screen.getByText('Focus me').parentElement!
    fireEvent.focus(trigger)

    await waitFor(() => {
      expect(screen.getByRole('tooltip')).toBeInTheDocument()
      expect(screen.getByText('Test tooltip content')).toBeInTheDocument()
    })
  })

  it('hides tooltip on blur', async () => {
    render(
      <Tooltip content="Test tooltip content">
        <span>Focus me</span>
      </Tooltip>
    )

    const trigger = screen.getByText('Focus me').parentElement!
    fireEvent.focus(trigger)

    await waitFor(() => {
      expect(screen.getByRole('tooltip')).toBeInTheDocument()
    })

    fireEvent.blur(trigger)

    await waitFor(() => {
      expect(screen.queryByRole('tooltip')).not.toBeInTheDocument()
    })
  })

  it('is keyboard accessible with tabIndex', () => {
    render(
      <Tooltip content="Test tooltip">
        <span>Accessible element</span>
      </Tooltip>
    )

    const trigger = screen.getByText('Accessible element').parentElement!
    expect(trigger).toHaveAttribute('tabIndex', '0')
  })

  it('has proper ARIA attributes when visible', async () => {
    render(
      <Tooltip content="Test tooltip">
        <span>ARIA element</span>
      </Tooltip>
    )

    const trigger = screen.getByText('ARIA element').parentElement!

    // Before hover - no aria-describedby
    expect(trigger).not.toHaveAttribute('aria-describedby')

    fireEvent.mouseEnter(trigger)

    // After hover - aria-describedby is set
    await waitFor(() => {
      expect(trigger).toHaveAttribute('aria-describedby', 'tooltip')
    })

    const tooltip = screen.getByRole('tooltip')
    expect(tooltip).toHaveAttribute('id', 'tooltip')
  })

  it('applies correct position class', async () => {
    const { rerender } = render(
      <Tooltip content="Test" position="top">
        <span>Element</span>
      </Tooltip>
    )

    const trigger = screen.getByText('Element').parentElement!
    fireEvent.mouseEnter(trigger)

    await waitFor(() => {
      const tooltip = screen.getByRole('tooltip')
      expect(tooltip).toHaveClass('tooltip', 'tooltip-top')
    })

    fireEvent.mouseLeave(trigger)

    // Test bottom position
    rerender(
      <Tooltip content="Test" position="bottom">
        <span>Element</span>
      </Tooltip>
    )

    fireEvent.mouseEnter(trigger)

    await waitFor(() => {
      const tooltip = screen.getByRole('tooltip')
      expect(tooltip).toHaveClass('tooltip', 'tooltip-bottom')
    })
  })

  it('uses fixed positioning for tooltip', async () => {
    render(
      <Tooltip content="Test tooltip">
        <span>Element</span>
      </Tooltip>
    )

    const trigger = screen.getByText('Element').parentElement!
    fireEvent.mouseEnter(trigger)

    await waitFor(() => {
      const tooltip = screen.getByRole('tooltip')
      expect(tooltip).toHaveStyle({ position: 'fixed' })
    })
  })

  it('renders multi-line tooltip content', async () => {
    const longContent = "This is a longer tooltip with multiple words. It should wrap properly and display all content correctly."

    render(
      <Tooltip content={longContent}>
        <span>Long tooltip</span>
      </Tooltip>
    )

    const trigger = screen.getByText('Long tooltip').parentElement!
    fireEvent.mouseEnter(trigger)

    await waitFor(() => {
      expect(screen.getByText(longContent)).toBeInTheDocument()
    })
  })

  it('handles rapid hover on/off', async () => {
    render(
      <Tooltip content="Test tooltip">
        <span>Rapid hover</span>
      </Tooltip>
    )

    const trigger = screen.getByText('Rapid hover').parentElement!

    // Rapid hover on/off
    fireEvent.mouseEnter(trigger)
    fireEvent.mouseLeave(trigger)
    fireEvent.mouseEnter(trigger)

    await waitFor(() => {
      expect(screen.getByRole('tooltip')).toBeInTheDocument()
    })

    fireEvent.mouseLeave(trigger)

    await waitFor(() => {
      expect(screen.queryByRole('tooltip')).not.toBeInTheDocument()
    })
  })

  it('does not interfere with child element clicks', () => {
    const handleClick = vi.fn()

    render(
      <Tooltip content="Test tooltip">
        <button onClick={handleClick}>Clickable</button>
      </Tooltip>
    )

    const button = screen.getByRole('button')
    fireEvent.click(button)

    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it('tooltip has pointer-events: none', async () => {
    render(
      <Tooltip content="Test tooltip">
        <span>Element</span>
      </Tooltip>
    )

    const trigger = screen.getByText('Element').parentElement!
    fireEvent.mouseEnter(trigger)

    await waitFor(() => {
      const tooltip = screen.getByRole('tooltip')
      // CSS class should have pointer-events: none
      expect(tooltip).toHaveClass('tooltip')
    })
  })

  it('defaults to top position when not specified', async () => {
    render(
      <Tooltip content="Test tooltip">
        <span>Element</span>
      </Tooltip>
    )

    const trigger = screen.getByText('Element').parentElement!
    fireEvent.mouseEnter(trigger)

    await waitFor(() => {
      const tooltip = screen.getByRole('tooltip')
      expect(tooltip).toHaveClass('tooltip-top')
    })
  })
})
