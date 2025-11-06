// ABOUTME: Unit tests for promptService API client
// ABOUTME: Tests all CRUD operations and error handling with mocked axios

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import axios from 'axios'
import { promptService } from './promptService'
import type {
  PromptCreate,
  PromptUpdate,
  PromptResponse,
  PromptListResponse
} from '../types/prompt.types'

// Mock axios
vi.mock('axios')

describe('promptService', () => {
  const mockAxios = vi.mocked(axios)
  const API_URL = 'http://localhost:8000'

  const mockPromptResponse: PromptResponse = {
    id: 1,
    name: 'global_market_analysis',
    category: 'global',
    prompt_text: 'Analyze the market with {{symbol}} and {{timeframe}}',
    template_variables: { symbol: 'string', timeframe: 'string' },
    version: 1,
    is_active: true,
    created_at: '2025-11-05T10:00:00Z',
    updated_at: '2025-11-05T10:00:00Z'
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('listPrompts', () => {
    it('should fetch all prompts with default parameters', async () => {
      const mockListResponse: PromptListResponse = {
        prompts: [mockPromptResponse],
        total: 1,
        skip: 0,
        limit: 100
      }

      mockAxios.get.mockResolvedValueOnce({ data: mockListResponse })

      const result = await promptService.listPrompts()

      expect(mockAxios.get).toHaveBeenCalledWith(
        `${API_URL}/api/prompts`,
        {
          params: {
            category: undefined,
            active_only: true,
            skip: 0,
            limit: 100
          }
        }
      )
      expect(result).toEqual(mockListResponse)
    })

    it('should filter prompts by category', async () => {
      const mockListResponse: PromptListResponse = {
        prompts: [mockPromptResponse],
        total: 1,
        skip: 0,
        limit: 100
      }

      mockAxios.get.mockResolvedValueOnce({ data: mockListResponse })

      await promptService.listPrompts('global')

      expect(mockAxios.get).toHaveBeenCalledWith(
        `${API_URL}/api/prompts`,
        {
          params: {
            category: 'global',
            active_only: true,
            skip: 0,
            limit: 100
          }
        }
      )
    })

    it('should include inactive prompts when activeOnly is false', async () => {
      const mockListResponse: PromptListResponse = {
        prompts: [mockPromptResponse],
        total: 1,
        skip: 0,
        limit: 100
      }

      mockAxios.get.mockResolvedValueOnce({ data: mockListResponse })

      await promptService.listPrompts(undefined, false)

      expect(mockAxios.get).toHaveBeenCalledWith(
        `${API_URL}/api/prompts`,
        {
          params: {
            category: undefined,
            active_only: false,
            skip: 0,
            limit: 100
          }
        }
      )
    })

    it('should handle pagination parameters', async () => {
      const mockListResponse: PromptListResponse = {
        prompts: [mockPromptResponse],
        total: 50,
        skip: 10,
        limit: 20
      }

      mockAxios.get.mockResolvedValueOnce({ data: mockListResponse })

      await promptService.listPrompts(undefined, true, 10, 20)

      expect(mockAxios.get).toHaveBeenCalledWith(
        `${API_URL}/api/prompts`,
        {
          params: {
            category: undefined,
            active_only: true,
            skip: 10,
            limit: 20
          }
        }
      )
    })

    it('should handle API errors', async () => {
      mockAxios.get.mockRejectedValueOnce(new Error('Network error'))

      await expect(promptService.listPrompts()).rejects.toThrow('Network error')
    })
  })

  describe('getPrompt', () => {
    it('should fetch a prompt by ID', async () => {
      mockAxios.get.mockResolvedValueOnce({ data: mockPromptResponse })

      const result = await promptService.getPrompt(1)

      expect(mockAxios.get).toHaveBeenCalledWith(`${API_URL}/api/prompts/1`)
      expect(result).toEqual(mockPromptResponse)
    })

    it('should handle 404 errors', async () => {
      mockAxios.get.mockRejectedValueOnce({
        response: { status: 404, data: { detail: 'Prompt not found' } }
      })

      await expect(promptService.getPrompt(999)).rejects.toMatchObject({
        response: { status: 404 }
      })
    })
  })

  describe('getPromptByName', () => {
    it('should fetch a prompt by name', async () => {
      mockAxios.get.mockResolvedValueOnce({ data: mockPromptResponse })

      const result = await promptService.getPromptByName('global_market_analysis')

      expect(mockAxios.get).toHaveBeenCalledWith(
        `${API_URL}/api/prompts/name/global_market_analysis`
      )
      expect(result).toEqual(mockPromptResponse)
    })

    it('should handle URL encoding for names with spaces', async () => {
      mockAxios.get.mockResolvedValueOnce({ data: mockPromptResponse })

      await promptService.getPromptByName('market analysis')

      expect(mockAxios.get).toHaveBeenCalledWith(
        `${API_URL}/api/prompts/name/market analysis`
      )
    })
  })

  describe('createPrompt', () => {
    it('should create a new prompt', async () => {
      const createData: PromptCreate = {
        name: 'test_prompt',
        category: 'position',
        prompt_text: 'Test prompt with {{variable}}',
        template_variables: { variable: 'string' }
      }

      mockAxios.post.mockResolvedValueOnce({ data: mockPromptResponse })

      const result = await promptService.createPrompt(createData)

      expect(mockAxios.post).toHaveBeenCalledWith(
        `${API_URL}/api/prompts`,
        createData
      )
      expect(result).toEqual(mockPromptResponse)
    })

    it('should handle validation errors', async () => {
      const invalidData: PromptCreate = {
        name: '',
        category: 'global',
        prompt_text: 'short',
        template_variables: {}
      }

      mockAxios.post.mockRejectedValueOnce({
        response: {
          status: 400,
          data: { detail: 'Name is required' }
        }
      })

      await expect(promptService.createPrompt(invalidData)).rejects.toMatchObject({
        response: { status: 400 }
      })
    })
  })

  describe('updatePrompt', () => {
    it('should update an existing prompt', async () => {
      const updateData: PromptUpdate = {
        prompt_text: 'Updated prompt text',
        change_reason: 'Improved clarity'
      }

      const updatedPrompt = {
        ...mockPromptResponse,
        prompt_text: 'Updated prompt text',
        version: 2
      }

      mockAxios.put.mockResolvedValueOnce({ data: updatedPrompt })

      const result = await promptService.updatePrompt(1, updateData)

      expect(mockAxios.put).toHaveBeenCalledWith(
        `${API_URL}/api/prompts/1`,
        updateData
      )
      expect(result).toEqual(updatedPrompt)
    })

    it('should handle partial updates', async () => {
      const partialUpdate: PromptUpdate = {
        name: 'new_name'
      }

      mockAxios.put.mockResolvedValueOnce({ data: mockPromptResponse })

      await promptService.updatePrompt(1, partialUpdate)

      expect(mockAxios.put).toHaveBeenCalledWith(
        `${API_URL}/api/prompts/1`,
        partialUpdate
      )
    })

    it('should handle not found errors', async () => {
      mockAxios.put.mockRejectedValueOnce({
        response: { status: 404, data: { detail: 'Prompt not found' } }
      })

      await expect(
        promptService.updatePrompt(999, { name: 'test' })
      ).rejects.toMatchObject({
        response: { status: 404 }
      })
    })
  })

  describe('deletePrompt', () => {
    it('should soft delete a prompt', async () => {
      const successResponse = {
        message: 'Prompt deactivated successfully',
        success: true
      }

      mockAxios.delete.mockResolvedValueOnce({ data: successResponse })

      const result = await promptService.deletePrompt(1)

      expect(mockAxios.delete).toHaveBeenCalledWith(`${API_URL}/api/prompts/1`)
      expect(result).toEqual(successResponse)
    })

    it('should handle deletion errors', async () => {
      mockAxios.delete.mockRejectedValueOnce({
        response: { status: 500, data: { detail: 'Server error' } }
      })

      await expect(promptService.deletePrompt(1)).rejects.toMatchObject({
        response: { status: 500 }
      })
    })
  })

  describe('getVersionHistory', () => {
    it('should fetch version history for a prompt', async () => {
      const mockVersionHistory = {
        versions: [
          {
            id: 1,
            prompt_id: 1,
            version: 2,
            prompt_text: 'Version 2 text',
            changed_by: 'user@example.com',
            changed_at: '2025-11-05T11:00:00Z',
            change_reason: 'Updated for clarity'
          },
          {
            id: 2,
            prompt_id: 1,
            version: 1,
            prompt_text: 'Version 1 text',
            changed_by: null,
            changed_at: '2025-11-05T10:00:00Z',
            change_reason: null
          }
        ],
        total: 2
      }

      mockAxios.get.mockResolvedValueOnce({ data: mockVersionHistory })

      const result = await promptService.getVersionHistory(1)

      expect(mockAxios.get).toHaveBeenCalledWith(
        `${API_URL}/api/prompts/1/versions`
      )
      expect(result).toEqual(mockVersionHistory)
    })

    it('should handle empty version history', async () => {
      const emptyHistory = {
        versions: [],
        total: 0
      }

      mockAxios.get.mockResolvedValueOnce({ data: emptyHistory })

      const result = await promptService.getVersionHistory(1)

      expect(result.versions).toHaveLength(0)
    })
  })

  describe('restoreVersion', () => {
    it('should restore a previous version', async () => {
      const restoredPrompt = {
        ...mockPromptResponse,
        version: 3,
        prompt_text: 'Restored version text'
      }

      mockAxios.post.mockResolvedValueOnce({ data: restoredPrompt })

      const result = await promptService.restoreVersion(1, 1, 'Reverting changes')

      expect(mockAxios.post).toHaveBeenCalledWith(
        `${API_URL}/api/prompts/1/restore/1`,
        { change_reason: 'Reverting changes' }
      )
      expect(result).toEqual(restoredPrompt)
    })

    it('should restore without change reason', async () => {
      mockAxios.post.mockResolvedValueOnce({ data: mockPromptResponse })

      await promptService.restoreVersion(1, 2)

      expect(mockAxios.post).toHaveBeenCalledWith(
        `${API_URL}/api/prompts/1/restore/2`,
        { change_reason: undefined }
      )
    })

    it('should handle invalid version numbers', async () => {
      mockAxios.post.mockRejectedValueOnce({
        response: { status: 404, data: { detail: 'Version not found' } }
      })

      await expect(
        promptService.restoreVersion(1, 999)
      ).rejects.toMatchObject({
        response: { status: 404 }
      })
    })
  })
})
