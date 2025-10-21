// ABOUTME: Application configuration for refresh intervals and API settings
// ABOUTME: Provides centralized configuration with environment variable overrides

/**
 * Refresh interval configuration (in milliseconds)
 */
export const REFRESH_INTERVALS = {
  // Crypto prices refresh every 60 seconds (24/7 trading)
  CRYPTO_PRICES: parseInt(import.meta.env.VITE_CRYPTO_REFRESH_INTERVAL || '60000'),

  // Stock prices refresh every 2 minutes (only during market hours)
  STOCK_PRICES: parseInt(import.meta.env.VITE_STOCK_REFRESH_INTERVAL || '120000'),

  // Portfolio summary refresh (same as crypto for now)
  PORTFOLIO_SUMMARY: parseInt(import.meta.env.VITE_PORTFOLIO_REFRESH_INTERVAL || '60000'),

  // Holdings table refresh (same as crypto for now)
  HOLDINGS_TABLE: parseInt(import.meta.env.VITE_HOLDINGS_REFRESH_INTERVAL || '60000'),
}

/**
 * API configuration
 */
export const API_CONFIG = {
  BASE_URL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  TIMEOUT: parseInt(import.meta.env.VITE_API_TIMEOUT || '30000'),
}

/**
 * Portfolio configuration
 */
export const PORTFOLIO_CONFIG = {
  BASE_CURRENCY: import.meta.env.VITE_BASE_CURRENCY || 'EUR',
  DEFAULT_DECIMAL_PLACES: 2,
  CRYPTO_DECIMAL_PLACES: 8,
}

/**
 * Helper to format refresh interval for display
 */
export function formatRefreshInterval(milliseconds: number): string {
  const seconds = Math.floor(milliseconds / 1000)
  const minutes = Math.floor(seconds / 60)

  if (minutes > 0) {
    const remainingSeconds = seconds % 60
    if (remainingSeconds > 0) {
      return `${minutes}m ${remainingSeconds}s`
    }
    return `${minutes}m`
  }

  return `${seconds}s`
}
