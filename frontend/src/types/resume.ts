// 注意：后端 API 返回 snake_case 字段名，前端类型与之保持一致

export interface Candidate {
  id: string
  name: string
  email?: string
  phone?: string
  current_role?: string
  years_of_exp?: number
  notes?: string
  created_at: string
}

export interface ResumeUploadResponse {
  id: string
  file_name: string
  file_size_bytes: number
  mime_type: string
  ocr_status: string
  ocr_error_msg?: string
  ocr_raw_text?: string
  created_at: string
}

export interface ResumeInfo {
  id: string
  candidate_id?: string
  file_name: string
  file_size_bytes: number
  mime_type: string
  ocr_status: string
  ocr_raw_text?: string
  ocr_error_msg?: string
  parsed_data?: ParsedResumeData
  created_at: string
  updated_at: string
}

export interface ParsedResumeData {
  name?: string
  email?: string
  phone?: string
  education?: Education[]
  experience?: WorkExperience[]
  skills?: string[]
  projects?: Project[]
}

export interface Education {
  school: string
  degree: string
  year: number
}

export interface WorkExperience {
  company: string
  role: string
  duration: string
  description: string
}

export interface Project {
  name: string
  description: string
  tech_stack: string[]
}

export interface ResumeAnalysis {
  id: string
  resume_id: string
  agent_model: string
  analysis_json: ResumeAnalysisData
  tokens_used?: number
  processing_ms?: number
  created_at: string
}

export interface ResumeAnalysisData {
  overall_assessment: string
  strengths: string[]
  weaknesses: string[]
  skill_match: Record<string, number>
  experience_relevance_score: number
  project_highlights: Array<{ project: string; depth_analysis: string }>
  suggested_questions: string[]
  red_flags: string[]
  tokens_used: number
  processing_ms: number
}
