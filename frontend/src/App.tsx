// ABOUTME: Main React application component for portfolio management
// ABOUTME: Modern UI with sidebar navigation and tab-based content organization

import { useState, useEffect } from 'react'
import axios from 'axios'
import Sidebar from './components/Sidebar'
import TabView from './components/TabView'
import TransactionImport from './components/TransactionImport'
import { DatabaseResetModal, useDatabaseReset } from './components/DatabaseResetModal'
import DatabaseStats from './components/DatabaseStats'
import './App.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

interface Position {
  ticker: string
  quantity: number
  avgCost: number
  currentPrice: number
  value: number
  pnl: number
  pnlPercent: number
}

interface Portfolio {
  totalValue: number
  positions: Position[]
  cashBalance: number
}

function App() {
  const [activeTab, setActiveTab] = useState('portfolio')
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null)
  const { isModalOpen, openResetModal, closeResetModal, handleReset } = useDatabaseReset()

  useEffect(() => {
    fetchPortfolio()
  }, [])

  const fetchPortfolio = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/portfolio`)
      const data = response.data
      setPortfolio({
        totalValue: data.total_value || 0,
        positions: data.positions || [],
        cashBalance: data.cash_balance || 0
      })
    } catch (error) {
      console.error('Failed to fetch portfolio:', error)
    }
  }

  const onDatabaseReset = () => {
    handleReset()
    fetchPortfolio()
  }

  const handleTabChange = (tab: string) => {
    setActiveTab(tab)

    // Handle database submenu items
    if (tab === 'database-reset') {
      openResetModal()
      // Keep activeTab on database-reset so the Database icon stays highlighted
    }
  }

  return (
    <div className="app-layout">
      <Sidebar activeTab={activeTab} onTabChange={handleTabChange} />

      <main className="main-content">
        <TabView activeTab={activeTab}>
          {/* Portfolio Tab */}
          <div data-tab="portfolio" className="portfolio-tab">
            <h1>Portfolio Overview</h1>
            {portfolio ? (
              <>
                <div className="summary-cards">
                  <div className="summary-card">
                    <div className="card-label">Total Value</div>
                    <div className="card-value">${portfolio.totalValue?.toFixed(2) || '0.00'}</div>
                  </div>
                  <div className="summary-card">
                    <div className="card-label">Cash Balance</div>
                    <div className="card-value">${portfolio.cashBalance?.toFixed(2) || '0.00'}</div>
                  </div>
                </div>

                {portfolio.positions.length > 0 ? (
                  <div className="positions-container">
                    <h2>Positions</h2>
                    <table className="positions-table">
                      <thead>
                        <tr>
                          <th>Ticker</th>
                          <th>Quantity</th>
                          <th>Avg Cost</th>
                          <th>Current Price</th>
                          <th>Value</th>
                          <th>P&L</th>
                          <th>P&L %</th>
                        </tr>
                      </thead>
                      <tbody>
                        {portfolio.positions.map((position) => (
                          <tr key={position.ticker}>
                            <td className="ticker">{position.ticker}</td>
                            <td>{position.quantity}</td>
                            <td>${position.avgCost?.toFixed(2) || '0.00'}</td>
                            <td>${position.currentPrice?.toFixed(2) || '0.00'}</td>
                            <td>${position.value?.toFixed(2) || '0.00'}</td>
                            <td className={(position.pnl ?? 0) >= 0 ? 'profit' : 'loss'}>
                              ${position.pnl?.toFixed(2) || '0.00'}
                            </td>
                            <td className={(position.pnlPercent ?? 0) >= 0 ? 'profit' : 'loss'}>
                              {position.pnlPercent?.toFixed(2) || '0.00'}%
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className="empty-state">
                    <p>No positions yet. Upload a CSV to get started.</p>
                  </div>
                )}
              </>
            ) : (
              <div className="loading-state">
                <p>Loading portfolio...</p>
              </div>
            )}
          </div>

          {/* Upload Tab */}
          <div data-tab="upload" className="upload-tab">
            <TransactionImport />
          </div>

          {/* Database Stats Tab */}
          <div data-tab="database-stats" className="database-tab">
            <DatabaseStats
              isOpen={true}
              onClose={() => setActiveTab('portfolio')}
              autoRefresh={false}
            />
          </div>

          {/* Database Reset Tab - handled by modal */}
          <div data-tab="database-reset" className="database-tab">
            <div className="empty-state">
              <p>Opening reset dialog...</p>
            </div>
          </div>
        </TabView>
      </main>

      {/* Database Reset Modal */}
      <DatabaseResetModal
        isOpen={isModalOpen}
        onClose={() => {
          closeResetModal()
          setActiveTab('portfolio')
        }}
        onReset={onDatabaseReset}
      />
    </div>
  )
}

export default App
