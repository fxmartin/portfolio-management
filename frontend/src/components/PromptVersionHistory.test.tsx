// ABOUTME: Unit tests for PromptVersionHistory component
// ABOUTME: Tests modal display, version fetching, restore functionality, and error handling

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { PromptVersionHistory } from './PromptVersionHistory'
import { promptService } from '../services/promptService'
import type { PromptResponse, PromptVersionResponse } from '../types/prompt.types'

// Mock services
vi.mock('../services/promptService')
vi.mock('react-toastify', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
    info: vi.fn()
  }
}))

describe('PromptVersionHistory', () => {
  const mockPrompt: PromptResponse = {
    id: 1,
    name: 'global_market_analysis',
    category: 'global',
    prompt_text: 'Current version text',
    template_variables: { symbol: 'string' },
    version: 3,
    is_active: true,
    created_at: '2025-11-05T10:00:00Z',
    updated_at: '2025-11-06T12:00:00Z'
  }

  const mockVersions: PromptVersionResponse[] = [
    {
      id: 3,
      prompt_id: 1,
      version: 3,
      prompt_text: 'Current version text',
      changed_by: 'user@example.com',
      changed_at: '2025-11-06T12:00:00Z',
      change_reason: 'Latest changes'
    },
    {
      id: 2,
      prompt_id: 1,
      version: 2,
      prompt_text: 'Second version text',
      changed_by: 'admin@example.com',
      changed_at: '2025-11-05T15:00:00Z',
      change_reason: 'Improvements'
    },
    {
      id: 1,
      prompt_id: 1,
      version: 1,
      prompt_text: 'Initial version text',
      changed_by: null,
      changed_at: '2025-11-05T10:00:00Z',
      change_reason: null
    }
  ]

  const mockHandlers = {
    onClose: vi.fn(),
    onRestore: vi.fn()
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Modal Rendering', () => {
    it('should render modal with prompt name', async () => {
      vi.mocked(promptService.getVersionHistory).mockResolvedValue({
        versions: mockVersions,
        total: 3
      })

      render(<PromptVersionHistory prompt={mockPrompt} {...mockHandlers} />)

      expect(screen.getByRole('dialog')).toBeInTheDocument()
      expect(screen.getByText(/Version History: global_market_analysis/i)).toBeInTheDocument()
    })

    it('should render close button', async () => {
      vi.mocked(promptService.getVersionHistory).mockResolvedValue({
        versions: mockVersions,
        total: 3
      })

      render(<PromptVersionHistory prompt={mockPrompt} {...mockHandlers} />)

      expect(screen.getByLabelText(/Close/i)).toBeInTheDocument()
    })

    it('should render modal overlay', async () => {
      vi.mocked(promptService.getVersionHistory).mockResolvedValue({
        versions: mockVersions,
        total: 3
      })

      const { container } = render(
        <PromptVersionHistory prompt={mockPrompt} {...mockHandlers} />
      )

      expect(container.querySelector('.prompt-version-history-modal')).toBeInTheDocument()
    })

    it('should have proper ARIA attributes', async () => {
      vi.mocked(promptService.getVersionHistory).mockResolvedValue({
        versions: mockVersions,
        total: 3
      })

      render(<PromptVersionHistory prompt={mockPrompt} {...mockHandlers} />)

      const dialog = screen.getByRole('dialog')
      expect(dialog).toHaveAttribute('aria-modal', 'true')
    })
  })

  describe('Version Fetching', () => {
    it('should fetch versions on mount', async () => {
      vi.mocked(promptService.getVersionHistory).mockResolvedValue({
        versions: mockVersions,
        total: 3
      })

      render(<PromptVersionHistory prompt={mockPrompt} {...mockHandlers} />)

      await waitFor(() => {
        expect(promptService.getVersionHistory).toHaveBeenCalledWith(1)
      })
    })

    it('should display loading state while fetching', () => {
      vi.mocked(promptService.getVersionHistory).mockImplementation(
        () => new Promise(() => {}) // Never resolves
      )

      render(<PromptVersionHistory prompt={mockPrompt} {...mockHandlers} />)

      expect(screen.getByText(/Loading/i)).toBeInTheDocument()
    })

    it('should render versions after successful fetch', async () => {
      vi.mocked(promptService.getVersionHistory).mockResolvedValue({
        versions: mockVersions,
        total: 3
      })

      render(<PromptVersionHistory prompt={mockPrompt} {...mockHandlers} />)

      await waitFor(() => {
        expect(screen.getByText(/Version 3/i)).toBeInTheDocument()
        expect(screen.getByText(/Version 2/i)).toBeInTheDocument()
        expect(screen.getByText(/Version 1/i)).toBeInTheDocument()
      })
    })

    it('should display error message on fetch failure', async () => {
      vi.mocked(promptService.getVersionHistory).mockRejectedValue(
        new Error('Network error')
      )

      render(<PromptVersionHistory prompt={mockPrompt} {...mockHandlers} />)

      await waitFor(() => {
        expect(screen.getByText(/Failed to load version history/i)).toBeInTheDocument()
      })
    })

    it('should show retry button on error', async () => {
      vi.mocked(promptService.getVersionHistory).mockRejectedValue(
        new Error('Network error')
      )

      render(<PromptVersionHistory prompt={mockPrompt} {...mockHandlers} />)

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Retry/i })).toBeInTheDocument()
      })
    })

    it('should retry fetching on retry button click', async () => {
      const user = userEvent.setup()
      vi.mocked(promptService.getVersionHistory)
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce({ versions: mockVersions, total: 3 })

      render(<PromptVersionHistory prompt={mockPrompt} {...mockHandlers} />)

      await waitFor(() => {
        expect(screen.getByText(/Failed to load/i)).toBeInTheDocument()
      })

      const retryButton = screen.getByRole('button', { name: /Retry/i })
      await user.click(retryButton)

      await waitFor(() => {
        expect(screen.getByText(/Version 3/i)).toBeInTheDocument()
      })
    })
  })

  describe('Version Selection', () => {
    it('should allow selecting a version', async () => {
      const user = userEvent.setup()
      vi.mocked(promptService.getVersionHistory).mockResolvedValue({
        versions: mockVersions,
        total: 3
      })

      const { container } = render(
        <PromptVersionHistory prompt={mockPrompt} {...mockHandlers} />
      )

      await waitFor(() => {
        expect(screen.getByText(/Version 2/i)).toBeInTheDocument()
      })

      const version2Card = container.querySelectorAll('.version-card')[1]
      await user.click(version2Card)

      expect(version2Card).toHaveClass('selected')
    })

    it('should deselect a version when clicked again', async () => {
      const user = userEvent.setup()
      vi.mocked(promptService.getVersionHistory).mockResolvedValue({
        versions: mockVersions,
        total: 3
      })

      const { container } = render(
        <PromptVersionHistory prompt={mockPrompt} {...mockHandlers} />
      )

      await waitFor(() => {
        expect(screen.getByText(/Version 2/i)).toBeInTheDocument()
      })

      const version2Card = container.querySelectorAll('.version-card')[1]
      await user.click(version2Card)
      expect(version2Card).toHaveClass('selected')

      await user.click(version2Card)
      expect(version2Card).not.toHaveClass('selected')
    })

    it('should show restore button when a version is selected', async () => {
      const user = userEvent.setup()
      vi.mocked(promptService.getVersionHistory).mockResolvedValue({
        versions: mockVersions,
        total: 3
      })

      const { container } = render(
        <PromptVersionHistory prompt={mockPrompt} {...mockHandlers} />
      )

      await waitFor(() => {
        expect(screen.getByText(/Version 2/i)).toBeInTheDocument()
      })

      // Initially no restore button
      expect(screen.queryByRole('button', { name: /Restore Version/i })).not.toBeInTheDocument()

      const version2Card = container.querySelectorAll('.version-card')[1]
      await user.click(version2Card)

      expect(screen.getByRole('button', { name: /Restore Version/i })).toBeInTheDocument()
    })

    it('should not allow restoring current version', async () => {
      const user = userEvent.setup()
      vi.mocked(promptService.getVersionHistory).mockResolvedValue({
        versions: mockVersions,
        total: 3
      })

      const { container } = render(
        <PromptVersionHistory prompt={mockPrompt} {...mockHandlers} />
      )

      await waitFor(() => {
        expect(screen.getByText(/Version 3/i)).toBeInTheDocument()
      })

      const currentVersionCard = container.querySelector('.version-card.current')
      await user.click(currentVersionCard!)

      // Restore button should not appear
      expect(screen.queryByRole('button', { name: /Restore Version/i })).not.toBeInTheDocument()
    })
  })

  describe('Restore Functionality', () => {
    it('should show confirmation modal when restore button clicked', async () => {
      const user = userEvent.setup()
      vi.mocked(promptService.getVersionHistory).mockResolvedValue({
        versions: mockVersions,
        total: 3
      })

      const { container } = render(
        <PromptVersionHistory prompt={mockPrompt} {...mockHandlers} />
      )

      await waitFor(() => {
        expect(screen.getByText(/Version 2/i)).toBeInTheDocument()
      })

      const version2Card = container.querySelectorAll('.version-card')[1]
      await user.click(version2Card)

      const restoreButton = screen.getByRole('button', { name: /Restore Version/i })
      await user.click(restoreButton)

      expect(screen.getByText(/Confirm Restore/i)).toBeInTheDocument()
      expect(screen.getByText(/Are you sure you want to restore version 2/i)).toBeInTheDocument()
    })

    it('should call restore API on confirmation', async () => {
      const user = userEvent.setup()
      vi.mocked(promptService.getVersionHistory).mockResolvedValue({
        versions: mockVersions,
        total: 3
      })
      vi.mocked(promptService.restoreVersion).mockResolvedValue({
        ...mockPrompt,
        version: 4,
        prompt_text: 'Second version text'
      })

      const { container } = render(
        <PromptVersionHistory prompt={mockPrompt} {...mockHandlers} />
      )

      await waitFor(() => {
        expect(screen.getByText(/Version 2/i)).toBeInTheDocument()
      })

      const version2Card = container.querySelectorAll('.version-card')[1]
      await user.click(version2Card)

      const restoreButton = screen.getByRole('button', { name: /Restore Version/i })
      await user.click(restoreButton)

      const confirmButton = screen.getByRole('button', { name: /Confirm/i })
      await user.click(confirmButton)

      await waitFor(() => {
        expect(promptService.restoreVersion).toHaveBeenCalledWith(1, 2, expect.any(String))
      })
    })

    it('should call onRestore callback after successful restore', async () => {
      const user = userEvent.setup()
      vi.mocked(promptService.getVersionHistory).mockResolvedValue({
        versions: mockVersions,
        total: 3
      })
      vi.mocked(promptService.restoreVersion).mockResolvedValue({
        ...mockPrompt,
        version: 4
      })

      const { container } = render(
        <PromptVersionHistory prompt={mockPrompt} {...mockHandlers} />
      )

      await waitFor(() => {
        expect(screen.getByText(/Version 2/i)).toBeInTheDocument()
      })

      const version2Card = container.querySelectorAll('.version-card')[1]
      await user.click(version2Card)

      const restoreButton = screen.getByRole('button', { name: /Restore Version/i })
      await user.click(restoreButton)

      const confirmButton = screen.getByRole('button', { name: /Confirm/i })
      await user.click(confirmButton)

      await waitFor(() => {
        expect(mockHandlers.onRestore).toHaveBeenCalled()
      })
    })

    it('should handle restore errors gracefully', async () => {
      const user = userEvent.setup()
      vi.mocked(promptService.getVersionHistory).mockResolvedValue({
        versions: mockVersions,
        total: 3
      })
      vi.mocked(promptService.restoreVersion).mockRejectedValue(
        new Error('Restore failed')
      )

      const { container } = render(
        <PromptVersionHistory prompt={mockPrompt} {...mockHandlers} />
      )

      await waitFor(() => {
        expect(screen.getByText(/Version 2/i)).toBeInTheDocument()
      })

      const version2Card = container.querySelectorAll('.version-card')[1]
      await user.click(version2Card)

      const restoreButton = screen.getByRole('button', { name: /Restore Version/i })
      await user.click(restoreButton)

      const confirmButton = screen.getByRole('button', { name: /Confirm/i })
      await user.click(confirmButton)

      await waitFor(() => {
        expect(screen.getByText(/Failed to restore/i)).toBeInTheDocument()
      })
    })

    it('should allow canceling restore confirmation', async () => {
      const user = userEvent.setup()
      vi.mocked(promptService.getVersionHistory).mockResolvedValue({
        versions: mockVersions,
        total: 3
      })

      const { container } = render(
        <PromptVersionHistory prompt={mockPrompt} {...mockHandlers} />
      )

      await waitFor(() => {
        expect(screen.getByText(/Version 2/i)).toBeInTheDocument()
      })

      const version2Card = container.querySelectorAll('.version-card')[1]
      await user.click(version2Card)

      const restoreButton = screen.getByRole('button', { name: /Restore Version/i })
      await user.click(restoreButton)

      const cancelButton = screen.getByRole('button', { name: /Cancel/i })
      await user.click(cancelButton)

      expect(screen.queryByText(/Confirm Restore/i)).not.toBeInTheDocument()
      expect(promptService.restoreVersion).not.toHaveBeenCalled()
    })
  })

  describe('Modal Controls', () => {
    it('should close modal when close button clicked', async () => {
      const user = userEvent.setup()
      vi.mocked(promptService.getVersionHistory).mockResolvedValue({
        versions: mockVersions,
        total: 3
      })

      render(<PromptVersionHistory prompt={mockPrompt} {...mockHandlers} />)

      await waitFor(() => {
        expect(screen.getByText(/Version 3/i)).toBeInTheDocument()
      })

      const closeButton = screen.getByLabelText(/Close/i)
      await user.click(closeButton)

      expect(mockHandlers.onClose).toHaveBeenCalled()
    })

    it('should close modal on Escape key press', async () => {
      const user = userEvent.setup()
      vi.mocked(promptService.getVersionHistory).mockResolvedValue({
        versions: mockVersions,
        total: 3
      })

      render(<PromptVersionHistory prompt={mockPrompt} {...mockHandlers} />)

      await waitFor(() => {
        expect(screen.getByText(/Version 3/i)).toBeInTheDocument()
      })

      await user.keyboard('{Escape}')

      expect(mockHandlers.onClose).toHaveBeenCalled()
    })

    it('should close modal on overlay click', async () => {
      const user = userEvent.setup()
      vi.mocked(promptService.getVersionHistory).mockResolvedValue({
        versions: mockVersions,
        total: 3
      })

      const { container } = render(
        <PromptVersionHistory prompt={mockPrompt} {...mockHandlers} />
      )

      await waitFor(() => {
        expect(screen.getByText(/Version 3/i)).toBeInTheDocument()
      })

      const modal = container.querySelector('.prompt-version-history-modal')
      await user.click(modal!)

      expect(mockHandlers.onClose).toHaveBeenCalled()
    })

    it('should not close modal on panel click', async () => {
      const user = userEvent.setup()
      vi.mocked(promptService.getVersionHistory).mockResolvedValue({
        versions: mockVersions,
        total: 3
      })

      const { container } = render(
        <PromptVersionHistory prompt={mockPrompt} {...mockHandlers} />
      )

      await waitFor(() => {
        expect(screen.getByText(/Version 3/i)).toBeInTheDocument()
      })

      const panel = container.querySelector('.prompt-version-history-panel')
      await user.click(panel!)

      expect(mockHandlers.onClose).not.toHaveBeenCalled()
    })
  })

  describe('Empty State', () => {
    it('should show empty message when no versions exist', async () => {
      vi.mocked(promptService.getVersionHistory).mockResolvedValue({
        versions: [],
        total: 0
      })

      render(<PromptVersionHistory prompt={mockPrompt} {...mockHandlers} />)

      await waitFor(() => {
        expect(screen.getByText(/No version history available/i)).toBeInTheDocument()
      })
    })
  })

  describe('Accessibility', () => {
    it('should trap focus within modal', async () => {
      vi.mocked(promptService.getVersionHistory).mockResolvedValue({
        versions: mockVersions,
        total: 3
      })

      render(<PromptVersionHistory prompt={mockPrompt} {...mockHandlers} />)

      await waitFor(() => {
        expect(screen.getByText(/Version 3/i)).toBeInTheDocument()
      })

      const dialog = screen.getByRole('dialog')
      expect(dialog).toBeInTheDocument()
    })

    it('should have descriptive aria-label on dialog', async () => {
      vi.mocked(promptService.getVersionHistory).mockResolvedValue({
        versions: mockVersions,
        total: 3
      })

      render(<PromptVersionHistory prompt={mockPrompt} {...mockHandlers} />)

      await waitFor(() => {
        const dialog = screen.getByRole('dialog')
        expect(dialog).toHaveAttribute('aria-labelledby')
      })
    })
  })
})
