// 后端 API 返回 snake_case

export interface InterviewReport {
  id: string
  interview_session_id: string
  report_json: ReportData
  agent_model: string
  tokens_used?: number
  processing_ms?: number
  created_at: string
  updated_at: string
}

export interface ReportData {
  overall_score: number
  dimension_scores: Record<string, number | null>
  question_reviews: QuestionReview[]
  strengths: string[]
  weaknesses: string[]
  hiring_recommendation: HiringRecommendation
  detailed_feedback: string
}

export interface QuestionReview {
  question_text: string
  source_type: string
  eval_mode: string
  score: number
  key_feedback: string
}

export type HiringRecommendation =
  | 'strongly_recommend'
  | 'recommend'
  | 'consider'
  | 'not_recommend'

// 面试记录列表项
export interface InterviewRecord {
  candidate_id: string
  candidate_name: string
  candidate_email?: string
  candidate_phone?: string
  candidate_role?: string
  resume_id?: string
  session_id: string
  interview_date: string
  overall_score?: number
  recommendation?: string
}

// 候选人完整档案
export interface CandidateDossier {
  candidate: CandidateInfo
  resumes: DossierResume[]
  interviews: DossierInterview[]
}

export interface CandidateInfo {
  id: string
  name: string
  email?: string
  phone?: string
  current_role?: string
  years_of_exp?: number
  notes?: string
  created_at: string
}

export interface DossierResume {
  id: string
  file_name: string
  file_size_bytes: number
  mime_type: string
  ocr_status: string
  ocr_raw_text?: string
  ocr_error_msg?: string
  parsed_data?: Record<string, any>
  file_url?: string
  created_at?: string
  analysis?: DossierAnalysis | null
}

export interface DossierAnalysis {
  id: string
  analysis_json: Record<string, any>
  agent_model: string
  tokens_used?: number
  processing_ms?: number
  created_at?: string
}

export interface DossierInterview {
  session_id: string
  status: string
  question_source?: string
  total_questions: number
  completed_questions: number
  total_score?: number
  started_at?: string
  ended_at?: string
  created_at?: string
  report?: DossierReport | null
}

export interface DossierReport {
  id: string
  report_json: ReportData
  agent_model: string
  tokens_used?: number
  processing_ms?: number
  created_at?: string
}
