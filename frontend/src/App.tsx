// ABOUTME: Main React application component for portfolio management
// ABOUTME: Handles CSV upload, portfolio display, and live price updates

import { useState, useEffect } from 'react'
import axios from 'axios'
import TransactionImport from './components/TransactionImport'
import { DatabaseResetModal, useDatabaseReset } from './components/DatabaseResetModal'
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
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null)
  const [showImport, setShowImport] = useState(false)
  const { isModalOpen, openResetModal, closeResetModal, handleReset } = useDatabaseReset()

  useEffect(() => {
    fetchPortfolio()
  }, [])

  const fetchPortfolio = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/portfolio`)
      // Map the response to match our interface
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
    // Callback after successful database reset
    handleReset()
    // Refresh portfolio data
    fetchPortfolio()
  }

  return (
    <div className="app">
      <h1>Portfolio Management</h1>

      {/* Action Buttons */}
      <div className="action-buttons">
        <button
          className="toggle-import-btn"
          onClick={() => setShowImport(!showImport)}
        >
          {showImport ? 'Hide Import' : 'Import Transactions'}
        </button>
        <button
          className="reset-database-btn"
          onClick={openResetModal}
          title="Clear all data and start fresh"
        >
          Reset Database
        </button>
      </div>

      {/* Transaction Import Component */}
      {showImport && (
        <div className="import-section">
          <TransactionImport />
        </div>
      )}

      <div className="portfolio-section">
        <h2>Portfolio Overview</h2>
        {portfolio ? (
          <>
            <div className="summary">
              <h3>Total Value: ${portfolio.totalValue?.toFixed(2) || '0.00'}</h3>
              <h4>Cash: ${portfolio.cashBalance?.toFixed(2) || '0.00'}</h4>
            </div>

            {portfolio.positions.length > 0 ? (
              <table className="positions">
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
                      <td>{position.ticker}</td>
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
            ) : (
              <p>No positions yet. Upload a CSV to get started.</p>
            )}
          </>
        ) : (
          <p>Loading portfolio...</p>
        )}
      </div>

      {/* Database Reset Modal */}
      <DatabaseResetModal
        isOpen={isModalOpen}
        onClose={closeResetModal}
        onReset={onDatabaseReset}
      />
    </div>
  )
}

export default App
