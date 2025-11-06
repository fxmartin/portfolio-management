// ABOUTME: API client service for Prompt Management endpoints
// ABOUTME: Provides methods for CRUD operations and version history management

import axios from 'axios'
import { API_CONFIG } from '../config/app.config'
import type {
  PromptCreate,
  PromptUpdate,
  PromptResponse,
  PromptListResponse,
  PromptVersionListResponse,
  SuccessResponse
} from '../types/prompt.types'

const API_URL = API_CONFIG.BASE_URL

export const promptService = {
  /**
   * List all prompts with optional filtering
   * @param category - Optional category filter
   * @param activeOnly - Show only active prompts (default: true)
   * @param skip - Pagination offset (default: 0)
   * @param limit - Pagination limit (default: 100)
   */
  async listPrompts(
    category?: string,
    activeOnly: boolean = true,
    skip: number = 0,
    limit: number = 100
  ): Promise<PromptListResponse> {
    const response = await axios.get<PromptListResponse>(
      `${API_URL}/api/prompts`,
      {
        params: { category, active_only: activeOnly, skip, limit }
      }
    )
    return response.data
  },

  /**
   * Get a specific prompt by ID
   * @param id - Prompt ID
   */
  async getPrompt(id: number): Promise<PromptResponse> {
    const response = await axios.get<PromptResponse>(
      `${API_URL}/api/prompts/${id}`
    )
    return response.data
  },

  /**
   * Get a specific prompt by name
   * @param name - Prompt name
   */
  async getPromptByName(name: string): Promise<PromptResponse> {
    const response = await axios.get<PromptResponse>(
      `${API_URL}/api/prompts/name/${name}`
    )
    return response.data
  },

  /**
   * Create a new prompt
   * @param data - Prompt creation data
   */
  async createPrompt(data: PromptCreate): Promise<PromptResponse> {
    const response = await axios.post<PromptResponse>(
      `${API_URL}/api/prompts`,
      data
    )
    return response.data
  },

  /**
   * Update an existing prompt
   * @param id - Prompt ID
   * @param data - Prompt update data
   */
  async updatePrompt(id: number, data: PromptUpdate): Promise<PromptResponse> {
    const response = await axios.put<PromptResponse>(
      `${API_URL}/api/prompts/${id}`,
      data
    )
    return response.data
  },

  /**
   * Delete a prompt (soft delete - sets is_active=false)
   * @param id - Prompt ID
   */
  async deletePrompt(id: number): Promise<SuccessResponse> {
    const response = await axios.delete<SuccessResponse>(
      `${API_URL}/api/prompts/${id}`
    )
    return response.data
  },

  /**
   * Get version history for a prompt
   * @param promptId - Prompt ID
   */
  async getVersionHistory(promptId: number): Promise<PromptVersionListResponse> {
    const response = await axios.get<PromptVersionListResponse>(
      `${API_URL}/api/prompts/${promptId}/versions`
    )
    return response.data
  },

  /**
   * Restore a previous version of a prompt
   * @param promptId - Prompt ID
   * @param versionNumber - Version number to restore
   * @param changeReason - Optional reason for restoration
   */
  async restoreVersion(
    promptId: number,
    versionNumber: number,
    changeReason?: string
  ): Promise<PromptResponse> {
    const response = await axios.post<PromptResponse>(
      `${API_URL}/api/prompts/${promptId}/restore/${versionNumber}`,
      { change_reason: changeReason }
    )
    return response.data
  }
}
