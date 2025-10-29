// ABOUTME: Display AI-powered price forecasts with scenario visualization
// ABOUTME: Shows two-quarter forecasts with pessimistic/realistic/optimistic scenarios

import { useState, useEffect } from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { RefreshCw, ChevronDown, ChevronUp } from 'lucide-react'
import { getForecast } from '../api/analysis'
import type { ForecastResponse, ForecastScenario } from '../api/analysis'
import './ForecastPanel.css'

interface ForecastPanelProps {
  symbol: string
}

const SCENARIO_COLORS = {
  Pessimistic: '#dc2626',
  Realistic: '#3b82f6',
  Optimistic: '#059669',
}

export const ForecastPanel: React.FC<ForecastPanelProps> = ({ symbol }) => {
  const [forecast, setForecast] = useState<ForecastResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [refreshing, setRefreshing] = useState(false)
  const [quarter, setQuarter] = useState<'q1' | 'q2'>('q1')

  useEffect(() => {
    loadForecast()
  }, [symbol])

  const loadForecast = async (forceRefresh = false) => {
    if (forceRefresh) {
      setRefreshing(true)
    } else {
      setLoading(true)
    }
    setError(null)

    try {
      const result = await getForecast(symbol, forceRefresh)
      setForecast(result)
    } catch (err: any) {
      console.error(`Failed to load forecast for ${symbol}:`, err)
      setError(err.response?.data?.detail || 'Failed to load forecast. Please try again.')
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  const handleRefresh = () => {
    loadForecast(true)
  }

  if (loading) {
    return (
      <div className="forecast-panel loading">
        <div className="loading-content">
          <div className="spinner"></div>
          <p>Generating forecast for {symbol}...</p>
          <span className="loading-hint">Analyzing historical data and market trends</span>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="forecast-panel error">
        <div className="error-content">
          <h3>Unable to Load Forecast</h3>
          <p>{error}</p>
          <button onClick={() => loadForecast()} className="retry-button">
            Retry
          </button>
        </div>
      </div>
    )
  }

  if (!forecast) {
    return null
  }

  const quarterData = forecast[`${quarter}_forecast`]

  // Prepare chart data
  const chartData = [
    {
      name: 'Pessimistic',
      price: quarterData.pessimistic.price,
    },
    {
      name: 'Realistic',
      price: quarterData.realistic.price,
    },
    {
      name: 'Optimistic',
      price: quarterData.optimistic.price,
    },
  ]

  return (
    <div className="forecast-panel">
      <div className="panel-header">
        <div className="header-left">
          <h3>Forecast: {symbol}</h3>
          {forecast.cached && (
            <span className="cache-badge" title="Forecast loaded from cache">
              Cached
            </span>
          )}
        </div>
        <div className="header-right">
          <div className="quarter-toggle">
            <button
              className={quarter === 'q1' ? 'active' : ''}
              onClick={() => setQuarter('q1')}
            >
              Q1 (3 months)
            </button>
            <button
              className={quarter === 'q2' ? 'active' : ''}
              onClick={() => setQuarter('q2')}
            >
              Q2 (6 months)
            </button>
          </div>
          <button
            onClick={handleRefresh}
            className={`refresh-btn ${refreshing ? 'refreshing' : ''}`}
            disabled={refreshing}
            title="Generate new forecast"
            aria-label="Refresh forecast"
          >
            <RefreshCw size={18} />
          </button>
        </div>
      </div>

      {/* Overall Outlook */}
      <div className="outlook-box">
        <h4>Overall Outlook</h4>
        <p>{forecast.overall_outlook}</p>
      </div>

      {/* Price Chart */}
      <div className="forecast-chart">
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData}>
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip
              formatter={(value: number) => `€${value.toFixed(2)}`}
              contentStyle={{
                background: 'white',
                border: '1px solid #e5e7eb',
                borderRadius: '6px',
              }}
            />
            <Bar dataKey="price" radius={[8, 8, 0, 0]}>
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={SCENARIO_COLORS[entry.name as keyof typeof SCENARIO_COLORS]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Scenario Cards */}
      <div className="scenarios">
        <ScenarioCard
          scenario="pessimistic"
          data={quarterData.pessimistic}
          color={SCENARIO_COLORS.Pessimistic}
        />
        <ScenarioCard
          scenario="realistic"
          data={quarterData.realistic}
          color={SCENARIO_COLORS.Realistic}
        />
        <ScenarioCard
          scenario="optimistic"
          data={quarterData.optimistic}
          color={SCENARIO_COLORS.Optimistic}
        />
      </div>

      {/* Footer */}
      <div className="panel-footer">
        <span className="timestamp">
          Generated {new Date(forecast.generated_at).toLocaleString('en-US', {
            month: 'short',
            day: 'numeric',
            hour: 'numeric',
            minute: '2-digit',
          })}
        </span>
        <span className="token-count">
          {forecast.tokens_used.toLocaleString()} tokens
        </span>
      </div>
    </div>
  )
}

interface ScenarioCardProps {
  scenario: string
  data: ForecastScenario
  color: string
}

const ScenarioCard: React.FC<ScenarioCardProps> = ({ scenario, data, color }) => {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className="scenario-card" style={{ borderLeftColor: color }}>
      <div
        className="scenario-header"
        onClick={() => setExpanded(!expanded)}
        role="button"
        tabIndex={0}
        onKeyPress={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault()
            setExpanded(!expanded)
          }
        }}
      >
        <div className="scenario-title">
          <h4>{scenario.charAt(0).toUpperCase() + scenario.slice(1)}</h4>
          <span className="scenario-confidence">{data.confidence}% confidence</span>
        </div>
        <div className="scenario-price" style={{ color }}>
          €{data.price.toFixed(2)}
        </div>
        {expanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
      </div>

      {expanded && (
        <div className="scenario-details">
          <div className="detail-section">
            <h5>Assumptions</h5>
            <p>{data.assumptions}</p>
          </div>
          <div className="detail-section">
            <h5>Risks</h5>
            <p>{data.risks}</p>
          </div>
        </div>
      )}
    </div>
  )
}

export default ForecastPanel
