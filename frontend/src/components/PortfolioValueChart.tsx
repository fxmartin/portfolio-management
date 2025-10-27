// ABOUTME: Line chart component showing portfolio value over time
// ABOUTME: Displays historical portfolio performance with time period selection

import { useState, useEffect } from 'react'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts'
import './PortfolioValueChart.css'

interface ChartDataPoint {
  date: string
  value: number
}

interface PortfolioHistoryData {
  data: ChartDataPoint[]
  period: string
  initial_value: number
  current_value: number
  change: number
  change_percent: number
}

interface PortfolioValueChartProps {
  currency?: string
}

type TimePeriod = '1D' | '1W' | '1M' | '3M' | '1Y' | 'All'

const TIME_RANGES: { label: string; value: TimePeriod }[] = [
  { label: '1D', value: '1D' },
  { label: '1W', value: '1W' },
  { label: '1M', value: '1M' },
  { label: '3M', value: '3M' },
  { label: '1Y', value: '1Y' },
  { label: 'All', value: 'All' },
]

export default function PortfolioValueChart({ currency = 'EUR' }: PortfolioValueChartProps) {
  const [period, setPeriod] = useState<TimePeriod>('1M')
  const [chartData, setChartData] = useState<PortfolioHistoryData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchHistoricalData = async () => {
      setLoading(true)
      setError(null)

      try {
        const response = await fetch(`/api/portfolio/history?period=${period}`)

        if (!response.ok) {
          throw new Error('Failed to fetch portfolio history')
        }

        const data = await response.json()
        setChartData(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error')
        console.error('Error fetching portfolio history:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchHistoricalData()
  }, [period])

  // Format date for display
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)

    if (period === '1D') {
      // Show hours for 1D view
      return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
    } else if (period === '1W') {
      // Show day and time for 1W
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
    } else {
      // Show date for longer periods
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
    }
  }

  // Format currency value
  const formatCurrency = (value: number) => {
    const currencySymbol = currency === 'EUR' ? '€' : '$'
    return `${currencySymbol}${value.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`
  }

  // Custom tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0]
      const date = new Date(data.payload.date)

      return (
        <div className="chart-tooltip">
          <p className="tooltip-label">
            {date.toLocaleDateString('en-US', {
              year: 'numeric',
              month: 'short',
              day: 'numeric',
              hour: period === '1D' ? '2-digit' : undefined,
              minute: period === '1D' ? '2-digit' : undefined,
            })}
          </p>
          <p className="tooltip-value">{formatCurrency(data.value)}</p>
        </div>
      )
    }
    return null
  }

  if (loading) {
    return (
      <div className="portfolio-value-chart loading">
        <div className="chart-header">
          <h3>Portfolio Performance</h3>
        </div>
        <div className="loading-message">Loading chart data...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="portfolio-value-chart error">
        <div className="chart-header">
          <h3>Portfolio Performance</h3>
        </div>
        <div className="error-message">Error: {error}</div>
      </div>
    )
  }

  if (!chartData || chartData.data.length === 0) {
    return (
      <div className="portfolio-value-chart empty">
        <div className="chart-header">
          <h3>Portfolio Performance</h3>
        </div>
        <div className="empty-message">No data available for the selected period</div>
      </div>
    )
  }

  const isPositiveChange = chartData.change >= 0

  return (
    <div className="portfolio-value-chart">
      <div className="chart-header">
        <div className="chart-title-section">
          <h3>Portfolio Performance</h3>
          <div className="chart-metrics">
            <span className="current-value">{formatCurrency(chartData.current_value)}</span>
            <span className={`change ${isPositiveChange ? 'positive' : 'negative'}`}>
              {isPositiveChange ? '+' : ''}
              {formatCurrency(chartData.change)} ({chartData.change_percent.toFixed(2)}%)
            </span>
          </div>
        </div>
        <div className="time-range-selector">
          {TIME_RANGES.map((range) => (
            <button
              key={range.value}
              className={`time-range-button ${period === range.value ? 'active' : ''}`}
              onClick={() => setPeriod(range.value)}
            >
              {range.label}
            </button>
          ))}
        </div>
      </div>

      <div className="chart-container">
        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={chartData.data} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
            <XAxis
              dataKey="date"
              tickFormatter={formatDate}
              stroke="#6b7280"
              style={{ fontSize: '12px' }}
              tick={{ fill: '#6b7280' }}
            />
            <YAxis
              tickFormatter={(value) => formatCurrency(value)}
              stroke="#6b7280"
              style={{ fontSize: '12px' }}
              tick={{ fill: '#6b7280' }}
              domain={['dataMin - 1000', 'dataMax + 1000']}
            />
            <Tooltip content={<CustomTooltip />} />
            <ReferenceLine
              y={chartData.initial_value}
              stroke="#9ca3af"
              strokeDasharray="3 3"
              label={{ value: 'Start', position: 'right', fill: '#6b7280', fontSize: 12 }}
            />
            <Line
              type="monotone"
              dataKey="value"
              stroke={isPositiveChange ? '#10b981' : '#ef4444'}
              strokeWidth={2}
              dot={false}
              animationDuration={300}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
