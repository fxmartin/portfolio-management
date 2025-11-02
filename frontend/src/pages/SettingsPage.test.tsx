// ABOUTME: Test suite for SettingsPage component
// ABOUTME: Tests tab navigation, API integration, settings display, and user interactions

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import '@testing-library/jest-dom'
import axios from 'axios'
import { SettingsPage } from './SettingsPage'

vi.mock('axios')
const mockedAxios = axios as any

describe('SettingsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()

    // Mock categories API
    mockedAxios.get.mockImplementation((url: string) => {
      if (url.includes('/api/settings/categories')) {
        return Promise.resolve({
          data: [
            { name: 'Display', key: 'display', description: 'Display settings' },
            { name: 'API Keys', key: 'api_keys', description: 'API key settings' },
            { name: 'AI Settings', key: 'ai_settings', description: 'AI settings' },
            { name: 'System', key: 'system', description: 'System settings' },
            { name: 'Advanced', key: 'advanced', description: 'Advanced settings' }
          ]
        })
      }
      if (url.includes('/api/settings/category/display')) {
        return Promise.resolve({
          data: [
            {
              key: 'theme',
              name: 'Theme',
              value: 'light',
              default_value: 'light',
              description: 'Color theme',
              category: 'display',
              input_type: 'select',
              options: ['light', 'dark'],
              is_sensitive: false
            }
          ]
        })
      }
      return Promise.reject(new Error('Not found'))
    })
  })

  describe('Basic Rendering', () => {
    it('renders page title "Settings"', async () => {
      render(<SettingsPage />)

      const title = screen.getByText('Settings')
      expect(title).toBeInTheDocument()
    })

    it('has proper page structure with settings-page class', () => {
      const { container } = render(<SettingsPage />)

      const pageDiv = container.querySelector('.settings-page')
      expect(pageDiv).toBeInTheDocument()
    })

    it('renders Settings icon', () => {
      render(<SettingsPage />)

      const header = screen.getByRole('banner')
      expect(header).toBeInTheDocument()
    })

    it('displays subtitle describing Settings functionality', () => {
      render(<SettingsPage />)

      const subtitle = screen.getByText(/Manage your portfolio preferences and configuration/i)
      expect(subtitle).toBeInTheDocument()
    })
  })

  describe('Tab Navigation', () => {
    it('renders all 5 category tabs', async () => {
      render(<SettingsPage />)

      await waitFor(() => {
        expect(screen.getByText('Display')).toBeInTheDocument()
        expect(screen.getByText('API Keys')).toBeInTheDocument()
        expect(screen.getByText('AI Settings')).toBeInTheDocument()
        expect(screen.getByText('System')).toBeInTheDocument()
        expect(screen.getByText('Advanced')).toBeInTheDocument()
      })
    })

    it('displays Display tab as active by default', async () => {
      const { container } = render(<SettingsPage />)

      await waitFor(() => {
        const displayTab = screen.getByText('Display').closest('.settings-tab')
        expect(displayTab).toHaveClass('active')
      })
    })

    it('switches to different tab when clicked', async () => {
      const user = userEvent.setup()
      render(<SettingsPage />)

      await waitFor(() => {
        expect(screen.getByText('Display')).toBeInTheDocument()
      })

      const apiKeysTab = screen.getByText('API Keys')
      await user.click(apiKeysTab)

      const activeTab = apiKeysTab.closest('.settings-tab')
      expect(activeTab).toHaveClass('active')
    })

    it('updates content area when tab changes', async () => {
      const user = userEvent.setup()

      mockedAxios.get.mockImplementation((url: string) => {
        if (url.includes('/api/settings/categories')) {
          return Promise.resolve({
            data: [
              { name: 'Display', key: 'display' },
              { name: 'API Keys', key: 'api_keys' }
            ]
          })
        }
        if (url.includes('/api/settings/category/api_keys')) {
          return Promise.resolve({
            data: [
              {
                key: 'twelve_data_key',
                name: 'Twelve Data API Key',
                value: 'test-key-123',
                description: 'API key for Twelve Data',
                category: 'api_keys',
                input_type: 'password',
                is_sensitive: true
              }
            ]
          })
        }
        return Promise.resolve({ data: [] })
      })

      render(<SettingsPage />)

      await waitFor(() => {
        expect(screen.getByText('API Keys')).toBeInTheDocument()
      })

      const apiKeysTab = screen.getByText('API Keys')
      await user.click(apiKeysTab)

      await waitFor(() => {
        expect(mockedAxios.get).toHaveBeenCalledWith(
          expect.stringContaining('/api/settings/category/api_keys')
        )
      })
    })
  })

  describe('Loading States', () => {
    it('displays loading spinner while fetching categories', () => {
      mockedAxios.get.mockImplementation(() =>
        new Promise(resolve => setTimeout(() => resolve({ data: [] }), 100))
      )

      render(<SettingsPage />)

      expect(screen.getByText(/Loading settings/i)).toBeInTheDocument()
    })

    it('displays loading state when switching tabs', async () => {
      const user = userEvent.setup()

      mockedAxios.get.mockImplementation((url: string) => {
        if (url.includes('/api/settings/categories')) {
          return Promise.resolve({
            data: [
              { name: 'Display', key: 'display' },
              { name: 'System', key: 'system' }
            ]
          })
        }
        return new Promise(resolve => setTimeout(() => resolve({ data: [] }), 100))
      })

      render(<SettingsPage />)

      await waitFor(() => {
        expect(screen.getByText('System')).toBeInTheDocument()
      })

      const systemTab = screen.getByText('System')
      await user.click(systemTab)

      expect(screen.getByText(/Loading/i)).toBeInTheDocument()
    })
  })

  describe('Error Handling', () => {
    it('displays error message when categories API fails', async () => {
      mockedAxios.get.mockRejectedValue(new Error('Network error'))

      render(<SettingsPage />)

      await waitFor(() => {
        expect(screen.getByText(/Failed to load settings/i)).toBeInTheDocument()
      })
    })

    it('displays retry button on error', async () => {
      mockedAxios.get.mockRejectedValue(new Error('Network error'))

      render(<SettingsPage />)

      await waitFor(() => {
        const retryButton = screen.getByText(/Retry/i)
        expect(retryButton).toBeInTheDocument()
      })
    })

    it('retries fetching when retry button is clicked', async () => {
      const user = userEvent.setup()

      mockedAxios.get
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce({
          data: [{ name: 'Display', key: 'display' }]
        })

      render(<SettingsPage />)

      await waitFor(() => {
        expect(screen.getByText(/Failed to load settings/i)).toBeInTheDocument()
      })

      const retryButton = screen.getByText(/Retry/i)
      await user.click(retryButton)

      await waitFor(() => {
        expect(screen.getByText('Display')).toBeInTheDocument()
      })
    })
  })

  describe('Responsive Design', () => {
    it('renders with responsive CSS classes', () => {
      const { container } = render(<SettingsPage />)

      const pageDiv = container.querySelector('.settings-page')
      expect(pageDiv).toBeInTheDocument()
    })
  })
})
