// ABOUTME: TypeScript type definitions for Prompt Management API
// ABOUTME: Matches backend prompt_schemas.py from Epic 8 F8.1-002

/**
 * Prompt category enum matching backend
 */
export type PromptCategory = 'global' | 'position' | 'forecast'

/**
 * Request payload for creating a new prompt
 */
export interface PromptCreate {
  name: string // min 1, max 100 chars
  category: PromptCategory
  prompt_text: string // min 10 chars
  template_variables: Record<string, string> // {varName: type}
}

/**
 * Request payload for updating an existing prompt
 */
export interface PromptUpdate {
  name?: string
  category?: PromptCategory
  prompt_text?: string
  template_variables?: Record<string, string>
  change_reason?: string // max 500 chars
}

/**
 * Prompt response from API
 */
export interface PromptResponse {
  id: number
  name: string
  category: PromptCategory
  prompt_text: string
  template_variables: Record<string, string>
  version: number
  is_active: boolean
  created_at: string // ISO datetime
  updated_at: string // ISO datetime
}

/**
 * List of prompts with pagination metadata
 */
export interface PromptListResponse {
  prompts: PromptResponse[]
  total: number
  skip: number
  limit: number
}

/**
 * Historical version of a prompt
 */
export interface PromptVersionResponse {
  id: number
  prompt_id: number
  version: number
  prompt_text: string
  changed_by: string | null
  changed_at: string // ISO datetime
  change_reason: string | null
}

/**
 * List of prompt versions with metadata
 */
export interface PromptVersionListResponse {
  versions: PromptVersionResponse[]
  total: number
}

/**
 * Request payload for restoring a previous version
 */
export interface RestoreVersionRequest {
  change_reason?: string
}

/**
 * Generic success response
 */
export interface SuccessResponse {
  message: string
  success: boolean
}
