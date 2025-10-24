// ABOUTME: Utility functions for formatting currency, percentages, and numbers
// ABOUTME: Provides consistent formatting across the application

/**
 * Format a number as currency with symbol and decimal places
 * @param value - Number to format
 * @param currency - Currency code (default: USD)
 * @param decimals - Number of decimal places (default: 2)
 * @returns Formatted currency string
 */
export function formatCurrency(
  value: number | null | undefined,
  currency: string = 'USD',
  decimals: number = 2
): string {
  if (value === null || value === undefined || isNaN(value)) {
    const symbol = getCurrencySymbol(currency)
    const zeroFormatted = (0).toLocaleString('en-US', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    })
    return `${symbol} ${zeroFormatted}`
  }

  const formatted = Math.abs(value).toLocaleString('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })
  const symbol = getCurrencySymbol(currency)

  return value < 0 ? `-${symbol} ${formatted}` : `${symbol} ${formatted}`
}

/**
 * Get currency symbol for a currency code
 * @param currency - Currency code (USD, EUR, GBP, etc.)
 * @returns Currency symbol
 */
export function getCurrencySymbol(currency: string): string {
  const symbols: Record<string, string> = {
    USD: '$',
    EUR: '€',
    GBP: '£',
    JPY: '¥',
    CHF: 'Fr',
    CAD: 'C$',
    AUD: 'A$',
  }

  return symbols[currency.toUpperCase()] || currency + ' '
}

/**
 * Format a percentage value
 * @param value - Percentage value (e.g., 5.25 for 5.25%)
 * @param decimals - Number of decimal places (default: 2)
 * @param showSign - Whether to show + for positive values (default: true)
 * @returns Formatted percentage string
 */
export function formatPercentage(
  value: number | null | undefined,
  decimals: number = 2,
  showSign: boolean = true
): string {
  if (value === null || value === undefined || isNaN(value)) {
    return '0.' + '0'.repeat(decimals) + '%'
  }

  const formatted = Math.abs(value).toFixed(decimals)
  const sign = value > 0 && showSign ? '+' : value < 0 ? '-' : ''

  return `${sign}${formatted}%`
}

/**
 * Format a number with commas and decimal places
 * @param value - Number to format
 * @param decimals - Number of decimal places (default: 2)
 * @returns Formatted number string
 */
export function formatNumber(
  value: number | null | undefined,
  decimals: number = 2
): string {
  if (value === null || value === undefined || isNaN(value)) {
    return '0.' + '0'.repeat(decimals)
  }

  return value.toLocaleString('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })
}

/**
 * Format a P&L change value with currency and percentage
 * @param amount - Dollar amount of change
 * @param percent - Percentage change
 * @param currency - Currency code
 * @returns Formatted change string like "+$123.45 (+5.25%)"
 */
export function formatPnLChange(
  amount: number | null | undefined,
  percent: number | null | undefined,
  currency: string = 'USD'
): string {
  if (amount === null || amount === undefined || isNaN(amount)) {
    return formatCurrency(0, currency) + ' (0.00%)'
  }

  const amountStr = formatCurrency(amount, currency)
  const percentStr = formatPercentage(percent || 0)
  const sign = amount >= 0 ? '+' : ''

  return `${sign}${amountStr} (${percentStr})`
}

/**
 * Format a date/time string for display
 * @param dateString - ISO date string
 * @param showTime - Whether to include time (default: true)
 * @returns Formatted date string
 */
export function formatDateTime(
  dateString: string | null | undefined,
  showTime: boolean = true
): string {
  if (!dateString) {
    return 'Never'
  }

  try {
    const date = new Date(dateString)

    if (showTime) {
      return date.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
        hour12: true,
        timeZoneName: 'short',
      })
    } else {
      return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
      })
    }
  } catch (e) {
    return 'Invalid Date'
  }
}

/**
 * Format a time ago string (e.g., "2 minutes ago")
 * @param dateString - ISO date string
 * @returns Formatted relative time string
 */
export function formatTimeAgo(dateString: string | null | undefined): string {
  if (!dateString) {
    return 'Never'
  }

  try {
    const date = new Date(dateString)
    const now = new Date()
    const seconds = Math.floor((now.getTime() - date.getTime()) / 1000)

    if (seconds < 60) {
      return 'Just now'
    }

    const minutes = Math.floor(seconds / 60)
    if (minutes < 60) {
      return `${minutes} minute${minutes === 1 ? '' : 's'} ago`
    }

    const hours = Math.floor(minutes / 60)
    if (hours < 24) {
      return `${hours} hour${hours === 1 ? '' : 's'} ago`
    }

    const days = Math.floor(hours / 24)
    if (days < 30) {
      return `${days} day${days === 1 ? '' : 's'} ago`
    }

    const months = Math.floor(days / 30)
    return `${months} month${months === 1 ? '' : 's'} ago`
  } catch (e) {
    return 'Unknown'
  }
}

/**
 * Get CSS class name for P&L values (positive, negative, neutral)
 * @param value - P&L value
 * @returns CSS class name
 */
export function getPnLClassName(value: number | null | undefined): string {
  if (value === null || value === undefined || isNaN(value)) {
    return 'neutral'
  }

  if (value > 0) {
    return 'profit'
  } else if (value < 0) {
    return 'loss'
  } else {
    return 'neutral'
  }
}
