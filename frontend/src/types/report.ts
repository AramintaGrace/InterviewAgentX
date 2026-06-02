export interface InterviewReport {
  id: string
  interviewSessionId: string
  reportJson: ReportData
  agentModel: string
  tokensUsed?: number
  processingMs?: number
  createdAt: string
  updatedAt: string
}

export interface ReportData {
  overallScore: number
  dimensionScores: Record<string, number | null>
  questionReviews: QuestionReview[]
  strengths: string[]
  weaknesses: string[]
  hiringRecommendation: HiringRecommendation
  detailedFeedback: string
}

export interface QuestionReview {
  questionText: string
  sourceType: string
  evalMode: string
  score: number
  keyFeedback: string
}

export type HiringRecommendation =
  | 'strongly_recommend'
  | 'recommend'
  | 'consider'
  | 'not_recommend'

export interface InterviewRecord {
  candidateId: string
  candidateName: string
  candidateEmail?: string
  resumeId?: string
  sessionId: string
  interviewDate: string
  overallScore?: number
  recommendation?: string
}
