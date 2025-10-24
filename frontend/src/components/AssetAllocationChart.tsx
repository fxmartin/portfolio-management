// ABOUTME: Pie chart component showing portfolio asset allocation by type
// ABOUTME: Displays percentage breakdown with interactive tooltips

import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts'
import './AssetAllocationChart.css'

interface AssetTypeMetrics {
  value: number
  pnl: number
  pnl_percent: number
}

interface AssetAllocationData {
  stocks: AssetTypeMetrics
  crypto: AssetTypeMetrics
  metals: AssetTypeMetrics
}

interface AssetAllocationChartProps {
  breakdown: AssetAllocationData
  totalValue: number
  currency?: string
}

interface ChartDataItem {
  name: string
  value: number
  percentage: number
  color: string
}

// Color scheme matching design specifications
const COLORS = {
  stocks: '#3b82f6', // blue
  crypto: '#f59e0b', // amber
  metals: '#8b5cf6', // purple
}

const ASSET_LABELS = {
  stocks: 'Stocks',
  crypto: 'Crypto',
  metals: 'Metals',
}

export default function AssetAllocationChart({
  breakdown,
  totalValue,
  currency = 'EUR',
}: AssetAllocationChartProps) {
  // Prepare chart data - filter out zero values
  const chartData: ChartDataItem[] = []

  Object.entries(breakdown).forEach(([assetType, metrics]) => {
    if (metrics.value > 0) {
      const percentage = totalValue > 0 ? (metrics.value / totalValue) * 100 : 0
      chartData.push({
        name: ASSET_LABELS[assetType as keyof typeof ASSET_LABELS],
        value: metrics.value,
        percentage: percentage,
        color: COLORS[assetType as keyof typeof COLORS],
      })
    }
  })

  // Don't render if no data
  if (chartData.length === 0) {
    return null
  }

  // Custom tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload
      const currencySymbol = currency === 'EUR' ? '€' : '$'
      return (
        <div className="chart-tooltip">
          <p className="tooltip-label">{data.name}</p>
          <p className="tooltip-value">
            {currencySymbol} {data.value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </p>
          <p className="tooltip-percentage">{data.percentage.toFixed(2)}%</p>
        </div>
      )
    }
    return null
  }

  // Custom label showing percentage
  const renderCustomLabel = (entry: any) => {
    return `${entry.percentage.toFixed(1)}%`
  }

  return (
    <div className="asset-allocation-chart">
      <ResponsiveContainer width="100%" height={250}>
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={renderCustomLabel}
            outerRadius={80}
            fill="#8884d8"
            dataKey="value"
          >
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
          <Legend
            verticalAlign="bottom"
            height={36}
            formatter={(value, entry: any) => (
              <span style={{ color: '#374151', fontSize: '0.875rem' }}>
                {value}
              </span>
            )}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  )
}
