// ABOUTME: Test suite for SettingsContext with comprehensive coverage
// ABOUTME: Tests settings fetching, updating, currency changes, refresh intervals, and error handling

import { renderHook, waitFor, act } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import axios from 'axios'
import { SettingsProvider, useSettings } from './SettingsContext'
import { toast } from 'react-toastify'

// Mock axios
vi.mock('axios')
const mockedAxios = axios as jest.Mocked<typeof axios>

// Mock toast
vi.mock('react-toastify', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}))

describe('SettingsContext', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('Settings Initialization', () => {
    it('should fetch display and system settings on mount', async () => {
      const displaySettings = [
        {
          key: 'base_currency',
          value: 'EUR',
          category: 'display',
          name: 'Base Currency',
          input_type: 'select',
          options: ['EUR', 'USD', 'GBP', 'CHF'],
        },
        {
          key: 'date_format',
          value: 'YYYY-MM-DD',
          category: 'display',
          name: 'Date Format',
          input_type: 'select',
          options: ['YYYY-MM-DD', 'DD/MM/YYYY', 'MM/DD/YYYY'],
        },
        {
          key: 'number_format',
          value: 'en-US',
          category: 'display',
          name: 'Number Format',
          input_type: 'select',
          options: ['en-US', 'de-DE', 'fr-FR', 'en-GB'],
        },
      ]

      const systemSettings = [
        {
          key: 'crypto_price_refresh_seconds',
          value: '60',
          category: 'system',
          name: 'Crypto Refresh Interval',
          input_type: 'number',
          min_value: 30,
          max_value: 600,
        },
        {
          key: 'stock_price_refresh_seconds',
          value: '120',
          category: 'system',
          name: 'Stock Refresh Interval',
          input_type: 'number',
          min_value: 60,
          max_value: 600,
        },
        {
          key: 'cache_ttl_hours',
          value: '1',
          category: 'system',
          name: 'Cache TTL',
          input_type: 'number',
          min_value: 1,
          max_value: 48,
        },
      ]

      mockedAxios.get.mockImplementation((url: string) => {
        if (url.includes('/api/settings/category/display')) {
          return Promise.resolve({ data: displaySettings })
        }
        if (url.includes('/api/settings/category/system')) {
          return Promise.resolve({ data: systemSettings })
        }
        return Promise.reject(new Error('Unknown URL'))
      })

      const { result } = renderHook(() => useSettings(), {
        wrapper: SettingsProvider,
      })

      // Initially loading
      expect(result.current.isLoading).toBe(true)

      // Wait for settings to load
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Verify settings were loaded correctly
      expect(result.current.baseCurrency).toBe('EUR')
      expect(result.current.dateFormat).toBe('YYYY-MM-DD')
      expect(result.current.numberFormat).toBe('en-US')
      expect(result.current.cryptoRefreshSeconds).toBe(60)
      expect(result.current.stockRefreshSeconds).toBe(120)
      expect(result.current.cacheTtlHours).toBe(1)

      // Verify API was called correctly
      expect(mockedAxios.get).toHaveBeenCalledWith(
        expect.stringContaining('/api/settings/category/display')
      )
      expect(mockedAxios.get).toHaveBeenCalledWith(
        expect.stringContaining('/api/settings/category/system')
      )
    })

    it('should handle API errors during initialization gracefully', async () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      mockedAxios.get.mockRejectedValue(new Error('Network error'))

      const { result } = renderHook(() => useSettings(), {
        wrapper: SettingsProvider,
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Should have default values even on error
      expect(result.current.baseCurrency).toBe('EUR')
      expect(result.current.cryptoRefreshSeconds).toBe(60)
      expect(result.current.stockRefreshSeconds).toBe(120)

      expect(consoleErrorSpy).toHaveBeenCalled()
      consoleErrorSpy.mockRestore()
    })
  })

  describe('Update Setting', () => {
    it('should update a setting via API and refresh state', async () => {
      const initialSettings = [
        { key: 'base_currency', value: 'EUR', category: 'display' },
      ]
      const updatedSettings = [
        { key: 'base_currency', value: 'USD', category: 'display' },
      ]

      mockedAxios.get.mockResolvedValue({ data: initialSettings })
      mockedAxios.put.mockResolvedValue({ data: { success: true } })

      const { result } = renderHook(() => useSettings(), {
        wrapper: SettingsProvider,
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.baseCurrency).toBe('EUR')

      // Update the setting
      mockedAxios.get.mockResolvedValue({ data: updatedSettings })

      await act(async () => {
        await result.current.updateSetting('base_currency', 'USD')
      })

      // Wait for refresh
      await waitFor(() => {
        expect(result.current.baseCurrency).toBe('USD')
      })

      // Verify API calls
      expect(mockedAxios.put).toHaveBeenCalledWith(
        expect.stringContaining('/api/settings/base_currency'),
        { value: 'USD' }
      )
      expect(toast.success).toHaveBeenCalledWith('Setting updated successfully')
    })

    it('should handle update errors and show error toast', async () => {
      const initialSettings = [
        { key: 'base_currency', value: 'EUR', category: 'display' },
      ]

      mockedAxios.get.mockResolvedValue({ data: initialSettings })
      mockedAxios.put.mockRejectedValue(new Error('Update failed'))

      const { result } = renderHook(() => useSettings(), {
        wrapper: SettingsProvider,
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // updateSetting throws on error, so we need to catch it
      await act(async () => {
        try {
          await result.current.updateSetting('base_currency', 'USD')
        } catch {
          // Expected to throw
        }
      })

      // State should remain unchanged on error
      expect(result.current.baseCurrency).toBe('EUR')
      expect(toast.error).toHaveBeenCalledWith('Failed to update setting')
    })
  })

  describe('Currency Change Side Effect', () => {
    it('should trigger portfolio recalculation when base_currency changes', async () => {
      const initialSettings = [
        { key: 'base_currency', value: 'EUR', category: 'display' },
      ]
      const updatedSettings = [
        { key: 'base_currency', value: 'USD', category: 'display' },
      ]

      mockedAxios.get.mockResolvedValue({ data: initialSettings })
      mockedAxios.put.mockResolvedValue({ data: { success: true } })
      mockedAxios.post.mockResolvedValue({ data: { success: true } })

      const { result } = renderHook(() => useSettings(), {
        wrapper: SettingsProvider,
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Update currency
      mockedAxios.get.mockResolvedValue({ data: updatedSettings })

      await act(async () => {
        await result.current.updateSetting('base_currency', 'USD')
      })

      // Verify portfolio recalculation was triggered
      await waitFor(() => {
        expect(mockedAxios.post).toHaveBeenCalledWith(
          expect.stringContaining('/api/portfolio/recalculate-positions')
        )
      })

      expect(toast.success).toHaveBeenCalledWith(
        'Portfolio recalculated for new currency'
      )
    })

    it('should not trigger portfolio recalculation for other display settings', async () => {
      const initialSettings = [
        { key: 'date_format', value: 'YYYY-MM-DD', category: 'display' },
      ]
      const updatedSettings = [
        { key: 'date_format', value: 'DD/MM/YYYY', category: 'display' },
      ]

      mockedAxios.get.mockResolvedValue({ data: initialSettings })
      mockedAxios.put.mockResolvedValue({ data: { success: true } })

      const { result } = renderHook(() => useSettings(), {
        wrapper: SettingsProvider,
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Update date format
      mockedAxios.get.mockResolvedValue({ data: updatedSettings })

      await act(async () => {
        await result.current.updateSetting('date_format', 'DD/MM/YYYY')
      })

      // Verify NO portfolio recalculation was triggered
      expect(mockedAxios.post).not.toHaveBeenCalledWith(
        expect.stringContaining('/api/portfolio/recalculate-positions')
      )
    })
  })

  describe('Refresh Intervals', () => {
    it('should update crypto refresh interval and maintain valid state', async () => {
      const initialSettings = [
        {
          key: 'crypto_price_refresh_seconds',
          value: '60',
          category: 'system',
        },
      ]
      const updatedSettings = [
        {
          key: 'crypto_price_refresh_seconds',
          value: '120',
          category: 'system',
        },
      ]

      mockedAxios.get.mockResolvedValue({ data: initialSettings })
      mockedAxios.put.mockResolvedValue({ data: { success: true } })

      const { result } = renderHook(() => useSettings(), {
        wrapper: SettingsProvider,
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.cryptoRefreshSeconds).toBe(60)

      // Update interval
      mockedAxios.get.mockResolvedValue({ data: updatedSettings })

      await act(async () => {
        await result.current.updateSetting('crypto_price_refresh_seconds', '120')
      })

      await waitFor(() => {
        expect(result.current.cryptoRefreshSeconds).toBe(120)
      })

      expect(mockedAxios.put).toHaveBeenCalledWith(
        expect.stringContaining('/api/settings/crypto_price_refresh_seconds'),
        { value: '120' }
      )
    })

    it('should update stock refresh interval and maintain valid state', async () => {
      const initialSettings = [
        {
          key: 'stock_price_refresh_seconds',
          value: '120',
          category: 'system',
        },
      ]
      const updatedSettings = [
        {
          key: 'stock_price_refresh_seconds',
          value: '300',
          category: 'system',
        },
      ]

      mockedAxios.get.mockResolvedValue({ data: initialSettings })
      mockedAxios.put.mockResolvedValue({ data: { success: true } })

      const { result } = renderHook(() => useSettings(), {
        wrapper: SettingsProvider,
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.stockRefreshSeconds).toBe(120)

      // Update interval
      mockedAxios.get.mockResolvedValue({ data: updatedSettings })

      await act(async () => {
        await result.current.updateSetting('stock_price_refresh_seconds', '300')
      })

      await waitFor(() => {
        expect(result.current.stockRefreshSeconds).toBe(300)
      })

      expect(mockedAxios.put).toHaveBeenCalledWith(
        expect.stringContaining('/api/settings/stock_price_refresh_seconds'),
        { value: '300' }
      )
    })
  })

  describe('Manual Refresh', () => {
    it('should allow manual refresh of all settings', async () => {
      const initialSettings = [
        { key: 'base_currency', value: 'EUR', category: 'display' },
      ]
      const refreshedSettings = [
        { key: 'base_currency', value: 'USD', category: 'display' },
      ]

      mockedAxios.get.mockResolvedValueOnce({ data: initialSettings })

      const { result } = renderHook(() => useSettings(), {
        wrapper: SettingsProvider,
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.baseCurrency).toBe('EUR')

      // Mock updated settings from backend
      mockedAxios.get.mockResolvedValueOnce({ data: refreshedSettings })
      mockedAxios.get.mockResolvedValueOnce({ data: [] })

      // Manually refresh
      await act(async () => {
        await result.current.refreshSettings()
      })

      await waitFor(() => {
        expect(result.current.baseCurrency).toBe('USD')
      })
    })
  })

  describe('Context Usage', () => {
    it('should throw error when useSettings is used outside provider', () => {
      // Suppress console.error for this test
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      expect(() => {
        renderHook(() => useSettings())
      }).toThrow('useSettings must be used within a SettingsProvider')

      consoleErrorSpy.mockRestore()
    })
  })
})
