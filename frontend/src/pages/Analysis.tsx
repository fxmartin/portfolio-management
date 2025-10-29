// ABOUTME: Main Analysis page component for AI-powered portfolio insights
// ABOUTME: Integrates global analysis, position list, and detailed analysis/forecast views

import { useState } from 'react'
import GlobalAnalysisCard from '../components/GlobalAnalysisCard'
import PositionAnalysisList from '../components/PositionAnalysisList'
import PositionAnalysisCard from '../components/PositionAnalysisCard'
import ForecastPanel from '../components/ForecastPanel'
import { Brain } from 'lucide-react'
import './Analysis.css'

type ViewMode = 'analysis' | 'forecast'

export const AnalysisPage: React.FC = () => {
  const [selectedSymbol, setSelectedSymbol] = useState<string | null>(null)
  const [viewMode, setViewMode] = useState<ViewMode>('analysis')

  const handleSelectPosition = (symbol: string) => {
    setSelectedSymbol(symbol)
    // Reset to analysis view when selecting a new position
    setViewMode('analysis')
  }

  return (
    <div className="analysis-page">
      {/* Page Header */}
      <header className="page-header">
        <div className="header-content">
          <div className="header-icon">
            <Brain size={32} />
          </div>
          <div className="header-text">
            <h1>AI-Powered Analysis</h1>
            <p className="subtitle">
              Get intelligent market insights and forecasts powered by Claude AI
            </p>
          </div>
        </div>
      </header>

      {/* Global Analysis Section - Full Width */}
      <section className="global-section">
        <GlobalAnalysisCard />
      </section>

      {/* Two-Column Layout: Position List + Detail Panel */}
      <div className="analysis-grid">
        {/* Position List - Left Side */}
        <section className="positions-section">
          <PositionAnalysisList
            onSelectPosition={handleSelectPosition}
            selectedSymbol={selectedSymbol}
          />
        </section>

        {/* Detail Panel - Right Side */}
        <section className="detail-section">
          {selectedSymbol ? (
            <>
              {/* Mode Tabs */}
              <div className="mode-tabs">
                <button
                  className={`tab-button ${viewMode === 'analysis' ? 'active' : ''}`}
                  onClick={() => setViewMode('analysis')}
                  aria-pressed={viewMode === 'analysis'}
                >
                  Analysis
                </button>
                <button
                  className={`tab-button ${viewMode === 'forecast' ? 'active' : ''}`}
                  onClick={() => setViewMode('forecast')}
                  aria-pressed={viewMode === 'forecast'}
                >
                  Forecast
                </button>
              </div>

              {/* Content Area */}
              <div className="detail-content">
                {viewMode === 'analysis' && (
                  <PositionAnalysisCard symbol={selectedSymbol} />
                )}

                {viewMode === 'forecast' && (
                  <ForecastPanel symbol={selectedSymbol} />
                )}
              </div>
            </>
          ) : (
            <div className="empty-state">
              <div className="empty-icon">
                <Brain size={64} />
              </div>
              <h3>Select a Position</h3>
              <p>Choose a position from the list to view AI-powered analysis and forecasts</p>
            </div>
          )}
        </section>
      </div>
    </div>
  )
}

export default AnalysisPage
