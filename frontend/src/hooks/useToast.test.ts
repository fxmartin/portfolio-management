// ABOUTME: Unit tests for the useToast custom hook
// ABOUTME: Tests toast management, different types, and clearing functionality

import { describe, it, expect, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import useToast from './useToast';

describe('useToast Hook', () => {
  it('should initialize with empty toasts array', () => {
    const { result } = renderHook(() => useToast());

    expect(result.current.toasts).toEqual([]);
  });

  it('should show success toast', () => {
    const { result } = renderHook(() => useToast());

    act(() => {
      result.current.showSuccess('Success!', 'Operation completed');
    });

    expect(result.current.toasts).toHaveLength(1);
    expect(result.current.toasts[0]).toMatchObject({
      type: 'success',
      title: 'Success!',
      message: 'Operation completed',
      duration: 5000,
    });
    expect(result.current.toasts[0].id).toBeDefined();
  });

  it('should show error toast', () => {
    const { result } = renderHook(() => useToast());

    act(() => {
      result.current.showError('Error!', 'Something went wrong');
    });

    expect(result.current.toasts).toHaveLength(1);
    expect(result.current.toasts[0]).toMatchObject({
      type: 'error',
      title: 'Error!',
      message: 'Something went wrong',
      duration: 5000,
    });
  });

  it('should show warning toast', () => {
    const { result } = renderHook(() => useToast());

    act(() => {
      result.current.showWarning('Warning!', 'Be careful');
    });

    expect(result.current.toasts).toHaveLength(1);
    expect(result.current.toasts[0]).toMatchObject({
      type: 'warning',
      title: 'Warning!',
      message: 'Be careful',
      duration: 5000,
    });
  });

  it('should show info toast', () => {
    const { result } = renderHook(() => useToast());

    act(() => {
      result.current.showInfo('Info', 'For your information');
    });

    expect(result.current.toasts).toHaveLength(1);
    expect(result.current.toasts[0]).toMatchObject({
      type: 'info',
      title: 'Info',
      message: 'For your information',
      duration: 5000,
    });
  });

  it('should show multiple toasts', () => {
    const { result } = renderHook(() => useToast());

    act(() => {
      result.current.showSuccess('First');
      result.current.showError('Second');
      result.current.showWarning('Third');
    });

    expect(result.current.toasts).toHaveLength(3);
    expect(result.current.toasts[0].title).toBe('First');
    expect(result.current.toasts[1].title).toBe('Second');
    expect(result.current.toasts[2].title).toBe('Third');
  });

  it('should dismiss specific toast', () => {
    const { result } = renderHook(() => useToast());

    let toastId: string;
    act(() => {
      result.current.showSuccess('First');
      toastId = result.current.showError('Second');
      result.current.showWarning('Third');
    });

    expect(result.current.toasts).toHaveLength(3);

    act(() => {
      result.current.dismissToast(toastId);
    });

    expect(result.current.toasts).toHaveLength(2);
    expect(result.current.toasts.find(t => t.id === toastId)).toBeUndefined();
    expect(result.current.toasts[0].title).toBe('First');
    expect(result.current.toasts[1].title).toBe('Third');
  });

  it('should clear all toasts', () => {
    const { result } = renderHook(() => useToast());

    act(() => {
      result.current.showSuccess('First');
      result.current.showError('Second');
      result.current.showWarning('Third');
    });

    expect(result.current.toasts).toHaveLength(3);

    act(() => {
      result.current.clearAll();
    });

    expect(result.current.toasts).toHaveLength(0);
  });

  it('should show toast without message', () => {
    const { result } = renderHook(() => useToast());

    act(() => {
      result.current.showSuccess('Title only');
    });

    expect(result.current.toasts[0]).toMatchObject({
      type: 'success',
      title: 'Title only',
      message: undefined,
      duration: 5000,
    });
  });

  it('should show toast with custom duration', () => {
    const { result } = renderHook(() => useToast());

    act(() => {
      result.current.showError('Error', 'Message', 10000);
    });

    expect(result.current.toasts[0].duration).toBe(10000);
  });

  it('should show toast with 0 duration (no auto-dismiss)', () => {
    const { result } = renderHook(() => useToast());

    act(() => {
      result.current.showError('Persistent', 'Will not auto-dismiss', 0);
    });

    expect(result.current.toasts[0].duration).toBe(0);
  });

  it('should generate unique IDs for toasts', () => {
    const { result } = renderHook(() => useToast());

    act(() => {
      result.current.showSuccess('First');
      result.current.showSuccess('Second');
      result.current.showSuccess('Third');
    });

    const ids = result.current.toasts.map(t => t.id);
    const uniqueIds = new Set(ids);
    expect(uniqueIds.size).toBe(3);
  });

  it('should return toast ID when showing toast', () => {
    const { result } = renderHook(() => useToast());

    let id1: string;
    let id2: string;

    act(() => {
      id1 = result.current.showSuccess('Test');
      id2 = result.current.showError('Test 2');
    });

    expect(result.current.toasts.find(t => t.id === id1)).toBeDefined();
    expect(result.current.toasts.find(t => t.id === id2)).toBeDefined();
  });

  it('should handle dismissing non-existent toast', () => {
    const { result } = renderHook(() => useToast());

    act(() => {
      result.current.showSuccess('Test');
    });

    expect(result.current.toasts).toHaveLength(1);

    act(() => {
      result.current.dismissToast('non-existent-id');
    });

    expect(result.current.toasts).toHaveLength(1);
  });

  it('should maintain consistent function references', () => {
    const { result, rerender } = renderHook(() => useToast());

    const firstShowSuccess = result.current.showSuccess;
    const firstShowError = result.current.showError;
    const firstDismissToast = result.current.dismissToast;

    rerender();

    expect(result.current.showSuccess).toBe(firstShowSuccess);
    expect(result.current.showError).toBe(firstShowError);
    expect(result.current.dismissToast).toBe(firstDismissToast);
  });
});