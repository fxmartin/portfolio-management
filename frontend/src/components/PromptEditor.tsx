// ABOUTME: Modal editor for creating and editing prompts with validation
// ABOUTME: Includes variable detection, template validation, and form handling

import { useState, useEffect, useMemo, useRef } from 'react'
import { X, Loader2 } from 'lucide-react'
import { toast } from 'react-toastify'
import type { PromptResponse, PromptCreate, PromptUpdate, PromptCategory } from '../types/prompt.types'
import './PromptEditor.css'

export interface PromptEditorProps {
  prompt: PromptResponse | null // null = create mode
  onSave: (data: PromptCreate | PromptUpdate) => Promise<void>
  onCancel: () => void
}

export const PromptEditor: React.FC<PromptEditorProps> = ({
  prompt,
  onSave,
  onCancel
}) => {
  // Form data
  const [name, setName] = useState(prompt?.name || '')
  const [category, setCategory] = useState<PromptCategory>(prompt?.category || 'global')
  const [promptText, setPromptText] = useState(prompt?.prompt_text || '')
  const [templateVariables, setTemplateVariables] = useState<Record<string, string>>(
    prompt?.template_variables || {}
  )
  const [changeReason, setChangeReason] = useState('')

  // UI state
  const [saving, setSaving] = useState(false)
  const [testing, setTesting] = useState(false)
  const [testResult, setTestResult] = useState<string | null>(null)
  const [errors, setErrors] = useState<Record<string, string>>({})

  // Refs
  const nameInputRef = useRef<HTMLInputElement>(null)

  // Auto-focus name input when modal opens
  useEffect(() => {
    nameInputRef.current?.focus()
  }, [])

  // Detect variables in template
  const detectVariables = (text: string): string[] => {
    // Support whitespace and kebab-case: {{var-name}} or {{ variable }}
    const regex = /\{\{\s*([\w-]+)\s*\}\}/g
    const matches = [...text.matchAll(regex)]
    return [...new Set(matches.map(m => m[1].trim()))]
  }

  // Highlighted variables (memoized)
  const highlightedVariables = useMemo(() => {
    return detectVariables(promptText)
  }, [promptText])

  // Auto-add detected variables to templateVariables
  useEffect(() => {
    const detected = detectVariables(promptText)
    const newVars = { ...templateVariables }
    let hasChanges = false

    detected.forEach(varName => {
      if (!(varName in newVars)) {
        newVars[varName] = 'string' // Default type
        hasChanges = true
      }
    })

    if (hasChanges) {
      setTemplateVariables(newVars)
    }
  }, [promptText]) // Note: intentionally not including templateVariables to avoid infinite loop

  // Close modal on Escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !saving) {
        onCancel()
      }
    }

    document.addEventListener('keydown', handleEscape)
    return () => document.removeEventListener('keydown', handleEscape)
  }, [saving, onCancel])

  // Validate form
  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {}

    // Name validation
    if (!name.trim()) {
      newErrors.name = 'Prompt name is required'
    } else if (name.length > 100) {
      newErrors.name = 'Name must be 100 characters or less'
    }

    // Prompt text validation
    if (!promptText.trim()) {
      newErrors.promptText = 'Prompt text is required'
    } else if (promptText.length < 10) {
      newErrors.promptText = 'Prompt must be at least 10 characters'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  // Test template (syntax validation only)
  const handleTestPrompt = async () => {
    setTesting(true)
    setTestResult(null)

    try {
      const detected = detectVariables(promptText)
      const missingVars = detected.filter(v => !(v in templateVariables))

      if (missingVars.length > 0) {
        setTestResult(`Missing variable definitions: ${missingVars.join(', ')}`)
      } else {
        setTestResult('✓ Template is valid')
        toast.success('Template is valid!')
      }
    } catch (err: any) {
      setTestResult(`Error: ${err.message}`)
    } finally {
      setTesting(false)
    }
  }

  // Save prompt
  const handleSave = async () => {
    if (!validateForm()) {
      return
    }

    try {
      setSaving(true)
      setErrors({})

      if (prompt) {
        // Update mode
        await onSave({
          name,
          category,
          prompt_text: promptText,
          template_variables: templateVariables,
          change_reason: changeReason || undefined
        })
      } else {
        // Create mode
        await onSave({
          name,
          category,
          prompt_text: promptText,
          template_variables: templateVariables
        })
      }

      // onSave will handle closing and showing success
    } catch (err: any) {
      console.error('Failed to save prompt:', err)
      const message = err.response?.data?.detail || 'Failed to save prompt'
      setErrors({ general: message })
    } finally {
      setSaving(false)
    }
  }

  // Remove variable
  const handleRemoveVariable = (varName: string) => {
    const newVars = { ...templateVariables }
    delete newVars[varName]
    setTemplateVariables(newVars)
  }

  // Change variable type
  const handleChangeVariableType = (varName: string, type: string) => {
    setTemplateVariables({
      ...templateVariables,
      [varName]: type
    })
  }

  // Handle overlay click
  const handleOverlayClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) {
      onCancel()
    }
  }

  return (
    <div className="prompt-editor-modal" onClick={handleOverlayClick}>
      <div className="prompt-editor-overlay" aria-hidden="true" />

      <div
        className="prompt-editor-panel"
        role="dialog"
        aria-modal="true"
        aria-labelledby="prompt-editor-title"
      >
        <div className="prompt-editor-header">
          <h2 id="prompt-editor-title">
            {prompt ? 'Edit Prompt' : 'Create Prompt'}
          </h2>
          <button
            className="close-btn"
            onClick={onCancel}
            aria-label="Close"
            disabled={saving}
          >
            <X size={20} />
          </button>
        </div>

        <div className="prompt-editor-body">
          {/* General error */}
          {errors.general && (
            <div className="error-banner" role="alert">
              {errors.general}
            </div>
          )}

          {/* Name Input */}
          <div className="form-group">
            <label htmlFor="prompt-name">Prompt Name</label>
            <input
              ref={nameInputRef}
              id="prompt-name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., global_market_analysis"
              className={errors.name ? 'error' : ''}
              aria-invalid={!!errors.name}
              aria-describedby={errors.name ? 'prompt-name-error' : undefined}
              disabled={saving || testing}
            />
            {errors.name && (
              <span className="error-text" id="prompt-name-error" role="alert">
                {errors.name}
              </span>
            )}
          </div>

          {/* Category Selector */}
          <div className="form-group">
            <label htmlFor="prompt-category">Category</label>
            <select
              id="prompt-category"
              value={category}
              onChange={(e) => setCategory(e.target.value as PromptCategory)}
              className={errors.category ? 'error' : ''}
              disabled={saving || testing}
            >
              <option value="global">Global Analysis</option>
              <option value="position">Position Analysis</option>
              <option value="forecast">Forecast Analysis</option>
            </select>
            {errors.category && (
              <span className="error-text" role="alert">
                {errors.category}
              </span>
            )}
          </div>

          {/* Prompt Template Textarea */}
          <div className="form-group">
            <label htmlFor="prompt-text">
              Prompt Template
              <span className="label-hint">
                Use {'{{variable}}'} for placeholders
              </span>
            </label>
            <textarea
              id="prompt-text"
              value={promptText}
              onChange={(e) => setPromptText(e.target.value)}
              placeholder="Enter your prompt template here..."
              className={`prompt-textarea ${errors.promptText ? 'error' : ''}`}
              rows={15}
              spellCheck={false}
              disabled={saving || testing}
            />
            {errors.promptText && (
              <span className="error-text" role="alert">
                {errors.promptText}
              </span>
            )}

            {/* Variable Hints */}
            {highlightedVariables.length > 0 && (
              <div className="variable-hints">
                <strong>Detected Variables:</strong>
                {highlightedVariables.map(varName => (
                  <span key={varName} className="variable-badge">
                    {`{{${varName}}}`}
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Template Variables Manager */}
          {Object.keys(templateVariables).length > 0 && (
            <div className="form-group">
              <label>Template Variables</label>
              <div className="template-variables">
                {Object.entries(templateVariables).map(([varName, varType]) => (
                  <div key={varName} className="variable-row">
                    <span className="variable-name">{varName}</span>
                    <select
                      value={varType}
                      onChange={(e) => handleChangeVariableType(varName, e.target.value)}
                      disabled={saving || testing}
                    >
                      <option value="string">String</option>
                      <option value="number">Number</option>
                      <option value="decimal">Decimal</option>
                      <option value="date">Date</option>
                      <option value="boolean">Boolean</option>
                    </select>
                    <button
                      onClick={() => handleRemoveVariable(varName)}
                      className="remove-var-btn"
                      title="Remove variable"
                      aria-label="Remove variable"
                      disabled={saving || testing}
                    >
                      <X size={14} />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Change Reason (only for updates) */}
          {prompt && (
            <div className="form-group">
              <label htmlFor="change-reason">
                Change Reason
                <span className="label-hint">(optional)</span>
              </label>
              <input
                id="change-reason"
                type="text"
                value={changeReason}
                onChange={(e) => setChangeReason(e.target.value)}
                placeholder="e.g., Improved clarity"
                disabled={saving || testing}
              />
            </div>
          )}

          {/* Test Result */}
          {testResult && (
            <div className={`test-result ${testResult.startsWith('✓') ? 'success' : 'error'}`}>
              {testResult}
            </div>
          )}
        </div>

        <div className="prompt-editor-footer">
          <div className="footer-left">
            {prompt && (
              <span className="version-indicator">
                Current version: v{prompt.version}
              </span>
            )}
          </div>

          <div className="footer-right">
            <button
              className="btn-secondary"
              onClick={handleTestPrompt}
              disabled={testing || saving || !promptText}
            >
              {testing ? (
                <>
                  <Loader2 size={14} className="spinner-icon" />
                  Testing...
                </>
              ) : (
                'Test Template'
              )}
            </button>

            <button
              className="btn-secondary"
              onClick={onCancel}
              disabled={saving}
            >
              Cancel
            </button>

            <button
              className="btn-primary"
              onClick={handleSave}
              disabled={saving || testing}
            >
              {saving ? (
                <>
                  <Loader2 size={14} className="spinner-icon" />
                  Saving...
                </>
              ) : (
                'Save Prompt'
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default PromptEditor
