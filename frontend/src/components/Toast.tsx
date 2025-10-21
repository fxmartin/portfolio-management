// ABOUTME: Toast notification component for displaying success/error messages
// ABOUTME: Provides auto-dismiss, manual dismiss, and multiple toast support

import React, { useEffect, useState } from 'react';
import './Toast.css';

export type ToastType = 'success' | 'error' | 'warning' | 'info';

export interface ToastMessage {
  id: string;
  type: ToastType;
  title: string;
  message?: string;
  duration?: number; // milliseconds, 0 for no auto-dismiss
}

interface ToastProps {
  toasts: ToastMessage[];
  onDismiss: (id: string) => void;
}

const Toast: React.FC<ToastProps> = ({ toasts, onDismiss }) => {
  const [visibleToasts, setVisibleToasts] = useState<Set<string>>(new Set());

  useEffect(() => {
    // Track visible toasts and set up auto-dismiss timers
    toasts.forEach(toast => {
      if (!visibleToasts.has(toast.id)) {
        setVisibleToasts(prev => new Set(prev).add(toast.id));

        if (toast.duration !== 0) {
          const duration = toast.duration || 5000;
          const timer = setTimeout(() => {
            onDismiss(toast.id);
          }, duration);

          return () => clearTimeout(timer);
        }
      }
    });
  }, [toasts, onDismiss, visibleToasts]);

  const getIcon = (type: ToastType) => {
    switch (type) {
      case 'success':
        return '✓';
      case 'error':
        return '✕';
      case 'warning':
        return '⚠';
      case 'info':
        return 'ℹ';
      default:
        return '';
    }
  };

  const getAriaLabel = (toast: ToastMessage) => {
    return `${toast.type} notification: ${toast.title}. ${toast.message || ''}`;
  };

  if (toasts.length === 0) return null;

  return (
    <div
      className="toast-container"
      role="region"
      aria-label="Notifications"
      aria-live="polite"
    >
      {toasts.map(toast => (
        <div
          key={toast.id}
          className={`toast toast-${toast.type}`}
          role="alert"
          aria-label={getAriaLabel(toast)}
        >
          <div className="toast-icon">
            <span aria-hidden="true">{getIcon(toast.type)}</span>
          </div>
          <div className="toast-content">
            <div className="toast-title">{toast.title}</div>
            {toast.message && (
              <div className="toast-message">{toast.message}</div>
            )}
          </div>
          <button
            className="toast-dismiss"
            onClick={() => onDismiss(toast.id)}
            aria-label="Dismiss notification"
          >
            <span aria-hidden="true">×</span>
          </button>
        </div>
      ))}
    </div>
  );
};

export default Toast;