// ABOUTME: React context for coordinating portfolio data refreshes across components
// ABOUTME: Allows any component to trigger position/holdings refresh after data changes

import React, { createContext, useContext, useCallback, useState } from 'react';

interface PortfolioRefreshContextType {
  refreshKey: number;
  triggerRefresh: () => void;
}

const PortfolioRefreshContext = createContext<PortfolioRefreshContextType | undefined>(undefined);

export const PortfolioRefreshProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [refreshKey, setRefreshKey] = useState(0);

  const triggerRefresh = useCallback(() => {
    console.log('[PortfolioRefreshContext] Triggering portfolio refresh');
    setRefreshKey(prev => prev + 1);
  }, []);

  return (
    <PortfolioRefreshContext.Provider value={{ refreshKey, triggerRefresh }}>
      {children}
    </PortfolioRefreshContext.Provider>
  );
};

export const usePortfolioRefresh = () => {
  const context = useContext(PortfolioRefreshContext);
  if (context === undefined) {
    throw new Error('usePortfolioRefresh must be used within a PortfolioRefreshProvider');
  }
  return context;
};
