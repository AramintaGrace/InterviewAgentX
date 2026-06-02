import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type {
  InterviewSession,
  GeneratedQuestion,
  Answer,
  AnswerAnalysis,
  QuestionSource,
} from '@/types/interview'
import { interviewsApi } from '@/api/interviews'

export const useInterviewStore = defineStore('interview', () => {
  const currentSession = ref<InterviewSession | null>(null)
  const questions = ref<GeneratedQuestion[]>([])
  const answers = ref<Answer[]>([])
  const analyses = ref<AnswerAnalysis[]>([])
  const currentQuestionIndex = ref(0)
  const loading = ref(false)
  const error = ref<string | null>(null)

  const currentQuestion = computed(() =>
    questions.value[currentQuestionIndex.value] || null
  )

  const currentAnalysis = computed(() =>
    analyses.value[currentQuestionIndex.value] || null
  )

  const progress = computed(() => ({
    current: currentQuestionIndex.value + 1,
    total: questions.value.length,
    percentage: questions.value.length
      ? Math.round(((currentQuestionIndex.value + 1) / questions.value.length) * 100)
      : 0,
  }))

  async function createSession(data: {
    candidateId: string
    resumeId: string
    questionSource: QuestionSource
    totalQuestions: number
  }) {
    loading.value = true
    error.value = null
    try {
      const response = await interviewsApi.create({
        candidate_id: data.candidateId,
        resume_id: data.resumeId,
        question_source: data.questionSource,
        total_questions: data.totalQuestions,
      })
      currentSession.value = response.data
      return response.data
    } catch (e: any) {
      error.value = e.message || '创建面试失败'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function startSession(sessionId: string) {
    loading.value = true
    try {
      const response = await interviewsApi.start(sessionId)
      currentSession.value = response.data
    } catch (e: any) {
      error.value = e.message ||'启动面试失败'
    } finally {
      loading.value = false
    }
  }

  async function loadQuestions(sessionId: string) {
    try {
      const response = await interviewsApi.listQuestions(sessionId)
      questions.value = response.data
    } catch (e: any) {
      error.value = '加载题目失败'
    }
  }

  async function submitAnswer(
    sessionId: string,
    questionId: string,
    transcriptText: string,
  ) {
    loading.value = true
    try {
      const response = await interviewsApi.submitAnswer(sessionId, {
        question_id: questionId,
        transcript_text: transcriptText,
      })
      answers.value.push(response.data)
      return response.data
    } catch (e: any) {
      error.value = e.message || '提交答案失败'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function loadAnswerAnalysis(sessionId: string, answerId: string) {
    try {
      const response = await interviewsApi.getAnswerAnalysis(sessionId, answerId)
      analyses.value.push(response.data)
      return response.data
    } catch (e: any) {
      error.value = '加载分析失败'
    }
  }

  function nextQuestion() {
    if (currentQuestionIndex.value < questions.value.length - 1) {
      currentQuestionIndex.value++
    }
  }

  function reset() {
    currentSession.value = null
    questions.value = []
    answers.value = []
    analyses.value = []
    currentQuestionIndex.value = 0
    loading.value = false
    error.value = null
  }

  return {
    currentSession,
    questions,
    answers,
    analyses,
    currentQuestionIndex,
    loading,
    error,
    currentQuestion,
    currentAnalysis,
    progress,
    createSession,
    startSession,
    loadQuestions,
    submitAnswer,
    loadAnswerAnalysis,
    nextQuestion,
    reset,
  }
})
