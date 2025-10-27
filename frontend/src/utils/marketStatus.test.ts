// ABOUTME: Unit tests for market status utility
// ABOUTME: Tests trading hours detection, timezone handling, and status calculations

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import {
  getStockMarketStatus,
  getCryptoMarketStatus,
  getMetalMarketStatus,
  getMarketStatus,
  getStatusIndicator,
  type MarketSession,
} from './marketStatus'

describe('marketStatus', () => {
  // Store original Date
  const RealDate = Date

  // Helper to mock Eastern Time
  const mockEasternTime = (
    year: number,
    month: number, // 0-indexed (0 = January)
    date: number,
    hours: number,
    minutes: number = 0
  ) => {
    // Create a mock date representing ET
    const mockDate = new RealDate(year, month, date, hours, minutes, 0, 0)

    // Set system time to our mock date
    vi.setSystemTime(mockDate)

    // Mock Intl.DateTimeFormat to treat mockDate as if it's in ET
    const formatToPartsSpy = vi.fn(() => {
      return [
        { type: 'year', value: mockDate.getFullYear().toString() },
        { type: 'literal', value: '/' },
        { type: 'month', value: (mockDate.getMonth() + 1).toString().padStart(2, '0') },
        { type: 'literal', value: '/' },
        { type: 'day', value: mockDate.getDate().toString().padStart(2, '0') },
        { type: 'literal', value: ', ' },
        { type: 'hour', value: mockDate.getHours().toString().padStart(2, '0') },
        { type: 'literal', value: ':' },
        { type: 'minute', value: mockDate.getMinutes().toString().padStart(2, '0') },
        { type: 'literal', value: ':' },
        { type: 'second', value: mockDate.getSeconds().toString().padStart(2, '0') },
      ]
    })

    vi.spyOn(Intl, 'DateTimeFormat').mockImplementation(() => {
      return {
        formatToParts: formatToPartsSpy,
      } as any
    })
  }

  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.restoreAllMocks()
    vi.useRealTimers()
  })

  describe('getStockMarketStatus', () => {
    it('should return open status during regular trading hours (10:00 AM)', () => {
      // Wednesday, 10:00 AM ET
      mockEasternTime(2025, 0, 29, 10, 0)

      const status = getStockMarketStatus()

      expect(status.isOpen).toBe(true)
      expect(status.session).toBe('open')
      expect(status.statusText).toContain('Open until')
      expect(status.nextEvent?.type).toBe('close')
    })

    it('should return open status at market open (9:30 AM)', () => {
      // Wednesday, 9:30 AM ET
      mockEasternTime(2025, 0, 29, 9, 30)

      const status = getStockMarketStatus()

      expect(status.isOpen).toBe(true)
      expect(status.session).toBe('open')
    })

    it('should return closed status right before market close (3:59 PM)', () => {
      // Wednesday, 3:59 PM ET
      mockEasternTime(2025, 0, 29, 15, 59)

      const status = getStockMarketStatus()

      expect(status.isOpen).toBe(true)
      expect(status.session).toBe('open')
    })

    it('should return pre-market status (7:00 AM)', () => {
      // Wednesday, 7:00 AM ET
      mockEasternTime(2025, 0, 29, 7, 0)

      const status = getStockMarketStatus()

      expect(status.isOpen).toBe(false)
      expect(status.session).toBe('pre-market')
      expect(status.statusText).toContain('Pre-market')
      expect(status.nextEvent?.type).toBe('open')
    })

    it('should return after-hours status (5:00 PM)', () => {
      // Wednesday, 5:00 PM ET
      mockEasternTime(2025, 0, 29, 17, 0)

      const status = getStockMarketStatus()

      expect(status.isOpen).toBe(false)
      expect(status.session).toBe('after-hours')
      expect(status.statusText).toContain('After-hours')
    })

    it('should return closed status early morning (2:00 AM)', () => {
      // Wednesday, 2:00 AM ET
      mockEasternTime(2025, 0, 29, 2, 0)

      const status = getStockMarketStatus()

      expect(status.isOpen).toBe(false)
      expect(status.session).toBe('closed')
      expect(status.statusText).toContain('Closed')
    })

    it('should return closed status late night (10:00 PM)', () => {
      // Wednesday, 10:00 PM ET
      mockEasternTime(2025, 0, 29, 22, 0)

      const status = getStockMarketStatus()

      expect(status.isOpen).toBe(false)
      expect(status.session).toBe('closed')
    })

    it('should return closed status on Saturday', () => {
      // Saturday, 10:00 AM ET
      mockEasternTime(2025, 1, 1, 10, 0)

      const status = getStockMarketStatus()

      expect(status.isOpen).toBe(false)
      expect(status.session).toBe('closed')
      expect(status.statusText).toContain('weekend')
      expect(status.nextEvent?.type).toBe('open')
      expect(status.nextEvent?.label).toContain('Mon')
    })

    it('should return closed status on Sunday', () => {
      // Sunday, 2:00 PM ET
      mockEasternTime(2025, 1, 2, 14, 0)

      const status = getStockMarketStatus()

      expect(status.isOpen).toBe(false)
      expect(status.session).toBe('closed')
      expect(status.statusText).toContain('weekend')
    })

    it('should calculate time until next open correctly', () => {
      // Wednesday, 8:00 AM ET (1.5 hours until 9:30 AM open)
      mockEasternTime(2025, 0, 29, 8, 0)

      const status = getStockMarketStatus()

      expect(status.nextEvent?.type).toBe('open')
      expect(status.nextEvent?.label).toContain('1h 30m')
    })

    it('should calculate time until close correctly', () => {
      // Wednesday, 3:00 PM ET (1 hour until 4:00 PM close)
      mockEasternTime(2025, 0, 29, 15, 0)

      const status = getStockMarketStatus()

      expect(status.isOpen).toBe(true)
      expect(status.nextEvent?.type).toBe('close')
      expect(status.nextEvent?.label).toContain('1h')
    })
  })

  describe('getCryptoMarketStatus', () => {
    it('should always return 24/7 status', () => {
      const status = getCryptoMarketStatus()

      expect(status.isOpen).toBe(true)
      expect(status.session).toBe('24/7')
      expect(status.statusText).toBe('24/7')
      expect(status.nextEvent).toBeNull()
    })
  })

  describe('getMetalMarketStatus', () => {
    it('should return similar status to stocks during trading hours', () => {
      // Wednesday, 10:00 AM ET
      mockEasternTime(2025, 0, 29, 10, 0)

      const status = getMetalMarketStatus()

      expect(status.isOpen).toBe(true)
      expect(status.session).toBe('open')
    })

    it('should return closed status on weekend', () => {
      // Saturday, 10:00 AM ET
      mockEasternTime(2025, 1, 1, 10, 0)

      const status = getMetalMarketStatus()

      expect(status.isOpen).toBe(false)
      expect(status.session).toBe('closed')
    })
  })

  describe('getMarketStatus', () => {
    it('should return stock status for stocks asset type', () => {
      mockEasternTime(2025, 0, 29, 10, 0) // Wednesday, 10:00 AM

      const status = getMarketStatus('stocks')

      expect(status.isOpen).toBe(true)
      expect(status.session).toBe('open')
    })

    it('should return crypto status for crypto asset type', () => {
      const status = getMarketStatus('crypto')

      expect(status.isOpen).toBe(true)
      expect(status.session).toBe('24/7')
    })

    it('should return metal status for metals asset type', () => {
      mockEasternTime(2025, 0, 29, 10, 0) // Wednesday, 10:00 AM

      const status = getMarketStatus('metals')

      expect(status.isOpen).toBe(true)
      expect(status.session).toBe('open')
    })
  })

  describe('getStatusIndicator', () => {
    it('should return green indicator for open session', () => {
      expect(getStatusIndicator('open')).toBe('🟢')
    })

    it('should return yellow indicator for pre-market', () => {
      expect(getStatusIndicator('pre-market')).toBe('🟡')
    })

    it('should return yellow indicator for after-hours', () => {
      expect(getStatusIndicator('after-hours')).toBe('🟡')
    })

    it('should return red indicator for closed', () => {
      expect(getStatusIndicator('closed')).toBe('🔴')
    })

    it('should return blue indicator for 24/7', () => {
      expect(getStatusIndicator('24/7')).toBe('🔵')
    })
  })

  describe('edge cases', () => {
    it('should handle Friday after-hours correctly (next open is Monday)', () => {
      // Friday, 5:00 PM ET
      mockEasternTime(2025, 0, 31, 17, 0)

      const status = getStockMarketStatus()

      expect(status.isOpen).toBe(false)
      expect(status.session).toBe('after-hours')
      expect(status.nextEvent?.label).toContain('Mon')
    })

    it('should handle Monday pre-market correctly', () => {
      // Monday, 7:00 AM ET
      mockEasternTime(2025, 1, 3, 7, 0)

      const status = getStockMarketStatus()

      expect(status.isOpen).toBe(false)
      expect(status.session).toBe('pre-market')
      expect(status.nextEvent?.type).toBe('open')
    })

    it('should handle exact market open time (9:30 AM)', () => {
      // Wednesday, 9:30:00 AM ET
      mockEasternTime(2025, 0, 29, 9, 30)

      const status = getStockMarketStatus()

      expect(status.isOpen).toBe(true)
      expect(status.session).toBe('open')
    })

    it('should handle exact market close time (4:00 PM)', () => {
      // Wednesday, 4:00:00 PM ET
      mockEasternTime(2025, 0, 29, 16, 0)

      const status = getStockMarketStatus()

      expect(status.isOpen).toBe(false)
      expect(status.session).toBe('after-hours')
    })
  })
})
