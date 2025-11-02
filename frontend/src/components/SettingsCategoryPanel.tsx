// ABOUTME: Settings category panel component displaying all settings for a specific category
// ABOUTME: Fetches and renders settings from the backend API with loading and error states

import { useEffect, useState, useCallback } from 'react'
import axios from 'axios'
import { API_CONFIG } from '../config/app.config'
import { SettingItem } from './SettingItem'
import './SettingsCategoryPanel.css'

const API_URL = API_CONFIG.BASE_URL

export interface Setting {
  key: string
  name: string
  value: string | number | boolean
  default_value: string | number | boolean
  description?: string
  category: string
  input_type: 'text' | 'password' | 'number' | 'select' | 'checkbox'
  options?: string[]
  is_sensitive?: boolean
  validation_regex?: string
  min_value?: number
  max_value?: number
}

export interface SettingsCategoryPanelProps {
  categoryKey: string
}

export const SettingsCategoryPanel: React.FC<SettingsCategoryPanelProps> = ({
  categoryKey
}) => {
  const [settings, setSettings] = useState<Setting[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchSettings = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await axios.get<Setting[]>(
        `${API_URL}/api/settings/category/${categoryKey}`
      )
      setSettings(response.data)
      setLoading(false)
    } catch (err) {
      console.error(`Failed to fetch settings for category ${categoryKey}:`, err)
      setError('Failed to load settings')
      setLoading(false)
    }
  }, [categoryKey])

  useEffect(() => {
    fetchSettings()
  }, [fetchSettings])

  const handleSettingUpdate = async (key: string, newValue: string | number | boolean) => {
    try {
      await axios.put(`${API_URL}/api/settings/${key}`, { value: newValue })

      // Update local state
      setSettings(prevSettings =>
        prevSettings.map(setting =>
          setting.key === key ? { ...setting, value: newValue } : setting
        )
      )
    } catch (err) {
      console.error(`Failed to update setting ${key}:`, err)
      throw err
    }
  }

  const handleSettingReset = async (key: string) => {
    try {
      await axios.post(`${API_URL}/api/settings/${key}/reset`)

      // Refetch settings to get the reset value
      await fetchSettings()
    } catch (err) {
      console.error(`Failed to reset setting ${key}:`, err)
      throw err
    }
  }

  if (loading) {
    return (
      <div className="settings-category-panel loading">
        <div className="loading-spinner"></div>
        <p>Loading...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="settings-category-panel error">
        <div className="error-icon">⚠️</div>
        <p>{error}</p>
        <button onClick={fetchSettings} className="retry-button">
          Retry
        </button>
      </div>
    )
  }

  if (settings.length === 0) {
    return (
      <div className="settings-category-panel empty">
        <p>No settings available for this category</p>
      </div>
    )
  }

  return (
    <div className="settings-category-panel">
      <div className="settings-list">
        {settings.map((setting) => (
          <SettingItem
            key={setting.key}
            setting={setting}
            onUpdate={handleSettingUpdate}
            onReset={handleSettingReset}
          />
        ))}
      </div>
    </div>
  )
}

export default SettingsCategoryPanel
