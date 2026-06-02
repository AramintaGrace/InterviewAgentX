// 后端 API 返回 snake_case

export interface KBCategory {
  id: string
  parent_id?: string
  name: string
  description?: string
  sort_order: number
  created_at: string
  updated_at: string
}

export interface KBCategoryCreate {
  name: string
  parent_id?: string
  description?: string
  sort_order?: number
}

export interface KBItem {
  id: string
  category_id?: string
  title?: string
  question: string
  answer: string
  tags?: string[]
  difficulty: 'easy' | 'medium' | 'hard'
  embedding_model: string
  embedding_dim: number
  is_vectorized: boolean
  needs_revectorize: boolean
  version: number
  created_at: string
  updated_at: string
}

export type VectorizationStatus = 'vectorized' | 'not_vectorized' | 'needs_revectorize'

export interface BatchOperationRequest {
  item_ids: string[]
  category_id?: string
}

export interface KBItemCreate {
  category_id?: string
  title?: string
  question: string
  answer: string
  tags?: string[]
  difficulty?: 'easy' | 'medium' | 'hard'
}

export interface KBItemUpdate {
  category_id?: string
  title?: string
  question?: string
  answer?: string
  tags?: string[]
  difficulty?: 'easy' | 'medium' | 'hard'
}
