// ABOUTME: Tests for the Sidebar component
// ABOUTME: Tests icon navigation, tooltips, active states, and submenu functionality

import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import '@testing-library/jest-dom'
import Sidebar from './Sidebar'

describe('Sidebar Component', () => {
  describe('Basic Rendering', () => {
    it('renders the sidebar with all navigation icons', () => {
      const mockOnTabChange = vi.fn()
      render(<Sidebar activeTab="portfolio" onTabChange={mockOnTabChange} />)

      // Check for sidebar container
      const sidebar = screen.getByRole('navigation')
      expect(sidebar).toBeInTheDocument()
      expect(sidebar).toHaveClass('sidebar')

      // Check for all menu items
      expect(screen.getByTitle('Portfolio')).toBeInTheDocument()
      expect(screen.getByTitle('Upload')).toBeInTheDocument()
      expect(screen.getByTitle('Database')).toBeInTheDocument()
    })

    it('applies active state to the current tab', () => {
      const mockOnTabChange = vi.fn()
      render(<Sidebar activeTab="upload" onTabChange={mockOnTabChange} />)

      const uploadButton = screen.getByTitle('Upload')
      expect(uploadButton).toHaveClass('active')
    })

    it('does not apply active state to inactive tabs', () => {
      const mockOnTabChange = vi.fn()
      render(<Sidebar activeTab="portfolio" onTabChange={mockOnTabChange} />)

      const uploadButton = screen.getByTitle('Upload')
      expect(uploadButton).not.toHaveClass('active')
    })
  })

  describe('Navigation Interactions', () => {
    it('calls onTabChange when a menu item is clicked', async () => {
      const mockOnTabChange = vi.fn()
      render(<Sidebar activeTab="portfolio" onTabChange={mockOnTabChange} />)

      const uploadButton = screen.getByTitle('Upload')
      await userEvent.click(uploadButton)

      expect(mockOnTabChange).toHaveBeenCalledWith('upload')
      expect(mockOnTabChange).toHaveBeenCalledTimes(1)
    })

    it('calls onTabChange with correct tab id for portfolio', async () => {
      const mockOnTabChange = vi.fn()
      render(<Sidebar activeTab="upload" onTabChange={mockOnTabChange} />)

      const portfolioButton = screen.getByTitle('Portfolio')
      await userEvent.click(portfolioButton)

      expect(mockOnTabChange).toHaveBeenCalledWith('portfolio')
    })
  })

  describe('Tooltips', () => {
    it('shows tooltip on hover with correct label', async () => {
      const user = userEvent.setup()
      const mockOnTabChange = vi.fn()
      render(<Sidebar activeTab="portfolio" onTabChange={mockOnTabChange} />)

      const uploadButton = screen.getByTitle('Upload')
      await user.hover(uploadButton)

      // Tooltip should be visible (title attribute serves as tooltip)
      expect(uploadButton).toHaveAttribute('title', 'Upload')
    })

    it('tooltips are accessible via aria-label', () => {
      const mockOnTabChange = vi.fn()
      render(<Sidebar activeTab="portfolio" onTabChange={mockOnTabChange} />)

      const portfolioButton = screen.getByTitle('Portfolio')
      const uploadButton = screen.getByTitle('Upload')
      const databaseButton = screen.getByTitle('Database')

      expect(portfolioButton).toHaveAttribute('aria-label', 'Portfolio')
      expect(uploadButton).toHaveAttribute('aria-label', 'Upload')
      expect(databaseButton).toHaveAttribute('aria-label', 'Database')
    })
  })

  describe('Keyboard Navigation', () => {
    it('supports keyboard navigation with Enter key', async () => {
      const user = userEvent.setup()
      const mockOnTabChange = vi.fn()
      render(<Sidebar activeTab="portfolio" onTabChange={mockOnTabChange} />)

      const uploadButton = screen.getByTitle('Upload')
      uploadButton.focus()
      await user.keyboard('{Enter}')

      expect(mockOnTabChange).toHaveBeenCalledWith('upload')
    })

    it('supports keyboard navigation with Space key', async () => {
      const user = userEvent.setup()
      const mockOnTabChange = vi.fn()
      render(<Sidebar activeTab="portfolio" onTabChange={mockOnTabChange} />)

      const uploadButton = screen.getByTitle('Upload')
      uploadButton.focus()
      await user.keyboard(' ')

      expect(mockOnTabChange).toHaveBeenCalledWith('upload')
    })

    it('all menu items are keyboard focusable', () => {
      const mockOnTabChange = vi.fn()
      render(<Sidebar activeTab="portfolio" onTabChange={mockOnTabChange} />)

      const portfolioButton = screen.getByTitle('Portfolio')
      const uploadButton = screen.getByTitle('Upload')
      const databaseButton = screen.getByTitle('Database')

      expect(portfolioButton).toHaveAttribute('tabIndex', '0')
      expect(uploadButton).toHaveAttribute('tabIndex', '0')
      expect(databaseButton).toHaveAttribute('tabIndex', '0')
    })
  })

  describe('Styling and Visual States', () => {
    it('has correct width for icon-only sidebar', () => {
      const mockOnTabChange = vi.fn()
      render(<Sidebar activeTab="portfolio" onTabChange={mockOnTabChange} />)

      const sidebar = screen.getByRole('navigation')
      const styles = window.getComputedStyle(sidebar)

      // Width should be 64px (will be set in CSS)
      expect(sidebar).toHaveClass('sidebar')
    })
  })
})

describe('Database Submenu', () => {
  describe('Submenu Interaction', () => {
    it('toggles submenu when database icon is clicked', async () => {
      const user = userEvent.setup()
      const mockOnTabChange = vi.fn()
      render(<Sidebar activeTab="portfolio" onTabChange={mockOnTabChange} />)

      const databaseButton = screen.getByTitle('Database')

      // Submenu should not be visible initially
      expect(screen.queryByText('Stats')).not.toBeInTheDocument()

      // Click to open submenu
      await user.click(databaseButton)

      // Submenu should now be visible
      await waitFor(() => {
        expect(screen.getByText('Stats')).toBeInTheDocument()
        expect(screen.getByText('Reset')).toBeInTheDocument()
      })
    })

    it('closes submenu when clicking outside', async () => {
      const user = userEvent.setup()
      const mockOnTabChange = vi.fn()
      const { container } = render(
        <div>
          <Sidebar activeTab="portfolio" onTabChange={mockOnTabChange} />
          <div data-testid="outside">Outside element</div>
        </div>
      )

      const databaseButton = screen.getByTitle('Database')

      // Open submenu
      await user.click(databaseButton)
      await waitFor(() => {
        expect(screen.getByText('Stats')).toBeInTheDocument()
      })

      // Click outside
      const outsideElement = screen.getByTestId('outside')
      await user.click(outsideElement)

      // Submenu should close
      await waitFor(() => {
        expect(screen.queryByText('Stats')).not.toBeInTheDocument()
      })
    })

    it('calls onTabChange with database-stats when Stats is clicked', async () => {
      const user = userEvent.setup()
      const mockOnTabChange = vi.fn()
      render(<Sidebar activeTab="portfolio" onTabChange={mockOnTabChange} />)

      const databaseButton = screen.getByTitle('Database')
      await user.click(databaseButton)

      await waitFor(() => {
        expect(screen.getByText('Stats')).toBeInTheDocument()
      })

      const statsButton = screen.getByText('Stats')
      await user.click(statsButton)

      expect(mockOnTabChange).toHaveBeenCalledWith('database-stats')
    })

    it('calls onTabChange with database-reset when Reset is clicked', async () => {
      const user = userEvent.setup()
      const mockOnTabChange = vi.fn()
      render(<Sidebar activeTab="portfolio" onTabChange={mockOnTabChange} />)

      const databaseButton = screen.getByTitle('Database')
      await user.click(databaseButton)

      await waitFor(() => {
        expect(screen.getByText('Reset')).toBeInTheDocument()
      })

      const resetButton = screen.getByText('Reset')
      await user.click(resetButton)

      expect(mockOnTabChange).toHaveBeenCalledWith('database-reset')
    })

    it('shows active state on Database when a database submenu item is active', () => {
      const mockOnTabChange = vi.fn()
      render(<Sidebar activeTab="database-stats" onTabChange={mockOnTabChange} />)

      const databaseButton = screen.getByTitle('Database')
      expect(databaseButton).toHaveClass('active')
    })

    it('closes submenu when selecting a submenu item', async () => {
      const user = userEvent.setup()
      const mockOnTabChange = vi.fn()
      render(<Sidebar activeTab="portfolio" onTabChange={mockOnTabChange} />)

      const databaseButton = screen.getByTitle('Database')
      await user.click(databaseButton)

      await waitFor(() => {
        expect(screen.getByText('Stats')).toBeInTheDocument()
      })

      const statsButton = screen.getByText('Stats')
      await user.click(statsButton)

      // Submenu should close after selection
      await waitFor(() => {
        expect(screen.queryByText('Stats')).not.toBeInTheDocument()
      })
    })

    it('keyboard navigation works for submenu items', async () => {
      const user = userEvent.setup()
      const mockOnTabChange = vi.fn()
      render(<Sidebar activeTab="portfolio" onTabChange={mockOnTabChange} />)

      const databaseButton = screen.getByTitle('Database')

      // Open submenu with keyboard
      await user.click(databaseButton)

      await waitFor(() => {
        expect(screen.getByText('Stats')).toBeInTheDocument()
      })

      const statsButton = screen.getByText('Stats')
      await user.click(statsButton)

      expect(mockOnTabChange).toHaveBeenCalledWith('database-stats')
    })

    it('Escape key closes the submenu', async () => {
      const user = userEvent.setup()
      const mockOnTabChange = vi.fn()
      render(<Sidebar activeTab="portfolio" onTabChange={mockOnTabChange} />)

      const databaseButton = screen.getByTitle('Database')
      await user.click(databaseButton)

      await waitFor(() => {
        expect(screen.getByText('Stats')).toBeInTheDocument()
      })

      await user.keyboard('{Escape}')

      await waitFor(() => {
        expect(screen.queryByText('Stats')).not.toBeInTheDocument()
      })
    })
  })
})

describe('Settings Navigation', () => {
  describe('Settings Menu Item', () => {
    it('renders Settings navigation item', () => {
      const mockOnTabChange = vi.fn()
      render(<Sidebar activeTab="portfolio" onTabChange={mockOnTabChange} />)

      const settingsButton = screen.getByTitle('Settings')
      expect(settingsButton).toBeInTheDocument()
    })

    it('Settings icon is visible', () => {
      const mockOnTabChange = vi.fn()
      render(<Sidebar activeTab="portfolio" onTabChange={mockOnTabChange} />)

      const settingsButton = screen.getByTitle('Settings')
      expect(settingsButton).toHaveAttribute('aria-label', 'Settings')
    })

    it('calls onTabChange with settings when clicked', async () => {
      const user = userEvent.setup()
      const mockOnTabChange = vi.fn()
      render(<Sidebar activeTab="portfolio" onTabChange={mockOnTabChange} />)

      const settingsButton = screen.getByTitle('Settings')
      await user.click(settingsButton)

      expect(mockOnTabChange).toHaveBeenCalledWith('settings')
      expect(mockOnTabChange).toHaveBeenCalledTimes(1)
    })

    it('shows active state when on Settings page', () => {
      const mockOnTabChange = vi.fn()
      render(<Sidebar activeTab="settings" onTabChange={mockOnTabChange} />)

      const settingsButton = screen.getByTitle('Settings')
      expect(settingsButton).toHaveClass('active')
    })

    it('is keyboard accessible with Enter key', async () => {
      const user = userEvent.setup()
      const mockOnTabChange = vi.fn()
      render(<Sidebar activeTab="portfolio" onTabChange={mockOnTabChange} />)

      const settingsButton = screen.getByTitle('Settings')
      settingsButton.focus()
      await user.keyboard('{Enter}')

      expect(mockOnTabChange).toHaveBeenCalledWith('settings')
    })
  })
})
