// ABOUTME: Tests for the TabView component
// ABOUTME: Tests tab switching, transitions, and content rendering

import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import TabView from './TabView'

describe('TabView Component', () => {
  describe('Basic Rendering', () => {
    it('renders the TabView container', () => {
      const { container } = render(
        <TabView activeTab="portfolio">
          <div data-tab="portfolio">Portfolio Content</div>
        </TabView>
      )

      expect(container.querySelector('.tab-view')).toBeInTheDocument()
    })

    it('renders active tab content', () => {
      render(
        <TabView activeTab="portfolio">
          <div data-tab="portfolio">Portfolio Content</div>
          <div data-tab="upload">Upload Content</div>
        </TabView>
      )

      expect(screen.getByText('Portfolio Content')).toBeInTheDocument()
      expect(screen.queryByText('Upload Content')).not.toBeInTheDocument()
    })

    it('does not render inactive tabs', () => {
      render(
        <TabView activeTab="upload">
          <div data-tab="portfolio">Portfolio Content</div>
          <div data-tab="upload">Upload Content</div>
        </TabView>
      )

      expect(screen.queryByText('Portfolio Content')).not.toBeInTheDocument()
      expect(screen.getByText('Upload Content')).toBeInTheDocument()
    })
  })

  describe('Tab Switching', () => {
    it('switches content when activeTab prop changes', async () => {
      const { rerender } = render(
        <TabView activeTab="portfolio">
          <div data-tab="portfolio">Portfolio Content</div>
          <div data-tab="upload">Upload Content</div>
        </TabView>
      )

      expect(screen.getByText('Portfolio Content')).toBeInTheDocument()

      rerender(
        <TabView activeTab="upload">
          <div data-tab="portfolio">Portfolio Content</div>
          <div data-tab="upload">Upload Content</div>
        </TabView>
      )

      await waitFor(() => {
        expect(screen.getByText('Upload Content')).toBeInTheDocument()
        expect(screen.queryByText('Portfolio Content')).not.toBeInTheDocument()
      })
    })

    it('handles switching between all three main tabs', async () => {
      const { rerender } = render(
        <TabView activeTab="portfolio">
          <div data-tab="portfolio">Portfolio Content</div>
          <div data-tab="upload">Upload Content</div>
          <div data-tab="database-stats">Database Stats Content</div>
        </TabView>
      )

      expect(screen.getByText('Portfolio Content')).toBeInTheDocument()

      // Switch to upload
      rerender(
        <TabView activeTab="upload">
          <div data-tab="portfolio">Portfolio Content</div>
          <div data-tab="upload">Upload Content</div>
          <div data-tab="database-stats">Database Stats Content</div>
        </TabView>
      )

      await waitFor(() => {
        expect(screen.getByText('Upload Content')).toBeInTheDocument()
      })

      // Switch to database
      rerender(
        <TabView activeTab="database-stats">
          <div data-tab="portfolio">Portfolio Content</div>
          <div data-tab="upload">Upload Content</div>
          <div data-tab="database-stats">Database Stats Content</div>
        </TabView>
      )

      await waitFor(() => {
        expect(screen.getByText('Database Stats Content')).toBeInTheDocument()
      })
    })

    it('handles rapid tab switching without errors', async () => {
      const { rerender } = render(
        <TabView activeTab="portfolio">
          <div data-tab="portfolio">Portfolio Content</div>
          <div data-tab="upload">Upload Content</div>
          <div data-tab="database-stats">Stats Content</div>
        </TabView>
      )

      // Rapidly switch tabs
      rerender(
        <TabView activeTab="upload">
          <div data-tab="portfolio">Portfolio Content</div>
          <div data-tab="upload">Upload Content</div>
          <div data-tab="database-stats">Stats Content</div>
        </TabView>
      )

      rerender(
        <TabView activeTab="database-stats">
          <div data-tab="portfolio">Portfolio Content</div>
          <div data-tab="upload">Upload Content</div>
          <div data-tab="database-stats">Stats Content</div>
        </TabView>
      )

      rerender(
        <TabView activeTab="portfolio">
          <div data-tab="portfolio">Portfolio Content</div>
          <div data-tab="upload">Upload Content</div>
          <div data-tab="database-stats">Stats Content</div>
        </TabView>
      )

      await waitFor(() => {
        expect(screen.getByText('Portfolio Content')).toBeInTheDocument()
      })
    })
  })

  describe('Content Management', () => {
    it('only renders one tab content at a time', () => {
      const { container } = render(
        <TabView activeTab="portfolio">
          <div data-tab="portfolio">Portfolio Content</div>
          <div data-tab="upload">Upload Content</div>
          <div data-tab="database-stats">Stats Content</div>
        </TabView>
      )

      const tabPanels = container.querySelectorAll('.tab-panel')
      expect(tabPanels).toHaveLength(1)
    })

    it('preserves tab content structure on switch', async () => {
      const { rerender } = render(
        <TabView activeTab="portfolio">
          <div data-tab="portfolio">
            <h2>Portfolio</h2>
            <p>Content</p>
          </div>
          <div data-tab="upload">
            <h2>Upload</h2>
            <p>Content</p>
          </div>
        </TabView>
      )

      rerender(
        <TabView activeTab="upload">
          <div data-tab="portfolio">
            <h2>Portfolio</h2>
            <p>Content</p>
          </div>
          <div data-tab="upload">
            <h2>Upload</h2>
            <p>Content</p>
          </div>
        </TabView>
      )

      await waitFor(() => {
        expect(screen.getByText('Upload')).toBeInTheDocument()
      })

      const heading = screen.getByRole('heading', { level: 2 })
      expect(heading).toHaveTextContent('Upload')
    })

    it('handles tabs with complex nested components', () => {
      const ComplexComponent = () => (
        <div>
          <h1>Title</h1>
          <div className="nested">
            <button>Action</button>
            <input type="text" placeholder="Test" />
          </div>
        </div>
      )

      render(
        <TabView activeTab="portfolio">
          <div data-tab="portfolio">
            <ComplexComponent />
          </div>
        </TabView>
      )

      expect(screen.getByText('Title')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Action' })).toBeInTheDocument()
      expect(screen.getByPlaceholderText('Test')).toBeInTheDocument()
    })
  })

  describe('Edge Cases', () => {
    it('handles undefined activeTab gracefully', () => {
      const { container } = render(
        <TabView activeTab="">
          <div data-tab="portfolio">Portfolio Content</div>
        </TabView>
      )

      expect(container.querySelector('.tab-view')).toBeInTheDocument()
    })

    it('handles no children', () => {
      const { container } = render(<TabView activeTab="portfolio" />)

      expect(container.querySelector('.tab-view')).toBeInTheDocument()
    })

    it('handles single child', () => {
      render(
        <TabView activeTab="portfolio">
          <div data-tab="portfolio">Only Content</div>
        </TabView>
      )

      expect(screen.getByText('Only Content')).toBeInTheDocument()
    })

    it('handles activeTab that does not match any tab', () => {
      const { container } = render(
        <TabView activeTab="nonexistent">
          <div data-tab="portfolio">Portfolio Content</div>
          <div data-tab="upload">Upload Content</div>
        </TabView>
      )

      expect(screen.queryByText('Portfolio Content')).not.toBeInTheDocument()
      expect(screen.queryByText('Upload Content')).not.toBeInTheDocument()
      expect(container.querySelector('.tab-view')).toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('has proper ARIA attributes for tab panel', () => {
      const { container } = render(
        <TabView activeTab="portfolio">
          <div data-tab="portfolio">Portfolio Content</div>
        </TabView>
      )

      const tabPanel = container.querySelector('.tab-panel')
      expect(tabPanel).toHaveAttribute('role', 'tabpanel')
    })
  })
})
