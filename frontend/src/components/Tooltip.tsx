// ABOUTME: Reusable tooltip component with accessibility features
// ABOUTME: Shows explanatory text on hover/focus with keyboard navigation support

import React, { useState, useRef, useEffect } from 'react'
import './Tooltip.css'

interface TooltipProps {
  content: string
  children: React.ReactElement
  position?: 'top' | 'bottom' | 'left' | 'right'
}

export const Tooltip: React.FC<TooltipProps> = ({
  content,
  children,
  position = 'top'
}) => {
  const [visible, setVisible] = useState(false)
  const [coords, setCoords] = useState({ x: 0, y: 0 })
  const triggerRef = useRef<HTMLSpanElement>(null)
  const tooltipRef = useRef<HTMLDivElement>(null)

  const showTooltip = () => setVisible(true)
  const hideTooltip = () => setVisible(false)

  // Calculate tooltip position relative to trigger element
  useEffect(() => {
    if (visible && triggerRef.current && tooltipRef.current) {
      const triggerRect = triggerRef.current.getBoundingClientRect()
      const tooltipRect = tooltipRef.current.getBoundingClientRect()

      let x = 0
      let y = 0

      switch (position) {
        case 'top':
          x = triggerRect.left + triggerRect.width / 2 - tooltipRect.width / 2
          y = triggerRect.top - tooltipRect.height - 8
          break
        case 'bottom':
          x = triggerRect.left + triggerRect.width / 2 - tooltipRect.width / 2
          y = triggerRect.bottom + 8
          break
        case 'left':
          x = triggerRect.left - tooltipRect.width - 8
          y = triggerRect.top + triggerRect.height / 2 - tooltipRect.height / 2
          break
        case 'right':
          x = triggerRect.right + 8
          y = triggerRect.top + triggerRect.height / 2 - tooltipRect.height / 2
          break
      }

      // Ensure tooltip stays within viewport
      const padding = 8
      if (x < padding) x = padding
      if (x + tooltipRect.width > window.innerWidth - padding) {
        x = window.innerWidth - tooltipRect.width - padding
      }
      if (y < padding) y = padding
      if (y + tooltipRect.height > window.innerHeight - padding) {
        y = window.innerHeight - tooltipRect.height - padding
      }

      setCoords({ x, y })
    }
  }, [visible, position])

  return (
    <>
      <span
        ref={triggerRef}
        className="tooltip-trigger"
        onMouseEnter={showTooltip}
        onMouseLeave={hideTooltip}
        onFocus={showTooltip}
        onBlur={hideTooltip}
        tabIndex={0}
        aria-describedby={visible ? 'tooltip' : undefined}
      >
        {children}
      </span>
      {visible && (
        <div
          ref={tooltipRef}
          id="tooltip"
          className={`tooltip tooltip-${position}`}
          role="tooltip"
          style={{
            position: 'fixed',
            left: `${coords.x}px`,
            top: `${coords.y}px`,
          }}
        >
          {content}
        </div>
      )}
    </>
  )
}

export default Tooltip
