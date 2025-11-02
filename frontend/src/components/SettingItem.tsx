// ABOUTME: Individual setting item component with input controls, save, and reset functionality
// ABOUTME: Supports text, password, number, select, and checkbox input types with validation

import { useState, useEffect } from 'react'
import { Eye, EyeOff, Loader2 } from 'lucide-react'
import { toast } from 'react-toastify'
import { useSettingValidation } from '../hooks/useSettingValidation'
import type { Setting } from './SettingsCategoryPanel'
import './SettingItem.css'

export interface SettingItemProps {
  setting: Setting
  onUpdate: (key: string, value: string | number | boolean) => Promise<void>
  onReset: (key: string) => Promise<void>
}

export const SettingItem: React.FC<SettingItemProps> = ({
  setting,
  onUpdate,
  onReset
}) => {
  const [currentValue, setCurrentValue] = useState<string | number | boolean>(setting.value)
  const [showPassword, setShowPassword] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Real-time validation hook
  const { isValid, error: validationError, validating } = useSettingValidation(setting.key, currentValue)

  // Update local value when setting prop changes (e.g., after reset)
  useEffect(() => {
    setCurrentValue(setting.value)
  }, [setting.value])

  const hasChanged = currentValue !== setting.value
  const hasDefaultChanged = setting.value !== setting.default_value

  // Save button should be enabled only when:
  // - Value has changed
  // - Not currently saving
  // - Not currently validating
  // - Value is valid
  const canSave = hasChanged && !saving && !validating && isValid

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setError(null)

    if (setting.input_type === 'checkbox') {
      const checkbox = e.target as HTMLInputElement
      setCurrentValue(checkbox.checked)
    } else if (setting.input_type === 'number') {
      const numValue = parseFloat(e.target.value)
      setCurrentValue(isNaN(numValue) ? e.target.value : numValue)
    } else {
      setCurrentValue(e.target.value)
    }
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
      setCurrentValue(setting.value)
      setSaving(false)
    }
  }

  const handleReset = async () => {
    try {
      setSaving(true)
      setError(null)
      await onReset(setting.key)
      setSaving(false)
    } catch (err) {
      console.error('Failed to reset setting:', err)
      setError('Failed to reset setting')
      setSaving(false)
    }
  }

  // Helper to get validation CSS classes
  const getValidationClass = () => {
    if (validating) return 'validating'
    if (hasChanged && !isValid) return 'invalid'
    if (hasChanged && isValid) return 'valid'
    return ''
  }

  const renderInput = () => {
    const validationClass = getValidationClass()

    switch (setting.input_type) {
      case 'text':
        return (
          <div className="input-with-validation">
            <input
              type="text"
              value={currentValue as string}
              onChange={handleChange}
              className={`setting-input ${validationClass}`}
              disabled={saving}
            />
            {validating && (
              <span className="validation-spinner" data-testid="validation-spinner">
                <Loader2 size={16} className="spinner-icon" />
              </span>
            )}
          </div>
        )

      case 'password':
        return (
          <div className="input-with-validation">
            <div className="password-input-wrapper">
              <input
                type={showPassword ? 'text' : 'password'}
                value={currentValue as string}
                onChange={handleChange}
                className={`setting-input password-input ${validationClass}`}
                disabled={saving}
              />
              <button
                type="button"
                className="password-toggle"
                onClick={() => setShowPassword(!showPassword)}
                aria-label={showPassword ? 'Hide password' : 'Show password'}
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
        )

      case 'number':
        return (
          <div className="input-with-validation">
            <input
              type="number"
              value={currentValue as number}
              onChange={handleChange}
              min={setting.min_value}
              max={setting.max_value}
              className={`setting-input ${validationClass}`}
              disabled={saving}
            />
            {validating && (
              <span className="validation-spinner" data-testid="validation-spinner">
                <Loader2 size={16} className="spinner-icon" />
              </span>
            )}
          </div>
        )

      case 'select':
        return (
          <div className="input-with-validation">
            <select
              value={currentValue as string}
              onChange={handleChange}
              className={`setting-input ${validationClass}`}
              disabled={saving}
            >
              {setting.options?.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
            {validating && (
              <span className="validation-spinner" data-testid="validation-spinner">
                <Loader2 size={16} className="spinner-icon" />
              </span>
            )}
          </div>
        )

      case 'checkbox':
        return (
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={currentValue as boolean}
              onChange={handleChange}
              className="setting-checkbox"
              disabled={saving}
            />
            <span className="checkbox-text">Enabled</span>
          </label>
        )

      default:
        return <input type="text" value={String(currentValue)} disabled />
    }
  }

  return (
    <div className="setting-item">
      <div className="setting-header">
        <div className="setting-info">
          <label className="setting-name">{setting.name}</label>
          {setting.description && (
            <p className="setting-description">{setting.description}</p>
          )}
        </div>
      </div>

      <div className="setting-control">
        {renderInput()}

        <div className="setting-actions">
          <button
            className="setting-button save-button"
            onClick={handleSave}
            disabled={!canSave}
          >
            {saving ? 'Saving...' : 'Save'}
          </button>

          {hasDefaultChanged && (
            <button
              className="setting-button reset-button"
              onClick={handleReset}
              disabled={saving}
            >
              Reset
            </button>
          )}
        </div>
      </div>

      {/* Validation error message */}
      {validationError && hasChanged && (
        <div className="validation-error">
          {validationError}
        </div>
      )}

      {/* General error message */}
      {error && (
        <div className="setting-error">
          {error}
        </div>
      )}
    </div>
  )
}

export default SettingItem
