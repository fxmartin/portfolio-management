// ABOUTME: Specialized component for API key input with test functionality and last updated timestamp
// ABOUTME: Extends SettingItem with test key button, success/error feedback, and timestamp display

import { useState } from 'react'
import { Eye, EyeOff, Loader2, CheckCircle, XCircle } from 'lucide-react'
import { toast } from 'react-toastify'
import axios from 'axios'
import { API_CONFIG } from '../config/app.config'
import { useSettingValidation } from '../hooks/useSettingValidation'
import type { Setting } from './SettingsCategoryPanel'
import './ApiKeyInput.css'

const API_URL = API_CONFIG.BASE_URL

export interface ApiKeyInputProps {
  setting: Setting
  onUpdate: (key: string, value: string | number | boolean) => Promise<void>
  onReset: (key: string) => Promise<void>
}

export const ApiKeyInput: React.FC<ApiKeyInputProps> = ({
  setting,
  onUpdate,
  onReset
}) => {
  const [currentValue, setCurrentValue] = useState<string>(
    setting.value === '********' ? '' : String(setting.value)
  )
  const [showPassword, setShowPassword] = useState(false)
  const [saving, setSaving] = useState(false)
  const [testing, setTesting] = useState(false)
  const [testResult, setTestResult] = useState<'success' | 'error' | null>(null)
  const [testError, setTestError] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  // Real-time validation hook
  const { isValid, error: validationError, validating } = useSettingValidation(
    setting.key,
    currentValue
  )

  const hasChanged = currentValue !== setting.value && currentValue !== ''
  const hasDefaultChanged = setting.value !== setting.default_value

  // Save button should be enabled only when:
  // - Value has changed
  // - Not currently saving
  // - Not currently validating
  // - Value is valid
  const canSave = hasChanged && !saving && !validating && isValid

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setError(null)
    setTestResult(null)
    setTestError(null)
    setCurrentValue(e.target.value)
  }

  const handleSave = async () => {
    try {
      setSaving(true)
      setError(null)
      await onUpdate(setting.key, currentValue)
      toast.success(`${setting.name} saved successfully`)
      setSaving(false)
    } catch (err) {
      console.error('Failed to save setting:', err)
      toast.error(`Failed to save ${setting.name}`)
      setError('Failed to update setting')
      // Revert to previous value on error (optimistic update rollback)
      setCurrentValue(setting.value === '********' ? '' : String(setting.value))
      setSaving(false)
    }
  }

  const handleReset = async () => {
    try {
      setSaving(true)
      setError(null)
      setTestResult(null)
      setTestError(null)
      await onReset(setting.key)
      setSaving(false)
    } catch (err) {
      console.error('Failed to reset setting:', err)
      setError('Failed to reset setting')
      setSaving(false)
    }
  }

  const handleTest = async () => {
    if (!currentValue || currentValue === '********') {
      setTestError('Please enter an API key to test')
      setTestResult('error')
      return
    }

    try {
      setTesting(true)
      setTestResult(null)
      setTestError(null)

      const response = await axios.post<{
        valid: boolean
        error?: string
        validated_value?: string
      }>(`${API_URL}/api/settings/${setting.key}/test`, {
        value: currentValue
      })

      if (response.data.valid) {
        setTestResult('success')
        setTestError(null)
        toast.success('API key is valid!')
      } else {
        setTestResult('error')
        setTestError(response.data.error || 'API key test failed')
      }
    } catch (err: any) {
      console.error('Failed to test API key:', err)
      setTestResult('error')
      if (err.response?.status === 404) {
        setTestError('Testing not supported for this API key type')
      } else {
        setTestError(
          err.response?.data?.detail || 'Failed to test API key'
        )
      }
    } finally {
      setTesting(false)
    }
  }

  // Helper to get validation CSS classes
  const getValidationClass = () => {
    if (validating) return 'validating'
    if (hasChanged && !isValid) return 'invalid'
    if (hasChanged && isValid) return 'valid'
    if (testResult === 'success') return 'test-success'
    if (testResult === 'error') return 'test-error'
    return ''
  }

  // Format last updated timestamp
  const formatTimestamp = (timestamp: string) => {
    try {
      const date = new Date(timestamp)
      const now = new Date()
      const diffMs = now.getTime() - date.getTime()
      const diffMins = Math.floor(diffMs / 60000)
      const diffHours = Math.floor(diffMs / 3600000)
      const diffDays = Math.floor(diffMs / 86400000)

      if (diffMins < 1) return 'just now'
      if (diffMins < 60) return `${diffMins}m ago`
      if (diffHours < 24) return `${diffHours}h ago`
      if (diffDays < 7) return `${diffDays}d ago`
      return date.toLocaleDateString()
    } catch {
      return 'Unknown'
    }
  }

  const validationClass = getValidationClass()

  return (
    <div className="api-key-input">
      <div className="api-key-header">
        <div className="api-key-info">
          <label htmlFor={`api-key-${setting.key}`} className="api-key-name">
            {setting.name}
          </label>
          {setting.description && (
            <p className="api-key-description">{setting.description}</p>
          )}
        </div>
        {/* @ts-ignore - TypeScript doesn't know about last_modified_at, but backend provides it */}
        {setting.last_modified_at && (
          <div className="api-key-timestamp">
            Last updated: {formatTimestamp(String(setting.last_modified_at))}
          </div>
        )}
      </div>

      <div className="api-key-control">
        <div className="input-with-validation">
          <div className="password-input-wrapper">
            <input
              id={`api-key-${setting.key}`}
              type={showPassword ? 'text' : 'password'}
              value={currentValue}
              onChange={handleChange}
              className={`api-key-input-field ${validationClass}`}
              placeholder="sk-ant-..."
              disabled={saving || testing}
            />
            <button
              type="button"
              className="password-toggle"
              onClick={() => setShowPassword(!showPassword)}
              aria-label={showPassword ? 'Hide API key' : 'Show API key'}
              disabled={saving || testing}
            >
              {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
            </button>
          </div>
          {validating && (
            <span className="validation-spinner" data-testid="validation-spinner">
              <Loader2 size={16} className="spinner-icon" />
            </span>
          )}
        </div>

        <div className="api-key-actions">
          <button
            className="api-key-button test-button"
            onClick={handleTest}
            disabled={testing || saving || !currentValue || currentValue === '********'}
          >
            {testing ? (
              <>
                <Loader2 size={14} className="spinner-icon" />
                Testing...
              </>
            ) : (
              'Test Key'
            )}
          </button>

          <button
            className="api-key-button save-button"
            onClick={handleSave}
            disabled={!canSave}
          >
            {saving ? 'Saving...' : 'Save'}
          </button>

          {hasDefaultChanged && setting.value !== '********' && (
            <button
              className="api-key-button reset-button"
              onClick={handleReset}
              disabled={saving || testing}
            >
              Reset
            </button>
          )}
        </div>
      </div>

      {/* Test result feedback */}
      {testResult === 'success' && (
        <div className="test-result success">
          <CheckCircle size={16} />
          <span>API key is valid and working</span>
        </div>
      )}

      {testResult === 'error' && testError && (
        <div className="test-result error">
          <XCircle size={16} />
          <span>{testError}</span>
        </div>
      )}

      {/* Validation error message */}
      {validationError && hasChanged && !testError && (
        <div className="validation-error">
          {validationError}
        </div>
      )}

      {/* General error message */}
      {error && (
        <div className="api-key-error">
          {error}
        </div>
      )}
    </div>
  )
}

export default ApiKeyInput
