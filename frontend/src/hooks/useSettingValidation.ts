// ABOUTME: React hook for debounced real-time validation of setting values
// ABOUTME: Calls validation API endpoint with 300ms debounce and returns validation state

import { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import { API_CONFIG } from '../config/app.config'

export interface ValidationResult {
  isValid: boolean
  error: string | null
  validating: boolean
}

/**
 * Hook for real-time validation of setting values with debouncing
 *
 * @param key - The setting key to validate
 * @param value - The current value to validate
 * @returns Validation state object with isValid, error, and validating flags
 */
export const useSettingValidation = (
  key: string,
  value: string | number | boolean
): ValidationResult => {
  const [isValid, setIsValid] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [validating, setValidating] = useState(false)
  const timeoutRef = useRef<NodeJS.Timeout | undefined>(undefined)

  useEffect(() => {
    // Clear previous timeout
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
    }

    // Debounce validation by 300ms
    timeoutRef.current = setTimeout(async () => {
      setValidating(true)
      try {
        const response = await axios.post(
          `${API_CONFIG.BASE_URL}/api/settings/${key}/validate`,
          { value }
        )
        setIsValid(response.data.valid)
        setError(response.data.error || null)
      } catch (err) {
        setIsValid(false)
        setError('Validation failed')
      } finally {
        setValidating(false)
      }
    }, 300)

    // Cleanup function to clear timeout
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
    }
  }, [key, value])

  return { isValid, error, validating }
}
