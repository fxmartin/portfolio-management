## Feature 8.6: Analysis UI Dashboard
**Feature Description**: Frontend components for displaying and interacting with AI analysis
**User Value**: Easy access to insights with beautiful, intuitive interface
**Priority**: High
**Complexity**: 8 story points

### Story F8.6-001: Analysis Dashboard Tab
**Status**: 🔴 Not Started
**User Story**: As FX, I want a dedicated Analysis tab so that I can easily access all AI insights

**Acceptance Criteria**:
- **Given** I navigate to the Analysis tab
- **When** the page loads
- **Then** I see global market analysis card
- **And** I see a list of my positions with analysis buttons
- **And** I can click any position to view detailed analysis
- **And** I can request forecast for any position
- **And** loading states are shown during generation
- **And** cached indicators show when analysis is from cache
- **And** I can force refresh any analysis

**Component Structure**:
```typescript
// frontend/src/pages/Analysis.tsx

import React from 'react';
import { GlobalAnalysisCard } from '../components/GlobalAnalysisCard';
import { PositionAnalysisList } from '../components/PositionAnalysisList';
import { ForecastPanel } from '../components/ForecastPanel';

export const AnalysisPage: React.FC = () => {
  const [selectedSymbol, setSelectedSymbol] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'analysis' | 'forecast'>('analysis');

  return (
    <div className="analysis-page">
      <header>
        <h1>Portfolio Analysis</h1>
        <p className="subtitle">AI-powered insights from Claude</p>
      </header>

      <div className="analysis-grid">
        {/* Global Analysis - Full Width */}
        <section className="global-section">
          <GlobalAnalysisCard />
        </section>

        {/* Position List - Left Side */}
        <section className="positions-section">
          <PositionAnalysisList
            onSelectPosition={setSelectedSymbol}
            selectedSymbol={selectedSymbol}
          />
        </section>

        {/* Detail Panel - Right Side */}
        <section className="detail-section">
          {selectedSymbol && (
            <div className="mode-tabs">
              <button
                className={viewMode === 'analysis' ? 'active' : ''}
                onClick={() => setViewMode('analysis')}
              >
                Analysis
              </button>
              <button
                className={viewMode === 'forecast' ? 'active' : ''}
                onClick={() => setViewMode('forecast')}
              >
                Forecast
              </button>
            </div>
          )}

          {selectedSymbol && viewMode === 'analysis' && (
            <PositionAnalysisCard symbol={selectedSymbol} />
          )}

          {selectedSymbol && viewMode === 'forecast' && (
            <ForecastPanel symbol={selectedSymbol} />
          )}

          {!selectedSymbol && (
            <div className="empty-state">
              <p>Select a position to view detailed analysis</p>
            </div>
          )}
        </section>
      </div>
    </div>
  );
};
```

**GlobalAnalysisCard Component**:
```typescript
// frontend/src/components/GlobalAnalysisCard.tsx

import React, { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { analysisApi } from '../api/analysis';

export const GlobalAnalysisCard: React.FC = () => {
  const [analysis, setAnalysis] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadAnalysis = async (forceRefresh = false) => {
    setLoading(true);
    setError(null);
    try {
      const result = await analysisApi.getGlobalAnalysis(forceRefresh);
      setAnalysis(result);
    } catch (err) {
      setError('Failed to load analysis');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAnalysis();
  }, []);

  if (loading) {
    return <div className="loading-card">Generating market analysis...</div>;
  }

  if (error) {
    return <div className="error-card">{error}</div>;
  }

  return (
    <div className="global-analysis-card">
      <div className="card-header">
        <h2>Market Overview</h2>
        <div className="card-actions">
          {analysis?.cached && (
            <span className="cache-badge">Cached</span>
          )}
          <span className="timestamp">
            {new Date(analysis.generated_at).toLocaleString()}
          </span>
          <button
            onClick={() => loadAnalysis(true)}
            className="refresh-btn"
            title="Generate new analysis"
          >
            Refresh
          </button>
        </div>
      </div>

      <div className="card-body">
        <ReactMarkdown>{analysis.analysis}</ReactMarkdown>
      </div>

      <div className="card-footer">
        <span className="token-count">
          {analysis.tokens_used} tokens
        </span>
      </div>
    </div>
  );
};
```

**PositionAnalysisList Component**:
```typescript
// frontend/src/components/PositionAnalysisList.tsx

interface PositionAnalysisListProps {
  onSelectPosition: (symbol: string) => void;
  selectedSymbol: string | null;
}

export const PositionAnalysisList: React.FC<PositionAnalysisListProps> = ({
  onSelectPosition,
  selectedSymbol
}) => {
  const [positions, setPositions] = useState<any[]>([]);

  useEffect(() => {
    // Fetch positions from portfolio API
    portfolioApi.getPositions().then(setPositions);
  }, []);

  return (
    <div className="position-list">
      <h3>Your Positions</h3>
      <div className="position-items">
        {positions.map(position => (
          <div
            key={position.symbol}
            className={`position-item ${selectedSymbol === position.symbol ? 'selected' : ''}`}
            onClick={() => onSelectPosition(position.symbol)}
          >
            <div className="position-symbol">{position.symbol}</div>
            <div className="position-value">
              €{position.current_value.toFixed(2)}
            </div>
            <div className={`position-pnl ${position.unrealized_pnl >= 0 ? 'positive' : 'negative'}`}>
              {position.unrealized_pnl >= 0 ? '+' : ''}
              {position.unrealized_pnl_percentage.toFixed(2)}%
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
```

**Definition of Done**:
- [x] Analysis page component
- [x] Global analysis card with markdown rendering
- [x] Position list component
- [x] Tab navigation (Analysis/Forecast)
- [x] Loading states
- [x] Error handling
- [x] Cache indicators
- [x] Refresh functionality
- [x] Responsive design
- [x] Unit tests (≥85% coverage)
- [x] Integration tests with mock API

**Story Points**: 5
**Priority**: Must Have
**Dependencies**: F8.3-001 (Global Analysis API)
**Risk Level**: Low
**Assigned To**: Unassigned

---

### Story F8.6-002: Forecast Visualization
**Status**: 🔴 Not Started
**User Story**: As FX, I want to visualize forecasts with charts so that I can easily understand the scenarios

**Acceptance Criteria**:
- **Given** I view a forecast
- **When** the forecast loads
- **Then** I see a chart showing current price and scenarios
- **And** pessimistic/realistic/optimistic scenarios are color-coded
- **And** confidence levels are displayed for each scenario
- **And** assumptions and risks are shown in expandable sections
- **And** I can toggle between Q1 and Q2 views
- **And** overall outlook is prominently displayed

**Forecast Panel Component**:
```typescript
// frontend/src/components/ForecastPanel.tsx

import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { analysisApi } from '../api/analysis';

interface ForecastPanelProps {
  symbol: string;
}

export const ForecastPanel: React.FC<ForecastPanelProps> = ({ symbol }) => {
  const [forecast, setForecast] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [quarter, setQuarter] = useState<'q1' | 'q2'>('q1');

  const loadForecast = async (forceRefresh = false) => {
    setLoading(true);
    try {
      const result = await analysisApi.getForecast(symbol, forceRefresh);
      setForecast(result);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadForecast();
  }, [symbol]);

  if (loading) {
    return <div className="loading">Generating forecast...</div>;
  }

  const quarterData = forecast[`${quarter}_forecast`];

  // Prepare chart data
  const chartData = [
    {
      name: 'Current',
      price: parseFloat(forecast.current_price),
      fill: '#888'
    },
    {
      name: 'Pessimistic',
      price: parseFloat(quarterData.pessimistic.price),
      confidence: quarterData.pessimistic.confidence,
      fill: '#ef4444'
    },
    {
      name: 'Realistic',
      price: parseFloat(quarterData.realistic.price),
      confidence: quarterData.realistic.confidence,
      fill: '#3b82f6'
    },
    {
      name: 'Optimistic',
      price: parseFloat(quarterData.optimistic.price),
      confidence: quarterData.optimistic.confidence,
      fill: '#22c55e'
    }
  ];

  return (
    <div className="forecast-panel">
      <div className="panel-header">
        <h3>Forecast for {symbol}</h3>
        <div className="quarter-toggle">
          <button
            className={quarter === 'q1' ? 'active' : ''}
            onClick={() => setQuarter('q1')}
          >
            Q1
          </button>
          <button
            className={quarter === 'q2' ? 'active' : ''}
            onClick={() => setQuarter('q2')}
          >
            Q2
          </button>
        </div>
      </div>

      <div className="outlook-box">
        <h4>Overall Outlook</h4>
        <p>{forecast.overall_outlook}</p>
      </div>

      <div className="forecast-chart">
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData}>
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="price" fill="#8884d8" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="scenarios">
        {['pessimistic', 'realistic', 'optimistic'].map(scenario => (
          <ScenarioCard
            key={scenario}
            scenario={scenario}
            data={quarterData[scenario]}
          />
        ))}
      </div>
    </div>
  );
};

const ScenarioCard: React.FC<{ scenario: string; data: any }> = ({ scenario, data }) => {
  const [expanded, setExpanded] = useState(false);

  const colors = {
    pessimistic: '#ef4444',
    realistic: '#3b82f6',
    optimistic: '#22c55e'
  };

  return (
    <div className="scenario-card" style={{ borderLeftColor: colors[scenario] }}>
      <div className="scenario-header" onClick={() => setExpanded(!expanded)}>
        <h4>{scenario.charAt(0).toUpperCase() + scenario.slice(1)}</h4>
        <div className="scenario-price">€{parseFloat(data.price).toFixed(2)}</div>
        <div className="scenario-confidence">{data.confidence}% confidence</div>
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
  );
};
```

**Styling**:
```css
/* frontend/src/components/ForecastPanel.css */

.forecast-panel {
  background: white;
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.quarter-toggle button {
  padding: 8px 16px;
  border: 1px solid #ddd;
  background: white;
  cursor: pointer;
}

.quarter-toggle button.active {
  background: #3b82f6;
  color: white;
}

.outlook-box {
  background: #f8fafc;
  padding: 16px;
  border-radius: 6px;
  margin-bottom: 20px;
}

.scenarios {
  display: grid;
  gap: 12px;
  margin-top: 20px;
}

.scenario-card {
  border-left: 4px solid;
  padding: 16px;
  background: #fafafa;
  cursor: pointer;
  transition: all 0.2s;
}

.scenario-card:hover {
  background: #f5f5f5;
}

.scenario-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.scenario-price {
  font-size: 1.5rem;
  font-weight: bold;
}

.scenario-confidence {
  font-size: 0.9rem;
  color: #666;
}

.scenario-details {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #ddd;
}

.detail-section {
  margin-bottom: 12px;
}

.detail-section h5 {
  font-size: 0.9rem;
  color: #666;
  margin-bottom: 4px;
}
```

**Definition of Done**:
- [x] Forecast panel component
- [x] Bar chart visualization
- [x] Quarter toggle (Q1/Q2)
- [x] Scenario cards with expand/collapse
- [x] Color coding for scenarios
- [x] Confidence display
- [x] Assumptions and risks sections
- [x] Responsive design
- [x] Loading states
- [x] Unit tests (≥85% coverage)
- [x] Integration tests

**Story Points**: 5
**Priority**: Must Have
**Dependencies**: F8.5-001 (Forecast API)
**Risk Level**: Low
**Assigned To**: Unassigned

