export type QuestionSource = 'resume' | 'knowledge_base' | 'mixed'
export type QuestionSourceType = 'resume_experience' | 'resume_project' | 'knowledge_base'
export type InterviewStatus = 'created' | 'in_progress' | 'paused' | 'completed' | 'cancelled'

export interface InterviewSession {
  id: string
  candidateId?: string
  resumeId?: string
  langgraphThreadId: string
  status: InterviewStatus
  questionSource?: QuestionSource
  totalQuestions: number
  completedQuestions: number
  totalScore?: number
  startedAt?: string
  endedAt?: string
  createdAt: string
  updatedAt: string
}

export interface InterviewSessionCreate {
  candidateId: string
  resumeId: string
  questionSource: QuestionSource
  totalQuestions: number
}

export interface GeneratedQuestion {
  id: string
  interviewSessionId: string
  sourceType: QuestionSourceType
  sourceKbItemId?: string
  sourceResumeContext?: string
  questionText: string
  aiReferenceAnswer?: string
  questionOrder: number
  status: string
  createdAt: string
}

export interface AnswerSubmit {
  questionId: string
  transcriptText: string
  audioMinioKey?: string
  audioDurationSec?: number
}

export interface Answer {
  id: string
  questionId: string
  transcriptText: string
  audioMinioKey?: string
  audioDurationSec?: number
  createdAt: string
}

export interface AnswerAnalysis {
  id: string
  answerId: string
  questionId: string
  evalMode: 'rag_hybrid' | 'llm_judge'
  analysisJson: AnswerAnalysisData
  agentModel: string
  tokensUsed?: number
  processingMs?: number
  createdAt: string
}

export interface AnswerAnalysisData {
  overallScore: number
  assessment: string
  strengths: string[]
  areasForImprovement: string[]
  // LLM-as-a-Judge
  accuracyScore?: number
  accuracyReasoning?: string
  completenessScore?: number
  completenessReasoning?: string
  clarityScore?: number
  clarityReasoning?: string
  technicalDepthScore?: number
  technicalDepthReasoning?: string
  authenticityFlag?: string
  // RAG hybrid
  vectorSimilarity?: number
  coveredPoints?: string[]
  missingPoints?: string[]
  retrievedChunks?: Array<{ id: string; similarity: number; text: string }>
}
