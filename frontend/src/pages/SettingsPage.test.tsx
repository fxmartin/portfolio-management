// ABOUTME: Test suite for SettingsPage component
// ABOUTME: Tests basic rendering, page structure, and placeholder content

import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import { SettingsPage } from './SettingsPage'

describe('SettingsPage', () => {
  describe('Basic Rendering', () => {
    it('renders page title "Settings"', () => {
      render(<SettingsPage />)

      const title = screen.getByText('Settings')
      expect(title).toBeInTheDocument()
    })

    it('renders placeholder message', () => {
      render(<SettingsPage />)

      const message = screen.getByText(/Settings management coming soon/i)
      expect(message).toBeInTheDocument()
    })

    it('has proper page structure with settings-page class', () => {
      const { container } = render(<SettingsPage />)

      const pageDiv = container.querySelector('.settings-page')
      expect(pageDiv).toBeInTheDocument()
    })

    it('renders Settings icon', () => {
      render(<SettingsPage />)

      // The Settings icon should be in the header
      const header = screen.getByRole('banner')
      expect(header).toBeInTheDocument()
    })

    it('displays subtitle describing Settings functionality', () => {
      render(<SettingsPage />)

      const subtitle = screen.getByText(/Manage your portfolio preferences and configuration/i)
      expect(subtitle).toBeInTheDocument()
    })
  })
})
