// ABOUTME: Main page for investment strategy management
// ABOUTME: Integrates strategy editor and recommendations display

import { useState, useEffect } from 'react';
import { RefreshCw } from 'lucide-react';
import { StrategyEditorCard } from '../components/StrategyEditorCard';
import StrategyRecommendationsCard from '../components/StrategyRecommendationsCard';
import { getStrategy, createStrategy, updateStrategy, getRecommendations } from '../api/strategy';
import type { InvestmentStrategy, StrategyDrivenRecommendationResponse } from '../types/strategy';
import './StrategyPage.css';

interface StrategyPageProps {
  onNavigateToTransactions?: () => void;
}

export default function StrategyPage({ onNavigateToTransactions }: StrategyPageProps = {}) {
  const [strategy, setStrategy] = useState<InvestmentStrategy | null>(null);
  const [recommendations, setRecommendations] = useState<StrategyDrivenRecommendationResponse | null>(null);
  const [loadingStrategy, setLoadingStrategy] = useState(true);
  const [loadingRecommendations, setLoadingRecommendations] = useState(false);
  const [savingStrategy, setSavingStrategy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadStrategy();
  }, []);

  const loadStrategy = async () => {
    try {
      setLoadingStrategy(true);
      setError(null);
      const data = await getStrategy();
      setStrategy(data);

      if (data) {
        // Auto-load recommendations if strategy exists
        await loadRecommendations();
      }
    } catch (err) {
      setError('Failed to load strategy');
      console.error('Failed to load strategy:', err);
    } finally {
      setLoadingStrategy(false);
    }
  };

  const loadRecommendations = async (forceRefresh = false) => {
    try {
      setLoadingRecommendations(true);
      const data = await getRecommendations(forceRefresh);
      setRecommendations(data);
    } catch (err) {
      // Don't set global error, show in recommendations card
      console.error('Failed to load recommendations:', err);
    } finally {
      setLoadingRecommendations(false);
    }
  };

  const handleSaveStrategy = async (formData: Partial<InvestmentStrategy>) => {
    try {
      setSavingStrategy(true);
      let savedStrategy;

      if (strategy) {
        savedStrategy = await updateStrategy(formData);
      } else {
        savedStrategy = await createStrategy(formData as any);
      }

      setStrategy(savedStrategy);

      // Auto-refresh recommendations with new strategy
      await loadRecommendations(true);
    } catch (err) {
      console.error('Failed to save strategy:', err);
      throw err; // Let the editor card handle the error
    } finally {
      setSavingStrategy(false);
    }
  };

  return (
    <div className="strategy-page">
      <header className="page-header">
        <h1>Investment Strategy</h1>
        {strategy && (
          <button
            onClick={() => loadRecommendations(true)}
            className="refresh-recommendations-button"
            disabled={loadingRecommendations}
          >
            <RefreshCw size={16} className={loadingRecommendations ? 'spinning' : ''} />
            Refresh Recommendations
          </button>
        )}
      </header>

      {error && (
        <div className="page-error">
          <p>{error}</p>
          <button onClick={loadStrategy}>Retry</button>
        </div>
      )}

      <div className="strategy-layout">
        <div className="strategy-editor-section">
          <StrategyEditorCard
            strategy={strategy}
            loading={loadingStrategy}
            saving={savingStrategy}
            onSave={handleSaveStrategy}
          />
        </div>

        <div className="strategy-recommendations-section">
          {strategy ? (
            <StrategyRecommendationsCard
              recommendations={recommendations}
              loading={loadingRecommendations}
              error={null}
              onRefresh={() => loadRecommendations(true)}
              onNavigateToTransactions={onNavigateToTransactions}
            />
          ) : (
            <div className="empty-state">
              <div className="empty-state-content">
                <h3>No Strategy Yet</h3>
                <p>Create your investment strategy to get personalized portfolio recommendations</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
