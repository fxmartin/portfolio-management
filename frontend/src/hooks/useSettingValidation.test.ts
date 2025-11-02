// ABOUTME: Test suite for useSettingValidation hook
// ABOUTME: Tests debounced validation, error handling, and cleanup behavior

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import axios from 'axios'
import { useSettingValidation } from './useSettingValidation'

// Mock axios
vi.mock('axios')

describe('useSettingValidation', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Initial State', () => {
    it('returns initial state with isValid=true, no error, not validating', () => {
      const { result } = renderHook(() => useSettingValidation('test_key', 'initial'))

      expect(result.current.isValid).toBe(true)
      expect(result.current.error).toBeNull()
      expect(result.current.validating).toBe(false)
    })
  })

  describe('Debounced Validation', () => {
    it('does not validate immediately on value change', async () => {
      const { rerender } = renderHook(
        ({ value }) => useSettingValidation('test_key', value),
        { initialProps: { value: 'initial' } }
      )

      rerender({ value: 'changed' })

      // Wait a bit less than debounce time
      await new Promise(resolve => setTimeout(resolve, 100))
      expect(axios.post).not.toHaveBeenCalled()
    })

    it('validates after 300ms debounce delay', async () => {
      const mockResponse = { data: { valid: true, error: null } }
      vi.mocked(axios.post).mockResolvedValue(mockResponse)

      const { result, rerender } = renderHook(
        ({ value }) => useSettingValidation('test_key', value),
        { initialProps: { value: 'initial' } }
      )

      rerender({ value: 'new_value' })

      // Wait for debounce + API call
      await waitFor(() => {
        expect(axios.post).toHaveBeenCalledWith(
          'http://localhost:8000/api/settings/test_key/validate',
          { value: 'new_value' }
        )
      }, { timeout: 1000 })

      expect(result.current.isValid).toBe(true)
      expect(result.current.error).toBeNull()
    })

    it('cancels previous validation on rapid value changes', async () => {
      const mockResponse = { data: { valid: true, error: null } }
      vi.mocked(axios.post).mockResolvedValue(mockResponse)

      const { rerender } = renderHook(
        ({ value }) => useSettingValidation('test_key', value),
        { initialProps: { value: 'initial' } }
      )

      // Change value multiple times rapidly
      rerender({ value: 'change1' })
      await new Promise(resolve => setTimeout(resolve, 50))

      rerender({ value: 'change2' })
      await new Promise(resolve => setTimeout(resolve, 50))

      rerender({ value: 'change3' })

      // Should only validate once with the final value
      await waitFor(() => {
        expect(axios.post).toHaveBeenCalledWith(
          'http://localhost:8000/api/settings/test_key/validate',
          { value: 'change3' }
        )
      }, { timeout: 1000 })

      expect(axios.post).toHaveBeenCalledTimes(1)
    })
  })

  describe('Validation States', () => {
    it('sets validating=true during API call', async () => {
      let resolveValidation: (value: any) => void
      const validationPromise = new Promise(resolve => {
        resolveValidation = resolve
      })

      vi.mocked(axios.post).mockReturnValue(validationPromise as any)

      const { result, rerender } = renderHook(
        ({ value }) => useSettingValidation('test_key', value),
        { initialProps: { value: 'initial' } }
      )

      rerender({ value: 'new_value' })

      // Wait for validation to start
      await waitFor(() => {
        expect(result.current.validating).toBe(true)
      }, { timeout: 1000 })

      // Resolve the validation
      resolveValidation!({ data: { valid: true, error: null } })

      await waitFor(() => {
        expect(result.current.validating).toBe(false)
      })
    })

    it('sets isValid=false and error message when validation fails', async () => {
      const mockResponse = {
        data: {
          valid: false,
          error: 'Value must be at least 5 characters'
        }
      }
      vi.mocked(axios.post).mockResolvedValue(mockResponse)

      const { result, rerender } = renderHook(
        ({ value }) => useSettingValidation('test_key', value),
        { initialProps: { value: 'initial' } }
      )

      rerender({ value: 'abc' })

      await waitFor(() => {
        expect(result.current.isValid).toBe(false)
        expect(result.current.error).toBe('Value must be at least 5 characters')
        expect(result.current.validating).toBe(false)
      }, { timeout: 1000 })
    })

    it('sets isValid=true when validation succeeds', async () => {
      const mockResponse = { data: { valid: true, error: null } }
      vi.mocked(axios.post).mockResolvedValue(mockResponse)

      const { result, rerender } = renderHook(
        ({ value }) => useSettingValidation('test_key', value),
        { initialProps: { value: 'initial' } }
      )

      rerender({ value: 'valid_value' })

      await waitFor(() => {
        expect(result.current.isValid).toBe(true)
        expect(result.current.error).toBeNull()
        expect(result.current.validating).toBe(false)
      }, { timeout: 1000 })
    })
  })

  describe('Error Handling', () => {
    it('handles API error gracefully', async () => {
      vi.mocked(axios.post).mockRejectedValue(new Error('Network error'))

      const { result, rerender } = renderHook(
        ({ value }) => useSettingValidation('test_key', value),
        { initialProps: { value: 'initial' } }
      )

      rerender({ value: 'new_value' })

      await waitFor(() => {
        expect(result.current.isValid).toBe(false)
        expect(result.current.error).toBe('Validation failed')
        expect(result.current.validating).toBe(false)
      }, { timeout: 1000 })
    })

    it('handles missing error field in response', async () => {
      const mockResponse = { data: { valid: false } }
      vi.mocked(axios.post).mockResolvedValue(mockResponse)

      const { result, rerender } = renderHook(
        ({ value }) => useSettingValidation('test_key', value),
        { initialProps: { value: 'initial' } }
      )

      rerender({ value: 'invalid' })

      await waitFor(() => {
        expect(result.current.isValid).toBe(false)
        expect(result.current.error).toBeNull()
        expect(result.current.validating).toBe(false)
      }, { timeout: 1000 })
    })
  })

  describe('Cleanup', () => {
    it('clears timeout on unmount', async () => {
      const { rerender, unmount } = renderHook(
        ({ value }) => useSettingValidation('test_key', value),
        { initialProps: { value: 'initial' } }
      )

      rerender({ value: 'new_value' })

      // Unmount before timeout completes
      unmount()

      await new Promise(resolve => setTimeout(resolve, 400))

      // Should not call API after unmount
      expect(axios.post).not.toHaveBeenCalled()
    })

    it('clears timeout on value change', async () => {
      const mockResponse = { data: { valid: true, error: null } }
      vi.mocked(axios.post).mockResolvedValue(mockResponse)

      const { rerender } = renderHook(
        ({ value }) => useSettingValidation('test_key', value),
        { initialProps: { value: 'initial' } }
      )

      rerender({ value: 'value1' })
      await new Promise(resolve => setTimeout(resolve, 100))

      rerender({ value: 'value2' })

      // Should only validate once with value2
      await waitFor(() => {
        expect(axios.post).toHaveBeenCalledWith(
          'http://localhost:8000/api/settings/test_key/validate',
          { value: 'value2' }
        )
      }, { timeout: 1000 })

      expect(axios.post).toHaveBeenCalledTimes(1)
    })
  })

  describe('Edge Cases', () => {
    it('handles empty string value', async () => {
      const mockResponse = { data: { valid: false, error: 'Value cannot be empty' } }
      vi.mocked(axios.post).mockResolvedValue(mockResponse)

      const { result, rerender } = renderHook(
        ({ value }) => useSettingValidation('test_key', value),
        { initialProps: { value: 'initial' } }
      )

      rerender({ value: '' })

      await waitFor(() => {
        expect(result.current.isValid).toBe(false)
        expect(result.current.error).toBe('Value cannot be empty')
      }, { timeout: 1000 })
    })

    it('handles number values', async () => {
      const mockResponse = { data: { valid: true, error: null } }
      vi.mocked(axios.post).mockResolvedValue(mockResponse)

      const { result, rerender } = renderHook(
        ({ value }) => useSettingValidation('cache_ttl', value),
        { initialProps: { value: 3600 } }
      )

      rerender({ value: 7200 })

      await waitFor(() => {
        expect(axios.post).toHaveBeenCalledWith(
          'http://localhost:8000/api/settings/cache_ttl/validate',
          { value: 7200 }
        )
        expect(result.current.isValid).toBe(true)
      }, { timeout: 1000 })
    })

    it('handles boolean values', async () => {
      const mockResponse = { data: { valid: true, error: null } }
      vi.mocked(axios.post).mockResolvedValue(mockResponse)

      const { result, rerender } = renderHook(
        ({ value }) => useSettingValidation('auto_refresh', value),
        { initialProps: { value: true } }
      )

      rerender({ value: false })

      await waitFor(() => {
        expect(axios.post).toHaveBeenCalledWith(
          'http://localhost:8000/api/settings/auto_refresh/validate',
          { value: false }
        )
        expect(result.current.isValid).toBe(true)
      }, { timeout: 1000 })
    })
  })

  describe('Multiple Settings', () => {
    it('validates different settings independently', async () => {
      const mockResponse1 = { data: { valid: true, error: null } }
      const mockResponse2 = { data: { valid: false, error: 'Invalid API key' } }

      vi.mocked(axios.post)
        .mockResolvedValueOnce(mockResponse1)
        .mockResolvedValueOnce(mockResponse2)

      const { result: result1, rerender: rerender1 } = renderHook(
        ({ value }) => useSettingValidation('setting1', value),
        { initialProps: { value: 'initial1' } }
      )

      const { result: result2, rerender: rerender2 } = renderHook(
        ({ value }) => useSettingValidation('setting2', value),
        { initialProps: { value: 'initial2' } }
      )

      rerender1({ value: 'valid_value' })
      rerender2({ value: 'invalid_key' })

      await waitFor(() => {
        expect(result1.current.isValid).toBe(true)
      }, { timeout: 1000 })

      await waitFor(() => {
        expect(result2.current.isValid).toBe(false)
        expect(result2.current.error).toBe('Invalid API key')
      }, { timeout: 1000 })
    })
  })
})
