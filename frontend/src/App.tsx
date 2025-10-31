// ABOUTME: Main React application component for portfolio management
// ABOUTME: Modern UI with sidebar navigation and tab-based content organization

import { useState } from 'react'
import { PortfolioRefreshProvider } from './contexts/PortfolioRefreshContext'
import Sidebar from './components/Sidebar'
import TabView from './components/TabView'
import TransactionImport from './components/TransactionImport'
import TransactionList from './components/TransactionList'
import OpenPositionsCard from './components/OpenPositionsCard'
import HoldingsTable from './components/HoldingsTable'
import RealizedPnLCard from './components/RealizedPnLCard'
import AnalysisPage from './pages/Analysis'
import RebalancingPage from './pages/Rebalancing'
import { DatabaseResetModal, useDatabaseReset } from './components/DatabaseResetModal'
import DatabaseStats from './components/DatabaseStats'
import './App.css'

function App() {
  const [activeTab, setActiveTab] = useState('portfolio')
  const [assetTypeFilter, setAssetTypeFilter] = useState<string | null>(null)
  const { isModalOpen, openResetModal, closeResetModal, handleReset } = useDatabaseReset()

  const onDatabaseReset = () => {
    handleReset()
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
    <PortfolioRefreshProvider>
      <div className="app-layout">
        <Sidebar activeTab={activeTab} onTabChange={handleTabChange} />

        <main className="main-content">
          <TabView activeTab={activeTab}>
            {/* Portfolio Tab */}
            <div data-tab="portfolio" className="portfolio-tab">
              <h1>Portfolio Dashboard</h1>
              <OpenPositionsCard onAssetTypeFilter={setAssetTypeFilter} />
              <HoldingsTable externalFilter={assetTypeFilter} />
              <RealizedPnLCard />
            </div>

            {/* Upload Tab */}
            <div data-tab="upload" className="upload-tab">
              <TransactionImport />
            </div>

            {/* Transactions Tab */}
            <div data-tab="transactions" className="transactions-tab">
              <TransactionList />
            </div>

            {/* Analysis Tab */}
            <div data-tab="analysis" className="analysis-tab">
              <AnalysisPage />
            </div>

            {/* Rebalancing Tab */}
            <div data-tab="rebalancing" className="rebalancing-tab">
              <RebalancingPage />
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
    </PortfolioRefreshProvider>
  )
}

export default App
