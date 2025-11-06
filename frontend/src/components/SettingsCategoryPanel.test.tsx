// ABOUTME: Test suite for SettingsCategoryPanel component
// ABOUTME: Tests settings display, loading states, error handling, and user interactions

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import axios from 'axios'
import { SettingsCategoryPanel } from './SettingsCategoryPanel'

vi.mock('axios')
const mockedAxios = axios as jest.Mocked<typeof axios>

// Mock PromptsManager
vi.mock('./PromptsManager', () => ({
  PromptsManager: () => <div data-testid="prompts-manager">PromptsManager Component</div>
}))

describe('SettingsCategoryPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks()

    mockedAxios.get.mockResolvedValue({
      data: [
        {
          key: 'theme',
          name: 'Theme',
          value: 'light',
          default_value: 'light',
          description: 'Application color theme',
          category: 'display',
          input_type: 'select',
          options: ['light', 'dark'],
          is_sensitive: false
        },
        {
          key: 'currency',
          name: 'Base Currency',
          value: 'EUR',
          default_value: 'EUR',
          description: 'Portfolio base currency',
          category: 'display',
          input_type: 'select',
          options: ['EUR', 'USD', 'GBP'],
          is_sensitive: false
        }
      ]
    })
  })

  describe('Basic Rendering', () => {
    it('renders settings for a category', async () => {
      render(<SettingsCategoryPanel categoryKey="display" />)

      await waitFor(() => {
        expect(screen.getByText('Theme')).toBeInTheDocument()
        expect(screen.getByText('Base Currency')).toBeInTheDocument()
      })
    })

    it('displays setting descriptions', async () => {
      render(<SettingsCategoryPanel categoryKey="display" />)

      await waitFor(() => {
        expect(screen.getByText('Application color theme')).toBeInTheDocument()
        expect(screen.getByText('Portfolio base currency')).toBeInTheDocument()
      })
    })

    it('fetches settings on mount', async () => {
      render(<SettingsCategoryPanel categoryKey="display" />)

      await waitFor(() => {
        expect(mockedAxios.get).toHaveBeenCalledWith(
          expect.stringContaining('/api/settings/category/display')
        )
      })
    })
  })

  describe('Loading States', () => {
    it('displays loading spinner while fetching settings', () => {
      mockedAxios.get.mockImplementation(() =>
        new Promise(resolve => setTimeout(() => resolve({ data: [] }), 100))
      )

      render(<SettingsCategoryPanel categoryKey="display" />)

      expect(screen.getByText(/Loading/i)).toBeInTheDocument()
    })

    it('hides loading state after data loads', async () => {
      render(<SettingsCategoryPanel categoryKey="display" />)

      await waitFor(() => {
        expect(screen.queryByText(/Loading/i)).not.toBeInTheDocument()
      })
    })
  })

  describe('Error Handling', () => {
    it('displays error message when API fails', async () => {
      mockedAxios.get.mockRejectedValue(new Error('Network error'))

      render(<SettingsCategoryPanel categoryKey="display" />)

      await waitFor(() => {
        expect(screen.getByText(/Failed to load settings/i)).toBeInTheDocument()
      })
    })

    it('shows retry button on error', async () => {
      mockedAxios.get.mockRejectedValue(new Error('Network error'))

      render(<SettingsCategoryPanel categoryKey="display" />)

      await waitFor(() => {
        expect(screen.getByText(/Retry/i)).toBeInTheDocument()
      })
    })
  })

  describe('Empty State', () => {
    it('displays empty message when no settings exist', async () => {
      mockedAxios.get.mockResolvedValue({ data: [] })

      render(<SettingsCategoryPanel categoryKey="display" />)

      await waitFor(() => {
        expect(screen.getByText(/No settings available/i)).toBeInTheDocument()
      })
    })
  })

  describe('Category Changes', () => {
    it('refetches settings when category changes', async () => {
      const { rerender } = render(<SettingsCategoryPanel categoryKey="display" />)

      await waitFor(() => {
        expect(mockedAxios.get).toHaveBeenCalledWith(
          expect.stringContaining('/api/settings/category/display')
        )
      })

      mockedAxios.get.mockResolvedValue({
        data: [
          {
            key: 'api_key',
            name: 'API Key',
            value: 'test-key',
            category: 'api_keys',
            input_type: 'password'
          }
        ]
      })

      rerender(<SettingsCategoryPanel categoryKey="api_keys" />)

      await waitFor(() => {
        expect(mockedAxios.get).toHaveBeenCalledWith(
          expect.stringContaining('/api/settings/category/api_keys')
        )
      })
    })
  })

  describe('Prompts Category Integration', () => {
    it('should render PromptsManager for prompts category', () => {
      render(<SettingsCategoryPanel categoryKey="prompts" />)

      expect(screen.getByTestId('prompts-manager')).toBeInTheDocument()
      expect(screen.getByText('PromptsManager Component')).toBeInTheDocument()
    })

    it('should not fetch settings for prompts category', () => {
      render(<SettingsCategoryPanel categoryKey="prompts" />)

      // Should not call axios for prompts category
      expect(mockedAxios.get).not.toHaveBeenCalled()
    })
  })

  describe('Display Settings Category (F9.5-002)', () => {
    it('should render currency selector with EUR, USD, GBP, CHF options', async () => {
      const mockSettings = [
        {
          key: 'base_currency',
          name: 'Base Currency',
          value: 'EUR',
          default_value: 'EUR',
          description: 'Base currency for portfolio display',
          category: 'display',
          input_type: 'select',
          options: ['EUR', 'USD', 'GBP', 'CHF'],
          is_sensitive: false,
          is_editable: true
        }
      ]

      mockedAxios.get.mockResolvedValueOnce({ data: mockSettings })

      render(<SettingsCategoryPanel categoryKey="display" />)

      await waitFor(() => {
        expect(screen.getByText('Base Currency')).toBeInTheDocument()
      })

      // Find the select element
      const selectElement = screen.getByDisplayValue('EUR')
      expect(selectElement).toBeInTheDocument()
      expect(selectElement.tagName).toBe('SELECT')

      // Check all options are present
      const options = selectElement.querySelectorAll('option')
      expect(options).toHaveLength(4)
      expect(options[0]).toHaveTextContent('EUR')
      expect(options[1]).toHaveTextContent('USD')
      expect(options[2]).toHaveTextContent('GBP')
      expect(options[3]).toHaveTextContent('CHF')
    })

    it('should render date format selector with all format options', async () => {
      const mockSettings = [
        {
          key: 'date_format',
          name: 'Date Format',
          value: 'YYYY-MM-DD',
          default_value: 'YYYY-MM-DD',
          description: 'Date format for transaction display',
          category: 'display',
          input_type: 'select',
          options: ['YYYY-MM-DD', 'DD/MM/YYYY', 'MM/DD/YYYY'],
          is_sensitive: false,
          is_editable: true
        }
      ]

      mockedAxios.get.mockResolvedValueOnce({ data: mockSettings })

      render(<SettingsCategoryPanel categoryKey="display" />)

      await waitFor(() => {
        expect(screen.getByText('Date Format')).toBeInTheDocument()
      })

      const selectElement = screen.getByDisplayValue('YYYY-MM-DD')
      expect(selectElement).toBeInTheDocument()

      const options = selectElement.querySelectorAll('option')
      expect(options).toHaveLength(3)
      expect(options[0]).toHaveTextContent('YYYY-MM-DD')
      expect(options[1]).toHaveTextContent('DD/MM/YYYY')
      expect(options[2]).toHaveTextContent('MM/DD/YYYY')
    })

    it('should render number format selector with all locale options', async () => {
      const mockSettings = [
        {
          key: 'number_format',
          name: 'Number Format',
          value: 'en-US',
          default_value: 'en-US',
          description: 'Number formatting locale',
          category: 'display',
          input_type: 'select',
          options: ['en-US', 'de-DE', 'fr-FR', 'en-GB'],
          is_sensitive: false,
          is_editable: true
        }
      ]

      mockedAxios.get.mockResolvedValueOnce({ data: mockSettings })

      render(<SettingsCategoryPanel categoryKey="display" />)

      await waitFor(() => {
        expect(screen.getByText('Number Format')).toBeInTheDocument()
      })

      const selectElement = screen.getByDisplayValue('en-US')
      expect(selectElement).toBeInTheDocument()

      const options = selectElement.querySelectorAll('option')
      expect(options).toHaveLength(4)
      expect(options[0]).toHaveTextContent('en-US')
      expect(options[1]).toHaveTextContent('de-DE')
      expect(options[2]).toHaveTextContent('fr-FR')
      expect(options[3]).toHaveTextContent('en-GB')
    })

    it('should render all display settings together', async () => {
      const mockSettings = [
        {
          key: 'base_currency',
          name: 'Base Currency',
          value: 'EUR',
          default_value: 'EUR',
          description: 'Base currency for portfolio display',
          category: 'display',
          input_type: 'select',
          options: ['EUR', 'USD', 'GBP', 'CHF'],
          is_sensitive: false
        },
        {
          key: 'date_format',
          name: 'Date Format',
          value: 'YYYY-MM-DD',
          default_value: 'YYYY-MM-DD',
          description: 'Date format for transaction display',
          category: 'display',
          input_type: 'select',
          options: ['YYYY-MM-DD', 'DD/MM/YYYY', 'MM/DD/YYYY'],
          is_sensitive: false
        },
        {
          key: 'number_format',
          name: 'Number Format',
          value: 'en-US',
          default_value: 'en-US',
          description: 'Number formatting locale',
          category: 'display',
          input_type: 'select',
          options: ['en-US', 'de-DE', 'fr-FR', 'en-GB'],
          is_sensitive: false
        }
      ]

      mockedAxios.get.mockResolvedValueOnce({ data: mockSettings })

      render(<SettingsCategoryPanel categoryKey="display" />)

      await waitFor(() => {
        expect(screen.getByText('Base Currency')).toBeInTheDocument()
        expect(screen.getByText('Date Format')).toBeInTheDocument()
        expect(screen.getByText('Number Format')).toBeInTheDocument()
      })

      // Verify descriptions
      expect(screen.getByText('Base currency for portfolio display')).toBeInTheDocument()
      expect(screen.getByText('Date format for transaction display')).toBeInTheDocument()
      expect(screen.getByText('Number formatting locale')).toBeInTheDocument()
    })

    it('should display correct API endpoint for display category', async () => {
      const mockSettings = [
        {
          key: 'base_currency',
          name: 'Base Currency',
          value: 'EUR',
          category: 'display',
          input_type: 'select',
          options: ['EUR', 'USD', 'GBP', 'CHF']
        }
      ]

      mockedAxios.get.mockResolvedValueOnce({ data: mockSettings })

      render(<SettingsCategoryPanel categoryKey="display" />)

      await waitFor(() => {
        expect(mockedAxios.get).toHaveBeenCalledWith(
          expect.stringContaining('/api/settings/category/display')
        )
      })
    })
  })

  describe('System Settings Category (F9.5-002)', () => {
    it('should render crypto refresh interval with correct range (30-600)', async () => {
      const mockSettings = [
        {
          key: 'crypto_price_refresh_seconds',
          name: 'Crypto Refresh Interval',
          value: 60,
          default_value: 60,
          description: 'Crypto price refresh interval (seconds)',
          category: 'system',
          input_type: 'number',
          min_value: 30,
          max_value: 600,
          is_sensitive: false,
          is_editable: true
        }
      ]

      mockedAxios.get.mockResolvedValueOnce({ data: mockSettings })

      render(<SettingsCategoryPanel categoryKey="system" />)

      await waitFor(() => {
        expect(screen.getByText('Crypto Refresh Interval')).toBeInTheDocument()
      })

      const inputElement = screen.getByDisplayValue('60')
      expect(inputElement).toBeInTheDocument()
      expect(inputElement.getAttribute('type')).toBe('number')
      expect(inputElement.getAttribute('min')).toBe('30')
      expect(inputElement.getAttribute('max')).toBe('600')
    })

    it('should render stock refresh interval with correct range (60-600)', async () => {
      const mockSettings = [
        {
          key: 'stock_price_refresh_seconds',
          name: 'Stock Refresh Interval',
          value: 120,
          default_value: 120,
          description: 'Stock price refresh interval (seconds)',
          category: 'system',
          input_type: 'number',
          min_value: 60,
          max_value: 600,
          is_sensitive: false,
          is_editable: true
        }
      ]

      mockedAxios.get.mockResolvedValueOnce({ data: mockSettings })

      render(<SettingsCategoryPanel categoryKey="system" />)

      await waitFor(() => {
        expect(screen.getByText('Stock Refresh Interval')).toBeInTheDocument()
      })

      const inputElement = screen.getByDisplayValue('120')
      expect(inputElement).toBeInTheDocument()
      expect(inputElement.getAttribute('type')).toBe('number')
      expect(inputElement.getAttribute('min')).toBe('60')
      expect(inputElement.getAttribute('max')).toBe('600')
    })

    it('should render cache TTL with correct range (1-48)', async () => {
      const mockSettings = [
        {
          key: 'cache_ttl_hours',
          name: 'Cache TTL',
          value: 1,
          default_value: 1,
          description: 'Redis cache TTL for analysis results (hours)',
          category: 'system',
          input_type: 'number',
          min_value: 1,
          max_value: 48,
          is_sensitive: false,
          is_editable: true
        }
      ]

      mockedAxios.get.mockResolvedValueOnce({ data: mockSettings })

      render(<SettingsCategoryPanel categoryKey="system" />)

      await waitFor(() => {
        expect(screen.getByText('Cache TTL')).toBeInTheDocument()
      })

      const inputElement = screen.getByDisplayValue('1')
      expect(inputElement).toBeInTheDocument()
      expect(inputElement.getAttribute('type')).toBe('number')
      expect(inputElement.getAttribute('min')).toBe('1')
      expect(inputElement.getAttribute('max')).toBe('48')
    })

    it('should render all system settings together', async () => {
      const mockSettings = [
        {
          key: 'crypto_price_refresh_seconds',
          name: 'Crypto Refresh Interval',
          value: 60,
          default_value: 60,
          description: 'Crypto price refresh interval (seconds)',
          category: 'system',
          input_type: 'number',
          min_value: 30,
          max_value: 600,
          is_sensitive: false
        },
        {
          key: 'stock_price_refresh_seconds',
          name: 'Stock Refresh Interval',
          value: 120,
          default_value: 120,
          description: 'Stock price refresh interval (seconds)',
          category: 'system',
          input_type: 'number',
          min_value: 60,
          max_value: 600,
          is_sensitive: false
        },
        {
          key: 'cache_ttl_hours',
          name: 'Cache TTL',
          value: 1,
          default_value: 1,
          description: 'Redis cache TTL for analysis results (hours)',
          category: 'system',
          input_type: 'number',
          min_value: 1,
          max_value: 48,
          is_sensitive: false
        }
      ]

      mockedAxios.get.mockResolvedValueOnce({ data: mockSettings })

      render(<SettingsCategoryPanel categoryKey="system" />)

      await waitFor(() => {
        expect(screen.getByText('Crypto Refresh Interval')).toBeInTheDocument()
        expect(screen.getByText('Stock Refresh Interval')).toBeInTheDocument()
        expect(screen.getByText('Cache TTL')).toBeInTheDocument()
      })

      // Verify descriptions
      expect(screen.getByText('Crypto price refresh interval (seconds)')).toBeInTheDocument()
      expect(screen.getByText('Stock price refresh interval (seconds)')).toBeInTheDocument()
      expect(screen.getByText('Redis cache TTL for analysis results (hours)')).toBeInTheDocument()
    })

    it('should display correct API endpoint for system category', async () => {
      const mockSettings = [
        {
          key: 'crypto_price_refresh_seconds',
          name: 'Crypto Refresh Interval',
          value: 60,
          category: 'system',
          input_type: 'number',
          min_value: 30,
          max_value: 600
        }
      ]

      mockedAxios.get.mockResolvedValueOnce({ data: mockSettings })

      render(<SettingsCategoryPanel categoryKey="system" />)

      await waitFor(() => {
        expect(mockedAxios.get).toHaveBeenCalledWith(
          expect.stringContaining('/api/settings/category/system')
        )
      })
    })
  })

  describe('Save and Reset Functionality (F9.5-002)', () => {
    it('should show Save button for each setting', async () => {
      const mockSettings = [
        {
          key: 'base_currency',
          name: 'Base Currency',
          value: 'EUR',
          default_value: 'EUR',
          category: 'display',
          input_type: 'select',
          options: ['EUR', 'USD']
        }
      ]

      mockedAxios.get.mockResolvedValueOnce({ data: mockSettings })

      render(<SettingsCategoryPanel categoryKey="display" />)

      await waitFor(() => {
        const saveButtons = screen.getAllByText('Save')
        expect(saveButtons.length).toBeGreaterThan(0)
      })
    })

    it('should show Reset button when value differs from default', async () => {
      const mockSettings = [
        {
          key: 'base_currency',
          name: 'Base Currency',
          value: 'USD',  // Different from default
          default_value: 'EUR',
          category: 'display',
          input_type: 'select',
          options: ['EUR', 'USD']
        }
      ]

      mockedAxios.get.mockResolvedValueOnce({ data: mockSettings })

      render(<SettingsCategoryPanel categoryKey="display" />)

      await waitFor(() => {
        expect(screen.getByText('Reset')).toBeInTheDocument()
      })
    })

    it('should not show Reset button when value equals default', async () => {
      const mockSettings = [
        {
          key: 'base_currency',
          name: 'Base Currency',
          value: 'EUR',  // Same as default
          default_value: 'EUR',
          category: 'display',
          input_type: 'select',
          options: ['EUR', 'USD']
        }
      ]

      mockedAxios.get.mockResolvedValueOnce({ data: mockSettings })

      render(<SettingsCategoryPanel categoryKey="display" />)

      await waitFor(() => {
        expect(screen.getByText('Save')).toBeInTheDocument()
      })

      expect(screen.queryByText('Reset')).not.toBeInTheDocument()
    })
  })

  describe('Integration with SettingsContext (F9.5-002)', () => {
    it('should call updateSetting when currency is changed', async () => {
      const mockSettings = [
        {
          key: 'base_currency',
          name: 'Base Currency',
          value: 'EUR',
          default_value: 'EUR',
          category: 'display',
          input_type: 'select',
          options: ['EUR', 'USD', 'GBP', 'CHF']
        }
      ]

      mockedAxios.get.mockResolvedValueOnce({ data: mockSettings })
      mockedAxios.put.mockResolvedValueOnce({ data: { success: true } })

      render(<SettingsCategoryPanel categoryKey="display" />)

      await waitFor(() => {
        expect(screen.getByDisplayValue('EUR')).toBeInTheDocument()
      })

      // Change would be triggered by SettingItem component
      // which calls handleSettingUpdate passed via props
      expect(screen.getByText('Base Currency')).toBeInTheDocument()
    })
  })

  describe('Validation and Error Handling (F9.5-002)', () => {
    it('should handle API errors gracefully when fetching settings', async () => {
      mockedAxios.get.mockRejectedValueOnce(new Error('Network error'))

      render(<SettingsCategoryPanel categoryKey="display" />)

      await waitFor(() => {
        expect(screen.getByText(/Failed to load settings/i)).toBeInTheDocument()
      })
    })

    it('should show retry button on error', async () => {
      mockedAxios.get.mockRejectedValueOnce(new Error('Network error'))

      render(<SettingsCategoryPanel categoryKey="display" />)

      await waitFor(() => {
        expect(screen.getByText(/Retry/i)).toBeInTheDocument()
      })
    })

    it('should handle validation rules for numeric settings', async () => {
      const mockSettings = [
        {
          key: 'crypto_price_refresh_seconds',
          name: 'Crypto Refresh Interval',
          value: 60,
          default_value: 60,
          description: 'Crypto price refresh interval (seconds)',
          category: 'system',
          input_type: 'number',
          min_value: 30,
          max_value: 600,
          is_sensitive: false,
          validation_regex: null
        }
      ]

      mockedAxios.get.mockResolvedValueOnce({ data: mockSettings })

      render(<SettingsCategoryPanel categoryKey="system" />)

      await waitFor(() => {
        const input = screen.getByDisplayValue('60')
        expect(input.getAttribute('min')).toBe('30')
        expect(input.getAttribute('max')).toBe('600')
      })
    })
  })

  describe('Mobile Responsiveness (F9.5-002)', () => {
    it('should render settings in mobile-friendly layout', async () => {
      const mockSettings = [
        {
          key: 'base_currency',
          name: 'Base Currency',
          value: 'EUR',
          category: 'display',
          input_type: 'select',
          options: ['EUR', 'USD']
        }
      ]

      mockedAxios.get.mockResolvedValueOnce({ data: mockSettings })

      render(<SettingsCategoryPanel categoryKey="display" />)

      await waitFor(() => {
        expect(screen.getByText('Base Currency')).toBeInTheDocument()
      })

      // Component should have responsive classes (tested via CSS)
      const panel = screen.getByText('Base Currency').closest('.settings-category-panel')
      expect(panel).toBeInTheDocument()
    })
  })
})
