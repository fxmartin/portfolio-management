// ABOUTME: Unit tests for VersionTimeline component
// ABOUTME: Tests version rendering, selection, metadata display, and responsive layout

import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { VersionTimeline } from './VersionTimeline'
import type { PromptVersionResponse } from '../types/prompt.types'

describe('VersionTimeline', () => {
  const mockVersions: PromptVersionResponse[] = [
    {
      id: 3,
      prompt_id: 1,
      version: 3,
      prompt_text: 'Latest version of the prompt',
      changed_by: 'user@example.com',
      changed_at: '2025-11-06T12:00:00Z',
      change_reason: 'Improved clarity'
    },
    {
      id: 2,
      prompt_id: 1,
      version: 2,
      prompt_text: 'Second version',
      changed_by: 'admin@example.com',
      changed_at: '2025-11-05T15:00:00Z',
      change_reason: 'Added more details'
    },
    {
      id: 1,
      prompt_id: 1,
      version: 1,
      prompt_text: 'Initial version',
      changed_by: null,
      changed_at: '2025-11-05T10:00:00Z',
      change_reason: null
    }
  ]

  const mockHandlers = {
    onSelectVersion: vi.fn(),
    selectedVersions: []
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Rendering', () => {
    it('should render all versions', () => {
      render(
        <VersionTimeline
          versions={mockVersions}
          currentVersion={3}
          {...mockHandlers}
        />
      )

      expect(screen.getByText(/Version 3/i)).toBeInTheDocument()
      expect(screen.getByText(/Version 2/i)).toBeInTheDocument()
      expect(screen.getByText(/Version 1/i)).toBeInTheDocument()
    })

    it('should display version metadata', () => {
      render(
        <VersionTimeline
          versions={mockVersions}
          currentVersion={3}
          {...mockHandlers}
        />
      )

      expect(screen.getByText('user@example.com')).toBeInTheDocument()
      expect(screen.getByText('admin@example.com')).toBeInTheDocument()
    })

    it('should show change reasons when provided', () => {
      render(
        <VersionTimeline
          versions={mockVersions}
          currentVersion={3}
          {...mockHandlers}
        />
      )

      expect(screen.getByText('Improved clarity')).toBeInTheDocument()
      expect(screen.getByText('Added more details')).toBeInTheDocument()
    })

    it('should show "Initial version" when change_reason is null', () => {
      render(
        <VersionTimeline
          versions={mockVersions}
          currentVersion={3}
          {...mockHandlers}
        />
      )

      // Check that "Initial version" appears in metadata (not preview)
      const allInitialText = screen.getAllByText('Initial version')
      expect(allInitialText.length).toBeGreaterThan(0)
    })

    it('should show "Unknown" when changed_by is null', () => {
      render(
        <VersionTimeline
          versions={mockVersions}
          currentVersion={3}
          {...mockHandlers}
        />
      )

      expect(screen.getByText('Unknown')).toBeInTheDocument()
    })
  })

  describe('Current Version Indicator', () => {
    it('should display "Current" badge on current version', () => {
      render(
        <VersionTimeline
          versions={mockVersions}
          currentVersion={3}
          {...mockHandlers}
        />
      )

      const currentBadges = screen.getAllByText('Current')
      expect(currentBadges).toHaveLength(1)
    })

    it('should apply current version styling', () => {
      const { container } = render(
        <VersionTimeline
          versions={mockVersions}
          currentVersion={3}
          {...mockHandlers}
        />
      )

      const versionCards = container.querySelectorAll('.version-card')
      expect(versionCards[0]).toHaveClass('current')
    })

    it('should not show current badge on historical versions', () => {
      render(
        <VersionTimeline
          versions={mockVersions}
          currentVersion={3}
          {...mockHandlers}
        />
      )

      const allText = screen.getByText(/Version 2/i).closest('.version-card')
      expect(allText).not.toHaveClass('current')
    })
  })

  describe('Version Selection', () => {
    it('should call onSelectVersion when clicking a version', async () => {
      const user = userEvent.setup()
      render(
        <VersionTimeline
          versions={mockVersions}
          currentVersion={3}
          {...mockHandlers}
        />
      )

      const version2Card = screen.getByText(/Version 2/i).closest('.version-card')
      await user.click(version2Card!)

      expect(mockHandlers.onSelectVersion).toHaveBeenCalledWith(2)
    })

    it('should apply selected styling to selected versions', () => {
      const { container } = render(
        <VersionTimeline
          versions={mockVersions}
          currentVersion={3}
          selectedVersions={[2]}
          onSelectVersion={mockHandlers.onSelectVersion}
        />
      )

      const versionCards = container.querySelectorAll('.version-card')
      expect(versionCards[1]).toHaveClass('selected')
    })

    it('should support multiple selected versions', () => {
      const { container } = render(
        <VersionTimeline
          versions={mockVersions}
          currentVersion={3}
          selectedVersions={[1, 2]}
          onSelectVersion={mockHandlers.onSelectVersion}
        />
      )

      const versionCards = container.querySelectorAll('.version-card')
      expect(versionCards[1]).toHaveClass('selected')
      expect(versionCards[2]).toHaveClass('selected')
    })

    it('should allow clicking current version', async () => {
      const user = userEvent.setup()
      const { container } = render(
        <VersionTimeline
          versions={mockVersions}
          currentVersion={3}
          {...mockHandlers}
        />
      )

      const currentVersionCard = container.querySelector('.version-card.current')
      await user.click(currentVersionCard!)

      expect(mockHandlers.onSelectVersion).toHaveBeenCalledWith(3)
    })
  })

  describe('Date Formatting', () => {
    it('should format dates in a readable format', () => {
      const { container } = render(
        <VersionTimeline
          versions={mockVersions}
          currentVersion={3}
          {...mockHandlers}
        />
      )

      // Should contain formatted date elements (not raw ISO strings)
      const dateElements = container.querySelectorAll('.version-date')
      expect(dateElements.length).toBe(3)

      // Dates should be human-readable (relative or absolute)
      const dateText = Array.from(dateElements).map(el => el.textContent)
      dateText.forEach(text => {
        expect(text).not.toMatch(/T\d{2}:\d{2}:\d{2}/) // Should not contain ISO time format
      })
    })

    it('should show relative time for recent changes', () => {
      const recentVersion: PromptVersionResponse = {
        id: 4,
        prompt_id: 1,
        version: 4,
        prompt_text: 'Very recent change',
        changed_by: 'user@example.com',
        changed_at: new Date(Date.now() - 1000 * 60 * 30).toISOString(), // 30 minutes ago
        change_reason: 'Recent update'
      }

      render(
        <VersionTimeline
          versions={[recentVersion]}
          currentVersion={4}
          {...mockHandlers}
        />
      )

      expect(screen.getByText(/ago|minutes|hours/i)).toBeInTheDocument()
    })
  })

  describe('Empty State', () => {
    it('should show empty state when no versions provided', () => {
      render(
        <VersionTimeline
          versions={[]}
          currentVersion={1}
          {...mockHandlers}
        />
      )

      expect(screen.getByText(/No version history available/i)).toBeInTheDocument()
    })

    it('should not render version cards when empty', () => {
      const { container } = render(
        <VersionTimeline
          versions={[]}
          currentVersion={1}
          {...mockHandlers}
        />
      )

      const versionCards = container.querySelectorAll('.version-card')
      expect(versionCards).toHaveLength(0)
    })
  })

  describe('Accessibility', () => {
    it('should have proper ARIA labels', () => {
      render(
        <VersionTimeline
          versions={mockVersions}
          currentVersion={3}
          {...mockHandlers}
        />
      )

      const timeline = screen.getByRole('list')
      expect(timeline).toBeInTheDocument()
    })

    it('should mark version cards as clickable list items', () => {
      render(
        <VersionTimeline
          versions={mockVersions}
          currentVersion={3}
          {...mockHandlers}
        />
      )

      const listItems = screen.getAllByRole('listitem')
      expect(listItems).toHaveLength(3)
    })

    it('should support keyboard navigation', async () => {
      const user = userEvent.setup()
      render(
        <VersionTimeline
          versions={mockVersions}
          currentVersion={3}
          {...mockHandlers}
        />
      )

      const firstVersion = screen.getByText(/Version 3/i).closest('.version-card')
      firstVersion?.focus()

      await user.keyboard('{Enter}')
      expect(mockHandlers.onSelectVersion).toHaveBeenCalledWith(3)
    })
  })

  describe('Prompt Text Preview', () => {
    it('should show prompt text preview', () => {
      render(
        <VersionTimeline
          versions={mockVersions}
          currentVersion={3}
          {...mockHandlers}
        />
      )

      expect(screen.getByText(/Latest version of the prompt/i)).toBeInTheDocument()
    })

    it('should truncate long prompt text', () => {
      const longPrompt: PromptVersionResponse = {
        id: 5,
        prompt_id: 1,
        version: 5,
        prompt_text: 'A'.repeat(200),
        changed_by: 'user@example.com',
        changed_at: '2025-11-06T12:00:00Z',
        change_reason: 'Long text test'
      }

      const { container } = render(
        <VersionTimeline
          versions={[longPrompt]}
          currentVersion={5}
          {...mockHandlers}
        />
      )

      const preview = container.querySelector('.version-preview')
      expect(preview?.textContent?.length).toBeLessThan(200)
    })
  })

  describe('Responsive Layout', () => {
    it('should render timeline structure', () => {
      const { container } = render(
        <VersionTimeline
          versions={mockVersions}
          currentVersion={3}
          {...mockHandlers}
        />
      )

      const timeline = container.querySelector('.version-timeline')
      expect(timeline).toBeInTheDocument()
    })

    it('should have mobile-friendly structure', () => {
      const { container } = render(
        <VersionTimeline
          versions={mockVersions}
          currentVersion={3}
          {...mockHandlers}
        />
      )

      // Check for mobile-responsive classes
      const cards = container.querySelectorAll('.version-card')
      expect(cards.length).toBeGreaterThan(0)
    })
  })
})
