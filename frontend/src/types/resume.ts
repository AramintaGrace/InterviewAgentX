export interface Candidate {
  id: string
  name: string
  email?: string
  phone?: string
  currentRole?: string
  yearsOfExp?: number
  notes?: string
  createdAt: string
}

export interface ResumeUploadResponse {
  id: string
  fileName: string
  fileSizeBytes: number
  mimeType: string
  ocrStatus: string
  createdAt: string
}

export interface ResumeInfo {
  id: string
  candidateId?: string
  fileName: string
  fileSizeBytes: number
  mimeType: string
  ocrStatus: string
  ocrRawText?: string
  ocrErrorMsg?: string
  parsedData?: ParsedResumeData
  createdAt: string
  updatedAt: string
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
  techStack: string[]
}

export interface ResumeAnalysis {
  id: string
  resumeId: string
  agentModel: string
  analysisJson: ResumeAnalysisData
  tokensUsed?: number
  processingMs?: number
  createdAt: string
}

export interface ResumeAnalysisData {
  overallAssessment: string
  strengths: string[]
  weaknesses: string[]
  skillMatch: Record<string, number>
  experienceRelevanceScore: number
  projectHighlights: Array<{ project: string; depthAnalysis: string }>
  suggestedQuestions: string[]
  redFlags: string[]
  tokensUsed: number
  processingMs: number
}
