// ABOUTME: Allocation comparison chart showing current vs target allocation
// ABOUTME: Visual bar chart using Recharts to display rebalancing needs

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts'
import type { RebalancingAnalysis } from '../api/rebalancing'
import './AllocationComparisonChart.css'

interface AllocationComparisonChartProps {
  analysis: RebalancingAnalysis
}

const AllocationComparisonChart: React.FC<AllocationComparisonChartProps> = ({ analysis }) => {
  // Prepare data for chart
  const chartData = analysis.current_allocation.map(alloc => ({
    name: alloc.asset_type,
    current: parseFloat(Number(alloc.current_percentage).toFixed(1)),
    target: parseFloat(Number(alloc.target_percentage).toFixed(1)),
    deviation: parseFloat(Number(alloc.deviation).toFixed(1)),
    status: alloc.status
  }))

  // Color mapping based on status
  const getBarColor = (status: string) => {
    switch (status) {
      case 'OVERWEIGHT':
        return '#ef4444' // Red
      case 'UNDERWEIGHT':
        return '#3b82f6' // Blue
      case 'SLIGHTLY_OVERWEIGHT':
        return '#f97316' // Orange
      case 'SLIGHTLY_UNDERWEIGHT':
        return '#06b6d4' // Cyan
      case 'BALANCED':
        return '#10b981' // Green
      default:
        return '#6b7280' // Gray
    }
  }

  // Format asset type names
  const formatAssetType = (type: string) => {
    switch (type) {
      case 'STOCK':
        return 'Stocks'
      case 'CRYPTO':
        return 'Crypto'
      case 'METAL':
        return 'Metals'
      default:
        return type
    }
  }

  return (
    <div className="allocation-comparison-chart">
      <h3>Current vs Target Allocation</h3>

      <ResponsiveContainer width="100%" height={300}>
        <BarChart
          data={chartData}
          margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="name"
            tickFormatter={formatAssetType}
            stroke="#6b7280"
          />
          <YAxis
            label={{ value: 'Percentage (%)', angle: -90, position: 'insideLeft' }}
            stroke="#6b7280"
          />
          <Tooltip
            formatter={(value: number) => `${value}%`}
            labelFormatter={formatAssetType}
            contentStyle={{
              backgroundColor: '#fff',
              border: '1px solid #e5e7eb',
              borderRadius: '8px'
            }}
          />
          <Legend />
          <Bar
            dataKey="current"
            name="Current"
            radius={[8, 8, 0, 0]}
          >
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={getBarColor(entry.status)} />
            ))}
          </Bar>
          <Bar
            dataKey="target"
            name="Target"
            fill="#9ca3af"
            radius={[8, 8, 0, 0]}
          />
        </BarChart>
      </ResponsiveContainer>

      {/* Legend Explanation */}
      <div className="chart-legend">
        <div className="legend-item">
          <span className="legend-dot overweight"></span>
          <span>Overweight (reduce)</span>
        </div>
        <div className="legend-item">
          <span className="legend-dot underweight"></span>
          <span>Underweight (increase)</span>
        </div>
        <div className="legend-item">
          <span className="legend-dot balanced"></span>
          <span>Balanced</span>
        </div>
      </div>

      {/* Deviation Summary */}
      <div className="deviation-summary">
        {chartData.map(item => (
          <div key={item.name} className="deviation-item">
            <span className="asset-name">{formatAssetType(item.name)}</span>
            <span className={`deviation-value ${item.deviation > 0 ? 'positive' : item.deviation < 0 ? 'negative' : 'neutral'}`}>
              {item.deviation > 0 ? '+' : ''}{item.deviation}%
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

export default AllocationComparisonChart
