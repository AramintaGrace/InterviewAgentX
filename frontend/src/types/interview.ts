// 注意：后端 API 返回 snake_case，类型声明保持一致

export type QuestionSource = 'resume' | 'knowledge_base' | 'mixed'
export type QuestionSourceType = 'resume_experience' | 'resume_project' | 'knowledge_base'
export type InterviewStatus = 'created' | 'in_progress' | 'paused' | 'completed' | 'cancelled'

export interface InterviewSession {
  id: string
  candidate_id?: string
  resume_id?: string
  langgraph_thread_id: string
  status: InterviewStatus
  question_source?: QuestionSource
  total_questions: number
  completed_questions: number
  total_score?: number
  started_at?: string
  ended_at?: string
  created_at: string
  updated_at: string
}

export interface InterviewSessionCreate {
  candidate_id: string
  resume_id: string
  question_source: QuestionSource
  total_questions: number
}

export interface GeneratedQuestion {
  id: string
  interview_session_id: string
  source_type: QuestionSourceType
  source_kb_item_id?: string
  source_resume_context?: string
  question_text: string
  ai_reference_answer?: string
  question_order: number
  status: string
  created_at: string
}

export interface AnswerSubmit {
  question_id: string
  transcript_text: string
  audio_minio_key?: string
  audio_duration_sec?: number
}

export interface Answer {
  id: string
  question_id: string
  transcript_text: string
  audio_minio_key?: string
  audio_duration_sec?: number
  created_at: string
}

export interface AnswerAnalysis {
  id: string
  answer_id: string
  question_id: string
  eval_mode: 'rag_hybrid' | 'llm_judge'
  analysis_json: AnswerAnalysisData
  agent_model: string
  tokens_used?: number
  processing_ms?: number
  created_at: string
}

export interface AnswerAnalysisData {
  overall_score: number
  assessment: string
  strengths: string[]
  areas_for_improvement: string[]
  // LLM-as-a-Judge
  accuracy_score?: number
  accuracy_reasoning?: string
  completeness_score?: number
  completeness_reasoning?: string
  clarity_score?: number
  clarity_reasoning?: string
  technical_depth_score?: number
  technical_depth_reasoning?: string
  authenticity_flag?: string
  // RAG hybrid
  vector_similarity?: number
  covered_points?: string[]
  missing_points?: string[]
  retrieved_chunks?: Array<{ id: string; similarity: number; text: string }>
}
