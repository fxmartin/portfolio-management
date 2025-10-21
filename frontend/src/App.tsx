// ABOUTME: Main React application component for portfolio management
// ABOUTME: Handles CSV upload, portfolio display, and live price updates

import { useState, useEffect } from 'react'
import axios from 'axios'
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
  const [loading, setLoading] = useState(false)
  const [uploadStatus, setUploadStatus] = useState('')

  useEffect(() => {
    fetchPortfolio()
  }, [])

  const fetchPortfolio = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/portfolio`)
      setPortfolio(response.data)
    } catch (error) {
      console.error('Failed to fetch portfolio:', error)
    }
  }

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    setLoading(true)
    setUploadStatus('Uploading...')

    const formData = new FormData()
    formData.append('file', file)

    try {
      await axios.post(`${API_URL}/api/import/revolut`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })
      setUploadStatus('Upload successful! Processing transactions...')
      setTimeout(() => {
        fetchPortfolio()
        setUploadStatus('')
      }, 2000)
    } catch (error) {
      setUploadStatus('Upload failed. Please try again.')
      console.error('Upload error:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app">
      <h1>Portfolio Management</h1>

      <div className="upload-section">
        <h2>Import Revolut CSV</h2>
        <input
          type="file"
          accept=".csv"
          onChange={handleFileUpload}
          disabled={loading}
        />
        {uploadStatus && <p className="status">{uploadStatus}</p>}
      </div>

      <div className="portfolio-section">
        <h2>Portfolio Overview</h2>
        {portfolio ? (
          <>
            <div className="summary">
              <h3>Total Value: ${portfolio.totalValue.toFixed(2)}</h3>
              <h4>Cash: ${portfolio.cashBalance.toFixed(2)}</h4>
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
                      <td className={position.pnl >= 0 ? 'profit' : 'loss'}>
                        ${position.pnl?.toFixed(2) || '0.00'}
                      </td>
                      <td className={position.pnlPercent >= 0 ? 'profit' : 'loss'}>
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
    </div>
  )
}

export default App
