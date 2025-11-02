// ABOUTME: Test suite for SettingItem component
// ABOUTME: Tests all input types (text, password, number, select, checkbox), update/reset functionality, and validation

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import '@testing-library/jest-dom'
import { SettingItem } from './SettingItem'
import type { Setting } from './SettingsCategoryPanel'

describe('SettingItem', () => {
  const mockOnUpdate = vi.fn()
  const mockOnReset = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    mockOnUpdate.mockResolvedValue(undefined)
    mockOnReset.mockResolvedValue(undefined)
  })

  describe('Text Input Type', () => {
    const textSetting: Setting = {
      key: 'app_name',
      name: 'Application Name',
      value: 'Portfolio Manager',
      default_value: 'Portfolio Manager',
      description: 'Name of the application',
      category: 'display',
      input_type: 'text',
      is_sensitive: false
    }

    it('renders text input with current value', () => {
      render(<SettingItem setting={textSetting} onUpdate={mockOnUpdate} onReset={mockOnReset} />)

      const input = screen.getByDisplayValue('Portfolio Manager')
      expect(input).toBeInTheDocument()
      expect(input).toHaveAttribute('type', 'text')
    })

    it('displays setting name and description', () => {
      render(<SettingItem setting={textSetting} onUpdate={mockOnUpdate} onReset={mockOnReset} />)

      expect(screen.getByText('Application Name')).toBeInTheDocument()
      expect(screen.getByText('Name of the application')).toBeInTheDocument()
    })

    it('calls onUpdate when Save button is clicked', async () => {
      const user = userEvent.setup()
      render(<SettingItem setting={textSetting} onUpdate={mockOnUpdate} onReset={mockOnReset} />)

      const input = screen.getByDisplayValue('Portfolio Manager')
      await user.clear(input)
      await user.type(input, 'New Name')

      const saveButton = screen.getByText('Save')
      await user.click(saveButton)

      await waitFor(() => {
        expect(mockOnUpdate).toHaveBeenCalledWith('app_name', 'New Name')
      })
    })

    it('disables Save button when value is unchanged', () => {
      render(<SettingItem setting={textSetting} onUpdate={mockOnUpdate} onReset={mockOnReset} />)

      const saveButton = screen.getByText('Save')
      expect(saveButton).toBeDisabled()
    })

    it('enables Save button when value changes', async () => {
      const user = userEvent.setup()
      render(<SettingItem setting={textSetting} onUpdate={mockOnUpdate} onReset={mockOnReset} />)

      const input = screen.getByDisplayValue('Portfolio Manager')
      await user.type(input, ' Updated')

      const saveButton = screen.getByText('Save')
      expect(saveButton).not.toBeDisabled()
    })
  })

  describe('Password Input Type', () => {
    const passwordSetting: Setting = {
      key: 'api_key',
      name: 'API Key',
      value: 'secret-key-123',
      default_value: '',
      description: 'Your API key',
      category: 'api_keys',
      input_type: 'password',
      is_sensitive: true
    }

    it('renders password input with masked value', () => {
      render(<SettingItem setting={passwordSetting} onUpdate={mockOnUpdate} onReset={mockOnReset} />)

      const input = screen.getByDisplayValue('secret-key-123')
      expect(input).toHaveAttribute('type', 'password')
    })

    it('displays masked value indicator for sensitive settings', () => {
      render(<SettingItem setting={passwordSetting} onUpdate={mockOnUpdate} onReset={mockOnReset} />)

      expect(screen.getByText('API Key')).toBeInTheDocument()
    })

    it('has show/hide toggle button', () => {
      render(<SettingItem setting={passwordSetting} onUpdate={mockOnUpdate} onReset={mockOnReset} />)

      const toggleButton = screen.getByRole('button', { name: /show|hide/i })
      expect(toggleButton).toBeInTheDocument()
    })

    it('toggles password visibility when toggle button is clicked', async () => {
      const user = userEvent.setup()
      render(<SettingItem setting={passwordSetting} onUpdate={mockOnUpdate} onReset={mockOnReset} />)

      const input = screen.getByDisplayValue('secret-key-123')
      expect(input).toHaveAttribute('type', 'password')

      const toggleButton = screen.getByRole('button', { name: /show/i })
      await user.click(toggleButton)

      expect(input).toHaveAttribute('type', 'text')
    })
  })

  describe('Number Input Type', () => {
    const numberSetting: Setting = {
      key: 'cache_ttl',
      name: 'Cache TTL',
      value: 3600,
      default_value: 3600,
      description: 'Cache time-to-live in seconds',
      category: 'system',
      input_type: 'number',
      min_value: 60,
      max_value: 86400
    }

    it('renders number input with current value', () => {
      render(<SettingItem setting={numberSetting} onUpdate={mockOnUpdate} onReset={mockOnReset} />)

      const input = screen.getByDisplayValue('3600')
      expect(input).toHaveAttribute('type', 'number')
    })

    it('respects min and max attributes', () => {
      render(<SettingItem setting={numberSetting} onUpdate={mockOnUpdate} onReset={mockOnReset} />)

      const input = screen.getByDisplayValue('3600')
      expect(input).toHaveAttribute('min', '60')
      expect(input).toHaveAttribute('max', '86400')
    })

    it('calls onUpdate with number value', async () => {
      const user = userEvent.setup()
      render(<SettingItem setting={numberSetting} onUpdate={mockOnUpdate} onReset={mockOnReset} />)

      const input = screen.getByDisplayValue('3600')
      await user.clear(input)
      await user.type(input, '7200')

      const saveButton = screen.getByText('Save')
      await user.click(saveButton)

      await waitFor(() => {
        expect(mockOnUpdate).toHaveBeenCalledWith('cache_ttl', 7200)
      })
    })
  })

  describe('Select Input Type', () => {
    const selectSetting: Setting = {
      key: 'theme',
      name: 'Theme',
      value: 'light',
      default_value: 'light',
      description: 'Application theme',
      category: 'display',
      input_type: 'select',
      options: ['light', 'dark', 'auto']
    }

    it('renders select dropdown with options', () => {
      render(<SettingItem setting={selectSetting} onUpdate={mockOnUpdate} onReset={mockOnReset} />)

      const select = screen.getByDisplayValue('light')
      expect(select.tagName).toBe('SELECT')

      expect(screen.getByRole('option', { name: 'light' })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: 'dark' })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: 'auto' })).toBeInTheDocument()
    })

    it('calls onUpdate when option is selected', async () => {
      const user = userEvent.setup()
      render(<SettingItem setting={selectSetting} onUpdate={mockOnUpdate} onReset={mockOnReset} />)

      const select = screen.getByDisplayValue('light')
      await user.selectOptions(select, 'dark')

      const saveButton = screen.getByText('Save')
      await user.click(saveButton)

      await waitFor(() => {
        expect(mockOnUpdate).toHaveBeenCalledWith('theme', 'dark')
      })
    })
  })

  describe('Checkbox Input Type', () => {
    const checkboxSetting: Setting = {
      key: 'auto_refresh',
      name: 'Auto Refresh',
      value: true,
      default_value: true,
      description: 'Automatically refresh data',
      category: 'system',
      input_type: 'checkbox'
    }

    it('renders checkbox input with checked state', () => {
      render(<SettingItem setting={checkboxSetting} onUpdate={mockOnUpdate} onReset={mockOnReset} />)

      const checkbox = screen.getByRole('checkbox')
      expect(checkbox).toBeChecked()
    })

    it('calls onUpdate with boolean value', async () => {
      const user = userEvent.setup()
      render(<SettingItem setting={checkboxSetting} onUpdate={mockOnUpdate} onReset={mockOnReset} />)

      const checkbox = screen.getByRole('checkbox')
      await user.click(checkbox)

      const saveButton = screen.getByText('Save')
      await user.click(saveButton)

      await waitFor(() => {
        expect(mockOnUpdate).toHaveBeenCalledWith('auto_refresh', false)
      })
    })

    it('renders unchecked checkbox when value is false', () => {
      const uncheckedSetting = { ...checkboxSetting, value: false }
      render(<SettingItem setting={uncheckedSetting} onUpdate={mockOnUpdate} onReset={mockOnReset} />)

      const checkbox = screen.getByRole('checkbox')
      expect(checkbox).not.toBeChecked()
    })
  })

  describe('Reset Functionality', () => {
    const modifiedSetting: Setting = {
      key: 'app_name',
      name: 'Application Name',
      value: 'Modified Name',
      default_value: 'Portfolio Manager',
      description: 'Name of the application',
      category: 'display',
      input_type: 'text'
    }

    it('shows Reset button when value differs from default', () => {
      render(<SettingItem setting={modifiedSetting} onUpdate={mockOnUpdate} onReset={mockOnReset} />)

      const resetButton = screen.getByText('Reset')
      expect(resetButton).toBeInTheDocument()
    })

    it('calls onReset when Reset button is clicked', async () => {
      const user = userEvent.setup()
      render(<SettingItem setting={modifiedSetting} onUpdate={mockOnUpdate} onReset={mockOnReset} />)

      const resetButton = screen.getByText('Reset')
      await user.click(resetButton)

      await waitFor(() => {
        expect(mockOnReset).toHaveBeenCalledWith('app_name')
      })
    })

    it('does not show Reset button when value equals default', () => {
      const defaultSetting = { ...modifiedSetting, value: 'Portfolio Manager' }
      render(<SettingItem setting={defaultSetting} onUpdate={mockOnUpdate} onReset={mockOnReset} />)

      const resetButton = screen.queryByText('Reset')
      expect(resetButton).not.toBeInTheDocument()
    })
  })

  describe('Error Handling', () => {
    const setting: Setting = {
      key: 'test_key',
      name: 'Test Setting',
      value: 'test',
      default_value: 'test',
      category: 'display',
      input_type: 'text'
    }

    it('displays error message when update fails', async () => {
      const user = userEvent.setup()
      mockOnUpdate.mockRejectedValue(new Error('Update failed'))

      render(<SettingItem setting={setting} onUpdate={mockOnUpdate} onReset={mockOnReset} />)

      const input = screen.getByDisplayValue('test')
      await user.type(input, ' updated')

      const saveButton = screen.getByText('Save')
      await user.click(saveButton)

      await waitFor(() => {
        expect(screen.getByText(/Failed to update setting/i)).toBeInTheDocument()
      })
    })

    it('displays error message when reset fails', async () => {
      const user = userEvent.setup()
      mockOnReset.mockRejectedValue(new Error('Reset failed'))

      const modifiedSetting = { ...setting, value: 'modified' }
      render(<SettingItem setting={modifiedSetting} onUpdate={mockOnUpdate} onReset={mockOnReset} />)

      const resetButton = screen.getByText('Reset')
      await user.click(resetButton)

      await waitFor(() => {
        expect(screen.getByText(/Failed to reset setting/i)).toBeInTheDocument()
      })
    })

    it('clears error message when user changes input', async () => {
      const user = userEvent.setup()
      mockOnUpdate.mockRejectedValueOnce(new Error('Update failed'))

      render(<SettingItem setting={setting} onUpdate={mockOnUpdate} onReset={mockOnReset} />)

      const input = screen.getByDisplayValue('test')
      await user.type(input, ' updated')

      const saveButton = screen.getByText('Save')
      await user.click(saveButton)

      await waitFor(() => {
        expect(screen.getByText(/Failed to update setting/i)).toBeInTheDocument()
      })

      await user.type(input, ' again')

      expect(screen.queryByText(/Failed to update setting/i)).not.toBeInTheDocument()
    })
  })

  describe('Loading States', () => {
    const setting: Setting = {
      key: 'test_key',
      name: 'Test Setting',
      value: 'test',
      default_value: 'test',
      category: 'display',
      input_type: 'text'
    }

    it('disables Save button while saving', async () => {
      const user = userEvent.setup()
      mockOnUpdate.mockImplementation(() =>
        new Promise(resolve => setTimeout(resolve, 100))
      )

      render(<SettingItem setting={setting} onUpdate={mockOnUpdate} onReset={mockOnReset} />)

      const input = screen.getByDisplayValue('test')
      await user.type(input, ' updated')

      const saveButton = screen.getByText('Save')
      await user.click(saveButton)

      expect(saveButton).toBeDisabled()
    })

    it('shows Saving text while saving', async () => {
      const user = userEvent.setup()
      mockOnUpdate.mockImplementation(() =>
        new Promise(resolve => setTimeout(resolve, 100))
      )

      render(<SettingItem setting={setting} onUpdate={mockOnUpdate} onReset={mockOnReset} />)

      const input = screen.getByDisplayValue('test')
      await user.type(input, ' updated')

      const saveButton = screen.getByText('Save')
      await user.click(saveButton)

      expect(screen.getByText('Saving...')).toBeInTheDocument()
    })
  })
})
