// ABOUTME: Icon-only sidebar navigation component with expandable submenu
// ABOUTME: Provides navigation between Portfolio, Upload, and Database sections

import { useState, useEffect, useRef } from 'react'
import { LayoutDashboard, Upload, Database, BarChart3, Trash2 } from 'lucide-react'
import './Sidebar.css'

interface SidebarProps {
  activeTab: string
  onTabChange: (tab: string) => void
}

const Sidebar: React.FC<SidebarProps> = ({ activeTab, onTabChange }) => {
  const [isSubmenuOpen, setIsSubmenuOpen] = useState(false)
  const submenuRef = useRef<HTMLDivElement>(null)
  const databaseButtonRef = useRef<HTMLButtonElement>(null)

  // Close submenu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        isSubmenuOpen &&
        submenuRef.current &&
        databaseButtonRef.current &&
        !submenuRef.current.contains(event.target as Node) &&
        !databaseButtonRef.current.contains(event.target as Node)
      ) {
        setIsSubmenuOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [isSubmenuOpen])

  // Close submenu on Escape key
  useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && isSubmenuOpen) {
        setIsSubmenuOpen(false)
      }
    }

    document.addEventListener('keydown', handleEscape)
    return () => {
      document.removeEventListener('keydown', handleEscape)
    }
  }, [isSubmenuOpen])

  const handleMenuItemClick = (tab: string) => {
    onTabChange(tab)
  }

  const handleDatabaseClick = () => {
    setIsSubmenuOpen(!isSubmenuOpen)
  }

  const handleSubmenuItemClick = (tab: string) => {
    onTabChange(tab)
    setIsSubmenuOpen(false)
  }

  const handleKeyPress = (
    event: React.KeyboardEvent,
    callback: () => void
  ) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault()
      callback()
    }
  }

  const isDatabaseActive = activeTab.startsWith('database')

  return (
    <nav className="sidebar" role="navigation" aria-label="Main navigation">
      <div className="sidebar-items">
        {/* Portfolio */}
        <button
          className={`sidebar-item ${activeTab === 'portfolio' ? 'active' : ''}`}
          onClick={() => handleMenuItemClick('portfolio')}
          onKeyPress={(e) => handleKeyPress(e, () => handleMenuItemClick('portfolio'))}
          title="Portfolio"
          aria-label="Portfolio"
          tabIndex={0}
        >
          <LayoutDashboard size={24} />
        </button>

        {/* Upload */}
        <button
          className={`sidebar-item ${activeTab === 'upload' ? 'active' : ''}`}
          onClick={() => handleMenuItemClick('upload')}
          onKeyPress={(e) => handleKeyPress(e, () => handleMenuItemClick('upload'))}
          title="Upload"
          aria-label="Upload"
          tabIndex={0}
        >
          <Upload size={24} />
        </button>

        {/* Database with Submenu */}
        <div className="sidebar-item-wrapper">
          <button
            ref={databaseButtonRef}
            className={`sidebar-item ${isDatabaseActive ? 'active' : ''}`}
            onClick={handleDatabaseClick}
            onKeyPress={(e) => handleKeyPress(e, handleDatabaseClick)}
            title="Database"
            aria-label="Database"
            aria-expanded={isSubmenuOpen}
            aria-haspopup="true"
            tabIndex={0}
          >
            <Database size={24} />
          </button>

          {/* Submenu Flyout */}
          {isSubmenuOpen && (
            <div
              ref={submenuRef}
              className="sidebar-submenu"
              role="menu"
              aria-label="Database submenu"
            >
              <button
                className="submenu-item"
                onClick={() => handleSubmenuItemClick('database-stats')}
                onKeyPress={(e) =>
                  handleKeyPress(e, () => handleSubmenuItemClick('database-stats'))
                }
                role="menuitem"
                tabIndex={0}
              >
                <BarChart3 size={20} />
                <span>Stats</span>
              </button>
              <button
                className="submenu-item"
                onClick={() => handleSubmenuItemClick('database-reset')}
                onKeyPress={(e) =>
                  handleKeyPress(e, () => handleSubmenuItemClick('database-reset'))
                }
                role="menuitem"
                tabIndex={0}
              >
                <Trash2 size={20} />
                <span>Reset</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </nav>
  )
}

export default Sidebar
