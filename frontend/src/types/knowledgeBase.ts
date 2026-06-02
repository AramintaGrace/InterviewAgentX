export interface KBCategory {
  id: string
  parentId?: string
  name: string
  description?: string
  sortOrder: number
  createdAt: string
  updatedAt: string
}

export interface KBItem {
  id: string
  categoryId?: string
  question: string
  answer: string
  tags?: string[]
  difficulty: 'easy' | 'medium' | 'hard'
  embeddingModel: string
  embeddingDim: number
  isVectorized: boolean
  version: number
  createdAt: string
  updatedAt: string
}

export interface KBItemCreate {
  categoryId?: string
  question: string
  answer: string
  tags?: string[]
  difficulty?: 'easy' | 'medium' | 'hard'
}

export interface KBItemUpdate {
  categoryId?: string
  question?: string
  answer?: string
  tags?: string[]
  difficulty?: 'easy' | 'medium' | 'hard'
}
