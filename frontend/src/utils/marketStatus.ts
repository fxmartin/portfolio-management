// ABOUTME: Market status utility for determining trading hours and market open/closed status
// ABOUTME: Handles timezone conversion to US Eastern Time for accurate market hours calculations

export type MarketSession = 'open' | 'pre-market' | 'after-hours' | 'closed' | '24/7'

export interface MarketStatus {
  isOpen: boolean
  session: MarketSession
  statusText: string
  nextEvent: {
    type: 'open' | 'close'
    time: Date
    label: string // e.g., "2h 15m", "9:30 AM"
  } | null
}

/**
 * Get the current time in US Eastern Time
 */
function getEasternTime(): Date {
  // Get current UTC time
  const now = new Date()

  // Format as Eastern Time string and parse back
  const formatter = new Intl.DateTimeFormat('en-US', {
    timeZone: 'America/New_York',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  })

  const parts = formatter.formatToParts(now)
  const values: Record<string, string> = {}
  parts.forEach(part => {
    if (part.type !== 'literal') {
      values[part.type] = part.value
    }
  })

  return new Date(
    parseInt(values.year),
    parseInt(values.month) - 1,
    parseInt(values.day),
    parseInt(values.hour),
    parseInt(values.minute),
    parseInt(values.second)
  )
}

/**
 * Check if the given Eastern Time date is a trading day (Mon-Fri)
 */
function isTradingDay(etDate: Date): boolean {
  const day = etDate.getDay()
  return day >= 1 && day <= 5 // Monday = 1, Friday = 5
}

/**
 * Get time in format "Xh Ym" or "Xm" for countdown display
 */
function formatCountdown(milliseconds: number): string {
  const totalMinutes = Math.floor(milliseconds / (1000 * 60))
  const hours = Math.floor(totalMinutes / 60)
  const minutes = totalMinutes % 60

  if (hours > 0) {
    return minutes > 0 ? `${hours}h ${minutes}m` : `${hours}h`
  }
  return `${minutes}m`
}

/**
 * Get time in format "H:MM AM/PM" for absolute time display
 */
function formatTime(date: Date): string {
  const hours = date.getHours()
  const minutes = date.getMinutes()
  const ampm = hours >= 12 ? 'PM' : 'AM'
  const displayHours = hours % 12 || 12
  const displayMinutes = minutes.toString().padStart(2, '0')

  return `${displayHours}:${displayMinutes} ${ampm}`
}

/**
 * Get market status for stocks (NYSE/NASDAQ)
 */
export function getStockMarketStatus(): MarketStatus {
  const et = getEasternTime()

  // Check if it's a trading day
  if (!isTradingDay(et)) {
    // Find next Monday (or today if it's Friday after close)
    const nextOpen = new Date(et)
    const daysUntilMonday = (8 - et.getDay()) % 7 || 7
    nextOpen.setDate(et.getDate() + daysUntilMonday)
    nextOpen.setHours(9, 30, 0, 0)

    return {
      isOpen: false,
      session: 'closed',
      statusText: 'Closed (weekend)',
      nextEvent: {
        type: 'open',
        time: nextOpen,
        label: `Mon ${formatTime(nextOpen)}`,
      },
    }
  }

  const hours = et.getHours()
  const minutes = et.getMinutes()
  const timeInMinutes = hours * 60 + minutes

  // Market hours in minutes since midnight
  const preMarketStart = 4 * 60 // 4:00 AM
  const regularOpen = 9 * 60 + 30 // 9:30 AM
  const regularClose = 16 * 60 // 4:00 PM
  const afterHoursEnd = 20 * 60 // 8:00 PM

  // Pre-market (4:00 AM - 9:30 AM)
  if (timeInMinutes >= preMarketStart && timeInMinutes < regularOpen) {
    const minutesUntilOpen = regularOpen - timeInMinutes
    const openTime = new Date(et)
    openTime.setHours(9, 30, 0, 0)

    return {
      isOpen: false,
      session: 'pre-market',
      statusText: `Pre-market • Regular at ${formatTime(openTime)}`,
      nextEvent: {
        type: 'open',
        time: openTime,
        label: formatCountdown(minutesUntilOpen * 60 * 1000),
      },
    }
  }

  // Regular hours (9:30 AM - 4:00 PM)
  if (timeInMinutes >= regularOpen && timeInMinutes < regularClose) {
    const minutesUntilClose = regularClose - timeInMinutes
    const closeTime = new Date(et)
    closeTime.setHours(16, 0, 0, 0)

    return {
      isOpen: true,
      session: 'open',
      statusText: `Open until ${formatTime(closeTime)}`,
      nextEvent: {
        type: 'close',
        time: closeTime,
        label: formatCountdown(minutesUntilClose * 60 * 1000),
      },
    }
  }

  // After-hours (4:00 PM - 8:00 PM)
  if (timeInMinutes >= regularClose && timeInMinutes < afterHoursEnd) {
    const nextOpen = new Date(et)
    nextOpen.setDate(et.getDate() + 1)
    nextOpen.setHours(9, 30, 0, 0)

    // Check if tomorrow is a trading day
    if (!isTradingDay(nextOpen)) {
      // Skip to Monday
      const daysUntilMonday = (8 - nextOpen.getDay()) % 7 || 7
      nextOpen.setDate(nextOpen.getDate() + daysUntilMonday)
    }

    return {
      isOpen: false,
      session: 'after-hours',
      statusText: `After-hours • Opens ${formatTime(nextOpen)}`,
      nextEvent: {
        type: 'open',
        time: nextOpen,
        label: `Mon ${formatTime(nextOpen)}`,
      },
    }
  }

  // Closed (before 4:00 AM or after 8:00 PM)
  const nextOpen = new Date(et)
  if (timeInMinutes < preMarketStart) {
    // Later today
    nextOpen.setHours(9, 30, 0, 0)
  } else {
    // Tomorrow
    nextOpen.setDate(et.getDate() + 1)
    nextOpen.setHours(9, 30, 0, 0)

    // Check if tomorrow is a trading day
    if (!isTradingDay(nextOpen)) {
      const daysUntilMonday = (8 - nextOpen.getDay()) % 7 || 7
      nextOpen.setDate(nextOpen.getDate() + daysUntilMonday)
    }
  }

  const msUntilOpen = nextOpen.getTime() - et.getTime()

  return {
    isOpen: false,
    session: 'closed',
    statusText: `Closed (opens in ${formatCountdown(msUntilOpen)})`,
    nextEvent: {
      type: 'open',
      time: nextOpen,
      label: formatCountdown(msUntilOpen),
    },
  }
}

/**
 * Get market status for crypto (always open)
 */
export function getCryptoMarketStatus(): MarketStatus {
  return {
    isOpen: true,
    session: '24/7',
    statusText: '24/7',
    nextEvent: null,
  }
}

/**
 * Get market status for metals (simplified - same as stocks for now)
 * Note: COMEX has different hours, but we'll use stock market hours for simplicity
 */
export function getMetalMarketStatus(): MarketStatus {
  // For now, use the same logic as stocks
  // In the future, this can be enhanced to handle COMEX-specific hours
  const stockStatus = getStockMarketStatus()

  return {
    ...stockStatus,
    statusText: stockStatus.statusText.replace('Pre-market', 'Pre-trading').replace('After-hours', 'After-trading'),
  }
}

/**
 * Get market status for a specific asset type
 */
export function getMarketStatus(assetType: 'stocks' | 'crypto' | 'metals'): MarketStatus {
  switch (assetType) {
    case 'stocks':
      return getStockMarketStatus()
    case 'crypto':
      return getCryptoMarketStatus()
    case 'metals':
      return getMetalMarketStatus()
    default:
      return getCryptoMarketStatus() // Fallback to 24/7
  }
}

/**
 * Get status indicator emoji based on market session
 */
export function getStatusIndicator(session: MarketSession): string {
  switch (session) {
    case 'open':
      return '🟢'
    case 'pre-market':
    case 'after-hours':
      return '🟡'
    case 'closed':
      return '🔴'
    case '24/7':
      return '🔵'
    default:
      return '⚪'
  }
}
