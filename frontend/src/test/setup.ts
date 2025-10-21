// ABOUTME: Test setup for Vitest with React Testing Library
// ABOUTME: Configures global test utilities and mocks

import '@testing-library/jest-dom'
import { vi } from 'vitest'

// Mock environment variables
vi.mock('import.meta', () => ({
  env: {
    VITE_API_URL: 'http://localhost:8000'
  }
}))