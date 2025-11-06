// ABOUTME: Test suite for SettingsCategoryPanel component
// ABOUTME: Tests settings display, loading states, error handling, and user interactions

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import axios from 'axios'
import { SettingsCategoryPanel } from './SettingsCategoryPanel'

vi.mock('axios')
const mockedAxios = axios as any

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
})
