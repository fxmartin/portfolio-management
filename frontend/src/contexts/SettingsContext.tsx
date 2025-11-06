// ABOUTME: React context for global settings management (display and system settings)
// ABOUTME: Provides settings to all components and handles side effects like currency changes

import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react'
import axios from 'axios'
import { toast } from 'react-toastify'
import { API_CONFIG } from '../config/app.config'

const API_URL = API_CONFIG.BASE_URL

interface Setting {
  key: string
  value: string | number | boolean
  category: string
  name?: string
  input_type?: string
  options?: string[]
  min_value?: number
  max_value?: number
}

interface SettingsContextType {
  // Display settings
  baseCurrency: string
  dateFormat: string
  numberFormat: string

  // System settings
  cryptoRefreshSeconds: number
  stockRefreshSeconds: number
  cacheTtlHours: number

  // Actions
  updateSetting: (key: string, value: string) => Promise<void>
  refreshSettings: () => Promise<void>

  // State
  isLoading: boolean
}

const SettingsContext = createContext<SettingsContextType | undefined>(undefined)

export const SettingsProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  // Display settings state
  const [baseCurrency, setBaseCurrency] = useState<string>('EUR')
  const [dateFormat, setDateFormat] = useState<string>('YYYY-MM-DD')
  const [numberFormat, setNumberFormat] = useState<string>('en-US')

  // System settings state
  const [cryptoRefreshSeconds, setCryptoRefreshSeconds] = useState<number>(60)
  const [stockRefreshSeconds, setStockRefreshSeconds] = useState<number>(120)
  const [cacheTtlHours, setCacheTtlHours] = useState<number>(1)

  // Loading state
  const [isLoading, setIsLoading] = useState(true)

  // Fetch settings from backend
  const fetchSettings = useCallback(async () => {
    try {
      setIsLoading(true)

      // Fetch display and system settings in parallel
      const [displayResponse, systemResponse] = await Promise.all([
        axios.get<Setting[]>(`${API_URL}/api/settings/category/display`),
        axios.get<Setting[]>(`${API_URL}/api/settings/category/system`),
      ])

      // Update display settings
      displayResponse.data.forEach((setting) => {
        switch (setting.key) {
          case 'base_currency':
            setBaseCurrency(String(setting.value))
            break
          case 'date_format':
            setDateFormat(String(setting.value))
            break
          case 'number_format':
            setNumberFormat(String(setting.value))
            break
        }
      })

      // Update system settings
      systemResponse.data.forEach((setting) => {
        switch (setting.key) {
          case 'crypto_price_refresh_seconds':
            setCryptoRefreshSeconds(parseInt(String(setting.value), 10))
            break
          case 'stock_price_refresh_seconds':
            setStockRefreshSeconds(parseInt(String(setting.value), 10))
            break
          case 'cache_ttl_hours':
            setCacheTtlHours(parseInt(String(setting.value), 10))
            break
        }
      })

      setIsLoading(false)
    } catch (error) {
      console.error('Failed to fetch settings:', error)
      setIsLoading(false)
      // Keep default values on error
    }
  }, [])

  // Fetch settings on mount
  useEffect(() => {
    fetchSettings()
  }, [fetchSettings])

  // Update a setting
  const updateSetting = useCallback(async (key: string, value: string) => {
    try {
      // Update setting via API
      await axios.put(`${API_URL}/api/settings/${key}`, { value })

      // Handle side effects based on the setting key
      if (key === 'base_currency') {
        // Trigger portfolio recalculation for currency changes
        try {
          await axios.post(`${API_URL}/api/portfolio/recalculate-positions`)
          toast.success('Portfolio recalculated for new currency')
        } catch (recalcError) {
          console.error('Failed to recalculate portfolio:', recalcError)
          toast.error('Failed to recalculate portfolio')
          throw recalcError
        }
      }

      // Refresh all settings to get updated values
      await fetchSettings()

      toast.success('Setting updated successfully')
    } catch (error) {
      console.error('Failed to update setting:', error)
      toast.error('Failed to update setting')
      throw error
    }
  }, [fetchSettings])

  // Manual refresh function
  const refreshSettings = useCallback(async () => {
    await fetchSettings()
  }, [fetchSettings])

  const value: SettingsContextType = {
    baseCurrency,
    dateFormat,
    numberFormat,
    cryptoRefreshSeconds,
    stockRefreshSeconds,
    cacheTtlHours,
    updateSetting,
    refreshSettings,
    isLoading,
  }

  return (
    <SettingsContext.Provider value={value}>
      {children}
    </SettingsContext.Provider>
  )
}

// Export hook separately to avoid fast-refresh issues
// eslint-disable-next-line react-refresh/only-export-components
export function useSettings() {
  const context = useContext(SettingsContext)
  if (context === undefined) {
    throw new Error('useSettings must be used within a SettingsProvider')
  }
  return context
}
