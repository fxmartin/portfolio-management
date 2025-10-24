// ABOUTME: Tests for formatting utility functions
// ABOUTME: Tests currency, percentage, number, and date formatting

import { describe, it, expect } from 'vitest'
import {
  formatCurrency,
  getCurrencySymbol,
  formatPercentage,
  formatNumber,
  formatPnLChange,
  formatDateTime,
  formatTimeAgo,
  getPnLClassName,
} from './formatters'

describe('formatCurrency', () => {
  it('should format positive USD amounts correctly', () => {
    expect(formatCurrency(1234.56)).toBe('$ 1,234.56')
    expect(formatCurrency(0)).toBe('$ 0.00')
    expect(formatCurrency(1000000)).toBe('$ 1,000,000.00')
  })

  it('should format negative amounts with minus sign', () => {
    expect(formatCurrency(-1234.56)).toBe('-$ 1,234.56')
    expect(formatCurrency(-0.01)).toBe('-$ 0.01')
  })

  it('should handle different currencies', () => {
    expect(formatCurrency(100, 'EUR')).toBe('€ 100.00')
    expect(formatCurrency(100, 'GBP')).toBe('£ 100.00')
    expect(formatCurrency(100, 'JPY')).toBe('¥ 100.00')
  })

  it('should handle custom decimal places', () => {
    expect(formatCurrency(1234.5678, 'USD', 4)).toBe('$ 1,234.5678')
    expect(formatCurrency(1234.5678, 'USD', 0)).toBe('$ 1,235')
    expect(formatCurrency(10, 'USD', 3)).toBe('$ 10.000')
  })

  it('should handle null and undefined values', () => {
    expect(formatCurrency(null)).toBe('$ 0.00')
    expect(formatCurrency(undefined)).toBe('$ 0.00')
    expect(formatCurrency(NaN)).toBe('$ 0.00')
  })

  it('should handle very large numbers', () => {
    expect(formatCurrency(1234567890.12)).toBe('$ 1,234,567,890.12')
  })

  it('should handle very small numbers', () => {
    expect(formatCurrency(0.01)).toBe('$ 0.01')
    expect(formatCurrency(0.001)).toBe('$ 0.00')
  })
})

describe('getCurrencySymbol', () => {
  it('should return correct symbols for supported currencies', () => {
    expect(getCurrencySymbol('USD')).toBe('$')
    expect(getCurrencySymbol('EUR')).toBe('€')
    expect(getCurrencySymbol('GBP')).toBe('£')
    expect(getCurrencySymbol('JPY')).toBe('¥')
    expect(getCurrencySymbol('CHF')).toBe('Fr')
    expect(getCurrencySymbol('CAD')).toBe('C$')
    expect(getCurrencySymbol('AUD')).toBe('A$')
  })

  it('should handle lowercase currency codes', () => {
    expect(getCurrencySymbol('usd')).toBe('$')
    expect(getCurrencySymbol('eur')).toBe('€')
  })

  it('should return currency code with space for unsupported currencies', () => {
    expect(getCurrencySymbol('XXX')).toBe('XXX ')
    expect(getCurrencySymbol('ABC')).toBe('ABC ')
  })
})

describe('formatPercentage', () => {
  it('should format positive percentages with + sign by default', () => {
    expect(formatPercentage(5.25)).toBe('+5.25%')
    expect(formatPercentage(100)).toBe('+100.00%')
    expect(formatPercentage(0.5)).toBe('+0.50%')
  })

  it('should format negative percentages with - sign', () => {
    expect(formatPercentage(-5.25)).toBe('-5.25%')
    expect(formatPercentage(-100)).toBe('-100.00%')
  })

  it('should format zero without sign', () => {
    expect(formatPercentage(0)).toBe('0.00%')
  })

  it('should respect showSign parameter', () => {
    expect(formatPercentage(5.25, 2, false)).toBe('5.25%')
    expect(formatPercentage(-5.25, 2, false)).toBe('-5.25%')
    expect(formatPercentage(0, 2, false)).toBe('0.00%')
  })

  it('should handle custom decimal places', () => {
    expect(formatPercentage(5.12345, 4)).toBe('+5.1235%')
    expect(formatPercentage(5.12345, 0)).toBe('+5%')
  })

  it('should handle null and undefined values', () => {
    expect(formatPercentage(null)).toBe('0.00%')
    expect(formatPercentage(undefined)).toBe('0.00%')
    expect(formatPercentage(NaN)).toBe('0.00%')
  })
})

describe('formatNumber', () => {
  it('should format numbers with commas', () => {
    expect(formatNumber(1234.56)).toBe('1,234.56')
    expect(formatNumber(1234567.89)).toBe('1,234,567.89')
    expect(formatNumber(1000000)).toBe('1,000,000.00')
  })

  it('should format numbers with specified decimal places', () => {
    expect(formatNumber(1234.5678, 4)).toBe('1,234.5678')
    expect(formatNumber(1234.5678, 0)).toBe('1,235')
  })

  it('should handle small numbers', () => {
    expect(formatNumber(0.5)).toBe('0.50')
    expect(formatNumber(0.001)).toBe('0.00')
  })

  it('should handle null and undefined values', () => {
    expect(formatNumber(null)).toBe('0.00')
    expect(formatNumber(undefined)).toBe('0.00')
    expect(formatNumber(NaN)).toBe('0.00')
  })
})

describe('formatPnLChange', () => {
  it('should format positive P&L change correctly', () => {
    const result = formatPnLChange(123.45, 5.25)
    expect(result).toContain('+$ 123.45')
    expect(result).toContain('(+5.25%)')
  })

  it('should format negative P&L change correctly', () => {
    const result = formatPnLChange(-123.45, -5.25)
    expect(result).toContain('-$ 123.45')
    expect(result).toContain('(-5.25%)')
  })

  it('should handle zero change', () => {
    const result = formatPnLChange(0, 0)
    expect(result).toContain('$ 0.00')
    expect(result).toContain('(0.00%)')
  })

  it('should handle different currencies', () => {
    const result = formatPnLChange(100, 5, 'EUR')
    expect(result).toContain('€ 100.00')
  })

  it('should handle null amount', () => {
    const result = formatPnLChange(null, 5)
    expect(result).toContain('$ 0.00')
    expect(result).toContain('(0.00%)')
  })

  it('should handle null percent', () => {
    const result = formatPnLChange(100, null)
    expect(result).toContain('+$ 100.00')
    expect(result).toContain('(0.00%)')
  })
})

describe('formatDateTime', () => {
  it('should format ISO date string with time', () => {
    const result = formatDateTime('2024-01-15T10:30:00Z')
    expect(result).toMatch(/Jan 15, 2024/)
    // Time format varies by locale, just check it includes a time
    expect(result).toMatch(/\d{1,2}:\d{2}/)
  })

  it('should format date without time when showTime is false', () => {
    const result = formatDateTime('2024-01-15T10:30:00Z', false)
    expect(result).toMatch(/Jan 15, 2024/)
    expect(result).not.toMatch(/10:30/)
  })

  it('should handle null and undefined', () => {
    expect(formatDateTime(null)).toBe('Never')
    expect(formatDateTime(undefined)).toBe('Never')
  })

  it('should handle invalid date strings', () => {
    expect(formatDateTime('invalid-date')).toBe('Invalid Date')
  })
})

describe('formatTimeAgo', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2024-01-15T12:00:00Z'))
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('should return "Just now" for very recent times', () => {
    const thirtySecondsAgo = new Date('2024-01-15T11:59:30Z').toISOString()
    expect(formatTimeAgo(thirtySecondsAgo)).toBe('Just now')
  })

  it('should format minutes ago correctly', () => {
    const fiveMinutesAgo = new Date('2024-01-15T11:55:00Z').toISOString()
    expect(formatTimeAgo(fiveMinutesAgo)).toBe('5 minutes ago')

    const oneMinuteAgo = new Date('2024-01-15T11:59:00Z').toISOString()
    expect(formatTimeAgo(oneMinuteAgo)).toBe('1 minute ago')
  })

  it('should format hours ago correctly', () => {
    const twoHoursAgo = new Date('2024-01-15T10:00:00Z').toISOString()
    expect(formatTimeAgo(twoHoursAgo)).toBe('2 hours ago')

    const oneHourAgo = new Date('2024-01-15T11:00:00Z').toISOString()
    expect(formatTimeAgo(oneHourAgo)).toBe('1 hour ago')
  })

  it('should format days ago correctly', () => {
    const threeDaysAgo = new Date('2024-01-12T12:00:00Z').toISOString()
    expect(formatTimeAgo(threeDaysAgo)).toBe('3 days ago')

    const oneDayAgo = new Date('2024-01-14T12:00:00Z').toISOString()
    expect(formatTimeAgo(oneDayAgo)).toBe('1 day ago')
  })

  it('should format months ago correctly', () => {
    const twoMonthsAgo = new Date('2023-11-15T12:00:00Z').toISOString()
    expect(formatTimeAgo(twoMonthsAgo)).toBe('2 months ago')

    const oneMonthAgo = new Date('2023-12-15T12:00:00Z').toISOString()
    expect(formatTimeAgo(oneMonthAgo)).toBe('1 month ago')
  })

  it('should handle null and undefined', () => {
    expect(formatTimeAgo(null)).toBe('Never')
    expect(formatTimeAgo(undefined)).toBe('Never')
  })

  it('should handle invalid dates', () => {
    const result = formatTimeAgo('invalid-date')
    // Invalid dates might return 'Unknown' or 'NaN months ago' depending on implementation
    expect(result).toMatch(/Unknown|NaN/)
  })
})

describe('getPnLClassName', () => {
  it('should return "profit" for positive values', () => {
    expect(getPnLClassName(100)).toBe('profit')
    expect(getPnLClassName(0.01)).toBe('profit')
  })

  it('should return "loss" for negative values', () => {
    expect(getPnLClassName(-100)).toBe('loss')
    expect(getPnLClassName(-0.01)).toBe('loss')
  })

  it('should return "neutral" for zero', () => {
    expect(getPnLClassName(0)).toBe('neutral')
  })

  it('should return "neutral" for null and undefined', () => {
    expect(getPnLClassName(null)).toBe('neutral')
    expect(getPnLClassName(undefined)).toBe('neutral')
    expect(getPnLClassName(NaN)).toBe('neutral')
  })
})
