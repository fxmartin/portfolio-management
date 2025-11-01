// ABOUTME: Strategy editor card for creating/updating investment strategies
// ABOUTME: Features validation, character/word counting, templates, and structured fields

import React, { useState, useEffect } from 'react'
import { StrategyTemplatesModal } from './StrategyTemplatesModal'
import type { InvestmentStrategy, StrategyTemplate } from '../types/strategy'
import './StrategyEditorCard.css'

interface StrategyEditorCardProps {
  strategy?: InvestmentStrategy
  onSave: (data: Partial<InvestmentStrategy>) => Promise<void>
}

const MAX_CHARS = 5000
const MIN_WORDS = 20

export const StrategyEditorCard: React.FC<StrategyEditorCardProps> = ({
  strategy,
  onSave
}) => {
  const [strategyText, setStrategyText] = useState('')
  const [targetAnnualReturn, setTargetAnnualReturn] = useState<number>(10)
  const [riskTolerance, setRiskTolerance] = useState<'low' | 'medium' | 'high' | 'custom'>('medium')
  const [timeHorizonYears, setTimeHorizonYears] = useState<number>(10)
  const [maxPositions, setMaxPositions] = useState<number>(25)
  const [profitTakingThreshold, setProfitTakingThreshold] = useState<number>(50)

  const [isTemplatesOpen, setIsTemplatesOpen] = useState(false)
  const [isSaving, setIsSaving] = useState(false)

  useEffect(() => {
    if (strategy) {
      setStrategyText(strategy.strategy_text)
      setTargetAnnualReturn(strategy.target_annual_return || 10)
      setRiskTolerance(strategy.risk_tolerance || 'medium')
      setTimeHorizonYears(strategy.time_horizon_years || 10)
      setMaxPositions(strategy.max_positions || 25)
      setProfitTakingThreshold(strategy.profit_taking_threshold || 50)
    }
  }, [strategy])

  const charCount = strategyText.length
  const wordCount = strategyText.trim().split(/\s+/).filter(word => word.length > 0).length

  const isValid = wordCount >= MIN_WORDS && charCount <= MAX_CHARS
  const hasMinWords = wordCount >= MIN_WORDS
  const underMaxChars = charCount <= MAX_CHARS

  const handleTemplateSelect = (template: StrategyTemplate) => {
    setStrategyText(template.strategy_text)
    setTargetAnnualReturn(template.target_annual_return)
    setRiskTolerance(template.risk_tolerance)
    setTimeHorizonYears(template.time_horizon_years)
    setMaxPositions(template.max_positions)
    setProfitTakingThreshold(template.profit_taking_threshold)
  }

  const handleSave = async () => {
    if (!isValid) return

    setIsSaving(true)
    try {
      await onSave({
        strategy_text: strategyText,
        target_annual_return: targetAnnualReturn,
        risk_tolerance: riskTolerance,
        time_horizon_years: timeHorizonYears,
        max_positions: maxPositions,
        profit_taking_threshold: profitTakingThreshold
      })
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <>
      <div className="strategy-editor-card card">
        <div className="card-header">
          <h2>Investment Strategy</h2>
          {strategy && (
            <div className="strategy-meta">
              <span className="version-badge">Version {strategy.version}</span>
              <span className="last-updated">
                Last updated: {new Date(strategy.updated_at).toLocaleDateString()}
              </span>
            </div>
          )}
        </div>

        <div className="card-body">
          {/* Strategy Text */}
          <div className="form-group">
            <label htmlFor="strategy-text" className="form-label">
              Strategy Text *
            </label>
            <textarea
              id="strategy-text"
              className={`form-textarea ${!hasMinWords || !underMaxChars ? 'invalid' : ''}`}
              value={strategyText}
              onChange={(e) => setStrategyText(e.target.value)}
              placeholder="Describe your investment strategy, goals, risk tolerance, asset allocation preferences, and decision-making criteria..."
              rows={12}
              maxLength={MAX_CHARS}
            />

            <div className="textarea-footer">
              <div className="counters">
                <span className={`counter ${!underMaxChars ? 'error' : ''}`}>
                  {charCount} / {MAX_CHARS} characters
                </span>
                <span className={`counter ${!hasMinWords ? 'error' : ''}`}>
                  {wordCount} words (minimum {MIN_WORDS})
                </span>
              </div>
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={() => setIsTemplatesOpen(true)}
              >
                Use Template
              </button>
            </div>

            {!hasMinWords && strategyText.length > 0 && (
              <div className="validation-error">
                Minimum 20 words required. Current: {wordCount} words.
              </div>
            )}
            {!underMaxChars && (
              <div className="validation-error">
                Maximum 5000 characters exceeded.
              </div>
            )}
          </div>

          {/* Structured Fields */}
          <div className="structured-fields">
            <h3 className="section-title">Additional Parameters (Optional)</h3>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="target-return" className="form-label">
                  Target Annual Return (%)
                </label>
                <input
                  id="target-return"
                  type="number"
                  className="form-input"
                  min="0"
                  max="100"
                  value={targetAnnualReturn}
                  onChange={(e) => setTargetAnnualReturn(parseInt(e.target.value) || 0)}
                />
                <div className="input-slider">
                  <input
                    type="range"
                    min="0"
                    max="100"
                    value={targetAnnualReturn}
                    onChange={(e) => setTargetAnnualReturn(parseInt(e.target.value))}
                  />
                </div>
              </div>

              <div className="form-group">
                <label htmlFor="risk-tolerance" className="form-label">
                  Risk Tolerance
                </label>
                <select
                  id="risk-tolerance"
                  className="form-select"
                  value={riskTolerance}
                  onChange={(e) => setRiskTolerance(e.target.value as any)}
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="custom">Custom</option>
                </select>
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="time-horizon" className="form-label">
                  Time Horizon (years)
                </label>
                <input
                  id="time-horizon"
                  type="number"
                  className="form-input"
                  min="1"
                  max="50"
                  value={timeHorizonYears}
                  onChange={(e) => setTimeHorizonYears(parseInt(e.target.value) || 1)}
                />
                <div className="input-slider">
                  <input
                    type="range"
                    min="1"
                    max="50"
                    value={timeHorizonYears}
                    onChange={(e) => setTimeHorizonYears(parseInt(e.target.value))}
                  />
                </div>
              </div>

              <div className="form-group">
                <label htmlFor="max-positions" className="form-label">
                  Max Positions
                </label>
                <input
                  id="max-positions"
                  type="number"
                  className="form-input"
                  min="1"
                  max="100"
                  value={maxPositions}
                  onChange={(e) => {
                    const value = parseInt(e.target.value) || 1
                    setMaxPositions(Math.min(100, Math.max(1, value)))
                  }}
                />
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="profit-threshold" className="form-label">
                  Profit-Taking Threshold (%)
                </label>
                <input
                  id="profit-threshold"
                  type="number"
                  className="form-input"
                  min="0"
                  max="1000"
                  value={profitTakingThreshold}
                  onChange={(e) => setProfitTakingThreshold(parseInt(e.target.value) || 0)}
                />
                <div className="input-slider">
                  <input
                    type="range"
                    min="0"
                    max="200"
                    step="5"
                    value={Math.min(profitTakingThreshold, 200)}
                    onChange={(e) => setProfitTakingThreshold(parseInt(e.target.value))}
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Save Button */}
          <div className="card-footer">
            <button
              type="button"
              className="btn btn-primary"
              onClick={handleSave}
              disabled={!isValid || isSaving}
            >
              {isSaving ? (
                <>
                  <span className="spinner"></span>
                  Saving...
                </>
              ) : (
                'Save Strategy'
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Templates Modal */}
      <StrategyTemplatesModal
        isOpen={isTemplatesOpen}
        onClose={() => setIsTemplatesOpen(false)}
        onSelectTemplate={handleTemplateSelect}
      />
    </>
  )
}
