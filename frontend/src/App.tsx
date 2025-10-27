// ABOUTME: Main React application component for portfolio management
// ABOUTME: Modern UI with sidebar navigation and tab-based content organization

import { useState } from 'react'
import Sidebar from './components/Sidebar'
import TabView from './components/TabView'
import TransactionImport from './components/TransactionImport'
import OpenPositionsCard from './components/OpenPositionsCard'
import PortfolioValueChart from './components/PortfolioValueChart'
import HoldingsTable from './components/HoldingsTable'
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
    <div className="app-layout">
      <Sidebar activeTab={activeTab} onTabChange={handleTabChange} />

      <main className="main-content">
        <TabView activeTab={activeTab}>
          {/* Portfolio Tab */}
          <div data-tab="portfolio" className="portfolio-tab">
            <h1>Portfolio Dashboard</h1>
            <OpenPositionsCard onAssetTypeFilter={setAssetTypeFilter} />
            <PortfolioValueChart currency="EUR" />
            <HoldingsTable externalFilter={assetTypeFilter} />
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
