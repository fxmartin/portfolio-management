// ABOUTME: Settings page component for managing portfolio preferences and configuration
// ABOUTME: Provides category-based navigation with Display, API Keys, AI Settings, System, and Advanced tabs

import { useEffect, useState, useCallback } from 'react'
import { Settings } from 'lucide-react'
import axios from 'axios'
import { API_CONFIG } from '../config/app.config'
import { SettingsCategoryPanel } from '../components/SettingsCategoryPanel'
import './SettingsPage.css'

const API_URL = API_CONFIG.BASE_URL

export interface SettingsCategory {
  name: string
  key: string
  description?: string
}

export const SettingsPage: React.FC = () => {
  const [categories, setCategories] = useState<SettingsCategory[]>([])
  const [activeCategory, setActiveCategory] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchCategories = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await axios.get<SettingsCategory[]>(`${API_URL}/api/settings/categories`)
      setCategories(response.data)

      // Set first category as active by default
      if (response.data.length > 0 && !activeCategory) {
        setActiveCategory(response.data[0].key)
      }

      setLoading(false)
    } catch (err) {
      console.error('Failed to fetch settings categories:', err)
      setError('Failed to load settings categories')
      setLoading(false)
    }
  }, [activeCategory])

  useEffect(() => {
    fetchCategories()
  }, [fetchCategories])

  const handleCategoryClick = (categoryKey: string) => {
    setActiveCategory(categoryKey)
  }

  if (loading) {
    return (
      <div className="settings-page">
        <header className="page-header" role="banner">
          <div className="header-content">
            <div className="header-icon">
              <Settings size={32} />
            </div>
            <div className="header-text">
              <h1>Settings</h1>
              <p className="subtitle">
                Manage your portfolio preferences and configuration
              </p>
            </div>
          </div>
        </header>
        <section className="settings-content">
          <div className="loading-state">
            <div className="loading-spinner"></div>
            <p>Loading settings...</p>
          </div>
        </section>
      </div>
    )
  }

  if (error) {
    return (
      <div className="settings-page">
        <header className="page-header" role="banner">
          <div className="header-content">
            <div className="header-icon">
              <Settings size={32} />
            </div>
            <div className="header-text">
              <h1>Settings</h1>
              <p className="subtitle">
                Manage your portfolio preferences and configuration
              </p>
            </div>
          </div>
        </header>
        <section className="settings-content">
          <div className="error-state">
            <div className="error-icon">⚠️</div>
            <p>{error}</p>
            <button onClick={fetchCategories} className="retry-button">
              Retry
            </button>
          </div>
        </section>
      </div>
    )
  }

  return (
    <div className="settings-page">
      {/* Page Header */}
      <header className="page-header" role="banner">
        <div className="header-content">
          <div className="header-icon">
            <Settings size={32} />
          </div>
          <div className="header-text">
            <h1>Settings</h1>
            <p className="subtitle">
              Manage your portfolio preferences and configuration
            </p>
          </div>
        </div>
      </header>

      {/* Settings Content with Tab Navigation */}
      <section className="settings-content">
        {/* Category Tabs */}
        <div className="settings-tabs" role="tablist">
          {categories.map((category) => (
            <button
              key={category.key}
              className={`settings-tab ${activeCategory === category.key ? 'active' : ''}`}
              role="tab"
              aria-selected={activeCategory === category.key}
              onClick={() => handleCategoryClick(category.key)}
            >
              {category.name}
            </button>
          ))}
        </div>

        {/* Category Content */}
        <div className="settings-panel">
          {activeCategory && (
            <SettingsCategoryPanel categoryKey={activeCategory} />
          )}
        </div>
      </section>
    </div>
  )
}

export default SettingsPage
