// ABOUTME: Unit tests for ApiKeyInput component with test key functionality
// ABOUTME: Tests input handling, API key testing, validation, and timestamp display

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import axios from 'axios'
import { toast } from 'react-toastify'
import { ApiKeyInput } from './ApiKeyInput'
import type { Setting } from './SettingsCategoryPanel'

// Mock dependencies
vi.mock('axios')
vi.mock('react-toastify', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn()
  }
}))

// Mock useSettingValidation hook
vi.mock('../hooks/useSettingValidation', () => ({
  useSettingValidation: vi.fn(() => ({
    isValid: true,
    error: null,
    validating: false
  }))
}))

describe('ApiKeyInput', () => {
  const mockOnUpdate = vi.fn()
  const mockOnReset = vi.fn()

  const mockApiKeySetting: Setting = {
    key: 'anthropic_api_key',
    name: 'Anthropic API Key',
    value: '********',
    default_value: null,
    description: 'API key for Claude analysis',
    category: 'api_keys',
    input_type: 'password',
    is_sensitive: true,
    last_modified_at: '2025-11-05T10:30:00Z'
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('Rendering', () => {
    it('should render API key input field', () => {
      render(
        <ApiKeyInput
          setting={mockApiKeySetting}
          onUpdate={mockOnUpdate}
          onReset={mockOnReset}
        />
      )

      expect(screen.getByLabelText(/Anthropic API Key/i)).toBeInTheDocument()
      expect(screen.getByPlaceholderText('sk-ant-...')).toBeInTheDocument()
    })

    it('should render setting description', () => {
      render(
        <ApiKeyInput
          setting={mockApiKeySetting}
          onUpdate={mockOnUpdate}
          onReset={mockOnReset}
        />
      )

      expect(screen.getByText('API key for Claude analysis')).toBeInTheDocument()
    })

    it('should render last updated timestamp', () => {
      render(
        <ApiKeyInput
          setting={mockApiKeySetting}
          onUpdate={mockOnUpdate}
          onReset={mockOnReset}
        />
      )

      expect(screen.getByText(/Last updated:/i)).toBeInTheDocument()
    })

    it('should render Test Key button', () => {
      render(
        <ApiKeyInput
          setting={mockApiKeySetting}
          onUpdate={mockOnUpdate}
          onReset={mockOnReset}
        />
      )

      expect(screen.getByRole('button', { name: /Test Key/i })).toBeInTheDocument()
    })

    it('should render Save button', () => {
      render(
        <ApiKeyInput
          setting={mockApiKeySetting}
          onUpdate={mockOnUpdate}
          onReset={mockOnReset}
        />
      )

      expect(screen.getByRole('button', { name: /Save/i })).toBeInTheDocument()
    })
  })

  describe('Password Toggle', () => {
    it('should toggle password visibility', async () => {
      const user = userEvent.setup()
      render(
        <ApiKeyInput
          setting={mockApiKeySetting}
          onUpdate={mockOnUpdate}
          onReset={mockOnReset}
        />
      )

      const input = screen.getByPlaceholderText('sk-ant-...')
      const toggleButton = screen.getByRole('button', {
        name: /Show API key/i
      })

      // Initially password type
      expect(input).toHaveAttribute('type', 'password')

      // Click to show
      await user.click(toggleButton)
      expect(input).toHaveAttribute('type', 'text')

      // Click to hide
      await user.click(toggleButton)
      expect(input).toHaveAttribute('type', 'password')
    })
  })

  describe('API Key Testing', () => {
    it('should test API key successfully', async () => {
      const user = userEvent.setup()
      const mockAxios = vi.mocked(axios)
      mockAxios.post.mockResolvedValueOnce({
        data: { valid: true, validated_value: 'sk-ant-test123' }
      })

      render(
        <ApiKeyInput
          setting={mockApiKeySetting}
          onUpdate={mockOnUpdate}
          onReset={mockOnReset}
        />
      )

      const input = screen.getByPlaceholderText('sk-ant-...')
      const testButton = screen.getByRole('button', { name: /Test Key/i })

      // Enter API key
      await user.type(input, 'sk-ant-test123')

      // Click Test Key
      await user.click(testButton)

      // Wait for API call
      await waitFor(() => {
        expect(mockAxios.post).toHaveBeenCalledWith(
          expect.stringContaining('/api/settings/anthropic_api_key/test'),
          { value: 'sk-ant-test123' }
        )
      })

      // Should show success message
      await waitFor(() => {
        expect(
          screen.getByText(/API key is valid and working/i)
        ).toBeInTheDocument()
      })

      // Should show success toast
      expect(toast.success).toHaveBeenCalledWith('API key is valid!')
    })

    it('should handle failed API key test', async () => {
      const user = userEvent.setup()
      const mockAxios = vi.mocked(axios)
      mockAxios.post.mockResolvedValueOnce({
        data: {
          valid: false,
          error: 'Invalid API key - authentication failed'
        }
      })

      render(
        <ApiKeyInput
          setting={mockApiKeySetting}
          onUpdate={mockOnUpdate}
          onReset={mockOnReset}
        />
      )

      const input = screen.getByPlaceholderText('sk-ant-...')
      const testButton = screen.getByRole('button', { name: /Test Key/i })

      // Enter invalid API key
      await user.type(input, 'invalid-key')

      // Click Test Key
      await user.click(testButton)

      // Wait for error message
      await waitFor(() => {
        expect(
          screen.getByText(/Invalid API key - authentication failed/i)
        ).toBeInTheDocument()
      })
    })

    it('should disable Test Key button when input is empty', () => {
      render(
        <ApiKeyInput
          setting={mockApiKeySetting}
          onUpdate={mockOnUpdate}
          onReset={mockOnReset}
        />
      )

      const testButton = screen.getByRole('button', { name: /Test Key/i })
      expect(testButton).toBeDisabled()
    })

    it('should show loading state while testing', async () => {
      const user = userEvent.setup()
      const mockAxios = vi.mocked(axios)

      // Create a promise that we can control
      let resolveTest: (value: any) => void
      const testPromise = new Promise((resolve) => {
        resolveTest = resolve
      })
      mockAxios.post.mockReturnValueOnce(testPromise as any)

      render(
        <ApiKeyInput
          setting={mockApiKeySetting}
          onUpdate={mockOnUpdate}
          onReset={mockOnReset}
        />
      )

      const input = screen.getByPlaceholderText('sk-ant-...')
      const testButton = screen.getByRole('button', { name: /Test Key/i })

      await user.type(input, 'sk-ant-test123')
      await user.click(testButton)

      // Should show loading state
      expect(screen.getByText(/Testing.../i)).toBeInTheDocument()
      expect(testButton).toBeDisabled()

      // Resolve the test
      resolveTest!({ data: { valid: true } })

      // Loading state should disappear
      await waitFor(() => {
        expect(screen.queryByText(/Testing.../i)).not.toBeInTheDocument()
      })
    })

    it('should handle network error during test', async () => {
      const user = userEvent.setup()
      const mockAxios = vi.mocked(axios)
      mockAxios.post.mockRejectedValueOnce(new Error('Network error'))

      render(
        <ApiKeyInput
          setting={mockApiKeySetting}
          onUpdate={mockOnUpdate}
          onReset={mockOnReset}
        />
      )

      const input = screen.getByPlaceholderText('sk-ant-...')
      const testButton = screen.getByRole('button', { name: /Test Key/i })

      await user.type(input, 'sk-ant-test123')
      await user.click(testButton)

      await waitFor(() => {
        expect(
          screen.getByText(/Failed to test API key/i)
        ).toBeInTheDocument()
      })
    })
  })

  describe('Save Functionality', () => {
    it('should save API key when Save button is clicked', async () => {
      const user = userEvent.setup()
      mockOnUpdate.mockResolvedValueOnce(undefined)

      render(
        <ApiKeyInput
          setting={mockApiKeySetting}
          onUpdate={mockOnUpdate}
          onReset={mockOnReset}
        />
      )

      const input = screen.getByPlaceholderText('sk-ant-...')
      const saveButton = screen.getByRole('button', { name: /Save/i })

      // Enter new value
      await user.type(input, 'sk-ant-new-key')

      // Save button should be enabled
      expect(saveButton).not.toBeDisabled()

      // Click Save
      await user.click(saveButton)

      // Should call onUpdate
      await waitFor(() => {
        expect(mockOnUpdate).toHaveBeenCalledWith(
          'anthropic_api_key',
          'sk-ant-new-key'
        )
      })

      // Should show success toast
      expect(toast.success).toHaveBeenCalledWith(
        expect.stringContaining('saved successfully')
      )
    })

    it('should disable Save button when value has not changed', () => {
      const settingWithValue = {
        ...mockApiKeySetting,
        value: 'existing-key'
      }

      render(
        <ApiKeyInput
          setting={settingWithValue}
          onUpdate={mockOnUpdate}
          onReset={mockOnReset}
        />
      )

      const saveButton = screen.getByRole('button', { name: /Save/i })
      expect(saveButton).toBeDisabled()
    })

    it('should handle save error and revert value', async () => {
      const user = userEvent.setup()
      mockOnUpdate.mockRejectedValueOnce(new Error('Save failed'))

      render(
        <ApiKeyInput
          setting={mockApiKeySetting}
          onUpdate={mockOnUpdate}
          onReset={mockOnReset}
        />
      )

      const input = screen.getByPlaceholderText('sk-ant-...')
      await user.type(input, 'sk-ant-new-key')

      const saveButton = screen.getByRole('button', { name: /Save/i })
      await user.click(saveButton)

      // Should show error toast
      await waitFor(() => {
        expect(toast.error).toHaveBeenCalled()
      })

      // Should revert to original value
      expect(input).toHaveValue('')
    })
  })

  describe('Reset Functionality', () => {
    it('should show Reset button when value differs from default', () => {
      const modifiedSetting = {
        ...mockApiKeySetting,
        value: 'current-value',
        default_value: null
      }

      render(
        <ApiKeyInput
          setting={modifiedSetting}
          onUpdate={mockOnUpdate}
          onReset={mockOnReset}
        />
      )

      expect(
        screen.getByRole('button', { name: /Reset/i })
      ).toBeInTheDocument()
    })

    it('should not show Reset button for masked values', () => {
      render(
        <ApiKeyInput
          setting={mockApiKeySetting}
          onUpdate={mockOnUpdate}
          onReset={mockOnReset}
        />
      )

      expect(
        screen.queryByRole('button', { name: /Reset/i })
      ).not.toBeInTheDocument()
    })

    it('should call onReset when Reset button is clicked', async () => {
      const user = userEvent.setup()
      mockOnReset.mockResolvedValueOnce(undefined)

      const modifiedSetting = {
        ...mockApiKeySetting,
        value: 'current-value'
      }

      render(
        <ApiKeyInput
          setting={modifiedSetting}
          onUpdate={mockOnUpdate}
          onReset={mockOnReset}
        />
      )

      const resetButton = screen.getByRole('button', { name: /Reset/i })
      await user.click(resetButton)

      await waitFor(() => {
        expect(mockOnReset).toHaveBeenCalledWith('anthropic_api_key')
      })
    })
  })

  describe('Timestamp Formatting', () => {
    it('should format recent timestamp as "just now"', () => {
      const recentSetting = {
        ...mockApiKeySetting,
        last_modified_at: new Date().toISOString()
      }

      render(
        <ApiKeyInput
          setting={recentSetting}
          onUpdate={mockOnUpdate}
          onReset={mockOnReset}
        />
      )

      expect(screen.getByText(/Last updated: just now/i)).toBeInTheDocument()
    })

    it('should format timestamp in minutes for recent changes', () => {
      const fiveMinutesAgo = new Date(Date.now() - 5 * 60 * 1000)
      const recentSetting = {
        ...mockApiKeySetting,
        last_modified_at: fiveMinutesAgo.toISOString()
      }

      render(
        <ApiKeyInput
          setting={recentSetting}
          onUpdate={mockOnUpdate}
          onReset={mockOnReset}
        />
      )

      expect(screen.getByText(/Last updated: 5m ago/i)).toBeInTheDocument()
    })

    it('should format timestamp in hours for older changes', () => {
      const threeHoursAgo = new Date(Date.now() - 3 * 60 * 60 * 1000)
      const oldSetting = {
        ...mockApiKeySetting,
        last_modified_at: threeHoursAgo.toISOString()
      }

      render(
        <ApiKeyInput
          setting={oldSetting}
          onUpdate={mockOnUpdate}
          onReset={mockOnReset}
        />
      )

      expect(screen.getByText(/Last updated: 3h ago/i)).toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('should have proper ARIA labels for toggle button', () => {
      render(
        <ApiKeyInput
          setting={mockApiKeySetting}
          onUpdate={mockOnUpdate}
          onReset={mockOnReset}
        />
      )

      const toggleButton = screen.getByRole('button', {
        name: /Show API key/i
      })
      expect(toggleButton).toHaveAttribute('aria-label')
    })

    it('should be keyboard accessible', async () => {
      const user = userEvent.setup()
      render(
        <ApiKeyInput
          setting={mockApiKeySetting}
          onUpdate={mockOnUpdate}
          onReset={mockOnReset}
        />
      )

      const input = screen.getByPlaceholderText('sk-ant-...')

      // Tab to input
      await user.tab()
      expect(input).toHaveFocus()

      // Type value
      await user.keyboard('sk-ant-test')
      expect(input).toHaveValue('sk-ant-test')
    })
  })
})
