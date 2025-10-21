// ABOUTME: Tab view component for organizing main content into switchable tabs
// ABOUTME: Handles tab switching with smooth transitions and proper content management

import { ReactNode, Children, cloneElement, ReactElement } from 'react'
import './TabView.css'

interface TabViewProps {
  activeTab: string
  children?: ReactNode
}

const TabView: React.FC<TabViewProps> = ({ activeTab, children }) => {
  // Find the active tab content
  const childrenArray = Children.toArray(children) as ReactElement[]

  const activeContent = childrenArray.find((child) => {
    return child.props['data-tab'] === activeTab
  })

  return (
    <div className="tab-view">
      {activeContent && (
        <div className="tab-panel" role="tabpanel" aria-labelledby={activeTab}>
          {cloneElement(activeContent)}
        </div>
      )}
      {!activeContent && (
        <div className="tab-panel" role="tabpanel">
          <div className="empty-state">
            <p>Tab "{activeTab}" not found</p>
          </div>
        </div>
      )}
    </div>
  )
}

export default TabView
