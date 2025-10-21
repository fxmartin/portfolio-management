// ABOUTME: Unit tests for the Toast notification component
// ABOUTME: Tests rendering, dismissal, auto-dismiss, and accessibility

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import Toast, { ToastMessage } from './Toast';

describe('Toast Component', () => {
  const mockOnDismiss = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('should render nothing when no toasts', () => {
    const { container } = render(
      <Toast toasts={[]} onDismiss={mockOnDismiss} />
    );
    expect(container.firstChild).toBeNull();
  });

  it('should render success toast with correct styling', () => {
    const toasts: ToastMessage[] = [
      {
        id: '1',
        type: 'success',
        title: 'Success!',
        message: 'Operation completed',
      },
    ];

    render(<Toast toasts={toasts} onDismiss={mockOnDismiss} />);

    expect(screen.getByRole('alert')).toBeInTheDocument();
    expect(screen.getByText('Success!')).toBeInTheDocument();
    expect(screen.getByText('Operation completed')).toBeInTheDocument();
    expect(screen.getByText('✓')).toBeInTheDocument();
  });

  it('should render error toast with correct styling', () => {
    const toasts: ToastMessage[] = [
      {
        id: '1',
        type: 'error',
        title: 'Error!',
        message: 'Something went wrong',
      },
    ];

    render(<Toast toasts={toasts} onDismiss={mockOnDismiss} />);

    expect(screen.getByText('Error!')).toBeInTheDocument();
    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
    expect(screen.getByText('✕')).toBeInTheDocument();
  });

  it('should render warning toast with correct icon', () => {
    const toasts: ToastMessage[] = [
      {
        id: '1',
        type: 'warning',
        title: 'Warning!',
      },
    ];

    render(<Toast toasts={toasts} onDismiss={mockOnDismiss} />);

    expect(screen.getByText('⚠')).toBeInTheDocument();
  });

  it('should render info toast with correct icon', () => {
    const toasts: ToastMessage[] = [
      {
        id: '1',
        type: 'info',
        title: 'Info',
      },
    ];

    render(<Toast toasts={toasts} onDismiss={mockOnDismiss} />);

    expect(screen.getByText('ℹ')).toBeInTheDocument();
  });

  it('should render multiple toasts', () => {
    const toasts: ToastMessage[] = [
      { id: '1', type: 'success', title: 'First' },
      { id: '2', type: 'error', title: 'Second' },
      { id: '3', type: 'info', title: 'Third' },
    ];

    render(<Toast toasts={toasts} onDismiss={mockOnDismiss} />);

    expect(screen.getByText('First')).toBeInTheDocument();
    expect(screen.getByText('Second')).toBeInTheDocument();
    expect(screen.getByText('Third')).toBeInTheDocument();
    expect(screen.getAllByRole('alert')).toHaveLength(3);
  });

  it('should call onDismiss when dismiss button clicked', () => {
    const toasts: ToastMessage[] = [
      { id: '1', type: 'success', title: 'Test' },
    ];

    render(<Toast toasts={toasts} onDismiss={mockOnDismiss} />);

    const dismissButton = screen.getByLabelText('Dismiss notification');
    fireEvent.click(dismissButton);

    expect(mockOnDismiss).toHaveBeenCalledWith('1');
  });

  it('should auto-dismiss after default duration', () => {
    const toasts: ToastMessage[] = [
      { id: '1', type: 'success', title: 'Auto dismiss' },
    ];

    render(<Toast toasts={toasts} onDismiss={mockOnDismiss} />);

    expect(mockOnDismiss).not.toHaveBeenCalled();

    vi.advanceTimersByTime(5000);

    expect(mockOnDismiss).toHaveBeenCalledWith('1');
  });

  it('should auto-dismiss after custom duration', () => {
    const toasts: ToastMessage[] = [
      {
        id: '1',
        type: 'success',
        title: 'Custom duration',
        duration: 2000,
      },
    ];

    render(<Toast toasts={toasts} onDismiss={mockOnDismiss} />);

    vi.advanceTimersByTime(1999);
    expect(mockOnDismiss).not.toHaveBeenCalled();

    vi.advanceTimersByTime(1);
    expect(mockOnDismiss).toHaveBeenCalledWith('1');
  });

  it('should not auto-dismiss when duration is 0', () => {
    const toasts: ToastMessage[] = [
      {
        id: '1',
        type: 'error',
        title: 'Persistent toast',
        duration: 0,
      },
    ];

    render(<Toast toasts={toasts} onDismiss={mockOnDismiss} />);

    vi.advanceTimersByTime(10000);

    expect(mockOnDismiss).not.toHaveBeenCalled();
  });

  it('should have proper ARIA labels', () => {
    const toasts: ToastMessage[] = [
      {
        id: '1',
        type: 'success',
        title: 'Accessible',
        message: 'This is accessible',
      },
    ];

    render(<Toast toasts={toasts} onDismiss={mockOnDismiss} />);

    const alert = screen.getByRole('alert');
    expect(alert).toHaveAttribute(
      'aria-label',
      'success notification: Accessible. This is accessible'
    );
  });

  it('should have ARIA live region', () => {
    const toasts: ToastMessage[] = [
      { id: '1', type: 'info', title: 'Live update' },
    ];

    render(<Toast toasts={toasts} onDismiss={mockOnDismiss} />);

    const region = screen.getByRole('region');
    expect(region).toHaveAttribute('aria-live', 'polite');
    expect(region).toHaveAttribute('aria-label', 'Notifications');
  });

  it('should render toast without message', () => {
    const toasts: ToastMessage[] = [
      { id: '1', type: 'success', title: 'Title only' },
    ];

    render(<Toast toasts={toasts} onDismiss={mockOnDismiss} />);

    expect(screen.getByText('Title only')).toBeInTheDocument();
    expect(screen.queryByText('undefined')).not.toBeInTheDocument();
  });
});