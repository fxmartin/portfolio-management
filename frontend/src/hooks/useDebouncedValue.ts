// ABOUTME: Custom hook for debouncing values to reduce unnecessary updates
// ABOUTME: Useful for search inputs and other rapidly changing values

import { useState, useEffect } from 'react'

/**
 * Debounce a value with a specified delay
 * @param value - The value to debounce
 * @param delay - Delay in milliseconds (default: 300)
 * @returns Debounced value
 */
export function useDebouncedValue<T>(value: T, delay: number = 300): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value)

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value)
    }, delay)

    return () => {
      clearTimeout(handler)
    }
  }, [value, delay])

  return debouncedValue
}
