<template>
  <div class="interview-session">
    <h2 class="page-title">
      🎤 面试作答
      <span v-if="store.currentSession?.question_source" class="source-badge" :class="store.currentSession.question_source">
        {{ sourceLabel }}
      </span>
    </h2>

    <ErrorBanner v-if="error" :message="error" @dismiss="error = ''" />

    <!-- 进度条 -->
    <InterviewProgressBar :current="store.progress.current" :total="store.progress.total" />

    <!-- 加载中 -->
    <LoadingSpinner v-if="loading" :text="loadingText" />

    <!-- 题目区域 -->
    <div v-if="currentQuestion && !loading" class="question-area">
      <QuestionCard :question="currentQuestion" />

      <AudioRecordButton @transcript="onTranscript" />
      <TranscriptDisplay v-model="transcript" />

      <div class="action-buttons">
        <button class="btn-primary" @click="submitAnswer"
          :disabled="!transcript.trim() || submitting || currentSubmitted">
          {{ submitting ? '⏳ 提交并分析中...' : currentSubmitted ? '✅ 已提交评分' : '📤 提交答案' }}
        </button>
        <button class="btn-secondary" @click="nextQuestion" :disabled="!currentSubmitted || submitting">
          ▶ 下一题
        </button>
      </div>
    </div>

    <!-- 分析结果 -->
    <AnswerAnalysisPanel v-if="currentAnalysis" :analysis="currentAnalysis" />

    <!-- 完成 -->
    <div v-if="isComplete" class="complete-section">
      <h3>🎉 面试完成！</h3>
      <p>所有题目已回答完毕</p>
      <button v-if="!generatingReport" class="btn-report" @click="generateReport">
        🤖 生成面试报告
      </button>
      <LoadingSpinner v-else text="正在生成报告..." />
      <router-link v-if="reportReady" :to="`/reports/${sessionId}`" class="btn-view-report">
        📊 查看面试报告
      </router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import InterviewProgressBar from '@/components/interview/InterviewProgressBar.vue'
import QuestionCard from '@/components/interview/QuestionCard.vue'
import AudioRecordButton from '@/components/interview/AudioRecordButton.vue'
import TranscriptDisplay from '@/components/interview/TranscriptDisplay.vue'
import AnswerAnalysisPanel from '@/components/interview/AnswerAnalysisPanel.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import ErrorBanner from '@/components/common/ErrorBanner.vue'
import { useInterviewStore } from '@/stores/interview'
import { interviewsApi } from '@/api/interviews'
import { reportsApi } from '@/api/reports'

const route = useRoute()
const store = useInterviewStore()
const sessionId = route.params.sessionId as string

const sourceLabel = computed(() => {
  const map: Record<string, string> = { resume: '简历模式', knowledge_base: '知识库模式', mixed: '混合模式' }
  return map[store.currentSession?.question_source || ''] || ''
})

const transcript = ref('')
const submitting = ref(false)
const error = ref('')
const loading = ref(false)
const loadingText = ref('')
const generatingReport = ref(false)
const reportReady = ref(false)

const currentQuestion = computed(() => store.currentQuestion)
const currentAnalysis = computed(() => store.currentAnalysis)
const submittedIndexes = ref<Set<number>>(new Set())
const currentSubmitted = computed(() => submittedIndexes.value.has(store.currentQuestionIndex))
const allQuestionsLoaded = computed(() => store.questions.length > 0)
const allAnswered = computed(() =>
  allQuestionsLoaded.value && store.answers.length >= store.questions.length
)
const isComplete = computed(() =>
  store.currentSession?.status === 'completed' || allAnswered.value
)

onMounted(async () => {
  // 如果 store 有 session 但没有题目，重新加载
  if (!store.currentSession || store.currentSession.id !== sessionId) {
    loading.value = true
    loadingText.value = '加载面试会话...'
    try {
      const sessionRes = await interviewsApi.get(sessionId)
      store.currentSession = sessionRes.data
    } catch (e: any) {
      error.value = '加载面试会话失败: ' + (e.message || '未知错误')
      loading.value = false
      return
    }
  }

  if (store.questions.length === 0) {
    loadingText.value = '加载题目...'
    try {
      await store.loadQuestions(sessionId)
    } catch (e: any) {
      error.value = '加载题目失败: ' + (e.message || '未知错误')
    }
  }

  // 恢复已提交的回答及其分析
  try {
    const answersRes = await interviewsApi.listAnswers(sessionId)
    store.answers = answersRes.data || []
    if (store.answers.length > 0) {
      store.currentQuestionIndex = Math.min(store.answers.length, store.questions.length - 1)
      // 恢复已提交标记
      const idxs = new Set<number>()
      for (let i = 0; i < store.answers.length; i++) idxs.add(i)
      submittedIndexes.value = idxs
      // 批量加载所有回答的分析
      store.analyses = []
      for (const a of store.answers) {
        try {
          await store.loadAnswerAnalysis(sessionId, a.id)
        } catch { /* 分析可能不存在 */ }
      }
    }
  } catch { /* 首次访问 */ }

  loading.value = false
})

function onTranscript(text: string) {
  // 追加到已有内容（不清空），方便语音多次录制和手动编辑混合使用
  transcript.value = transcript.value ? transcript.value + '\n' + text : text
}

async function submitAnswer() {
  if (!transcript.value.trim() || !currentQuestion.value || currentSubmitted.value) return

  submitting.value = true
  error.value = ''

  try {
    // 1) 提交回答
    const answerRes = await store.submitAnswer(
      sessionId,
      currentQuestion.value.id,
      transcript.value
    )

    // 2) 触发 AI 分析
    const analysisRes = await interviewsApi.analyzeAnswer(sessionId, answerRes.id)
    store.analyses.push(analysisRes.data)

    // 3) 标记已提交
    const idx = submittedIndexes.value
    idx.add(store.currentQuestionIndex)
    submittedIndexes.value = new Set(idx)

    // 4) 清空输入
    transcript.value = ''
  } catch (e: any) {
    error.value = e.message || '提交失败，请重试'
  } finally {
    submitting.value = false
  }
}

function nextQuestion() {
  transcript.value = ''
  store.nextQuestion()
}

async function generateReport() {
  generatingReport.value = true
  try {
    await reportsApi.generate(sessionId)
    reportReady.value = true
  } catch (e: any) {
    error.value = e.message || '报告生成失败'
  } finally {
    generatingReport.value = false
  }
}
</script>

<style scoped>
.page-title { font-size: 22px; margin-bottom: 24px; display: flex; align-items: center; gap: 12px; }
.source-badge { font-size: 12px; padding: 2px 10px; border-radius: 10px; font-weight: 500; }
.source-badge.resume { background: #e8f0fe; color: #1a73e8; }
.source-badge.knowledge_base { background: #e8f5e9; color: #2e7d32; }
.source-badge.mixed { background: #fff3e0; color: #e65100; }
.question-area {
  max-width: 800px;
  background: #fff;
  padding: 24px;
  border-radius: 10px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.06);
  margin-bottom: 16px;
}
.action-buttons { display: flex; gap: 12px; margin-top: 20px; }
.btn-primary {
  flex: 1;
  padding: 12px 24px;
  background: #1a73e8;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
}
.btn-primary:hover:not(:disabled) { background: #1557b0; }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-secondary {
  padding: 12px 20px;
  background: #f5f5f5;
  color: #666;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
}
.btn-secondary:hover:not(:disabled) { background: #eee; }
.btn-secondary:disabled { opacity: 0.4; cursor: not-allowed; }

.complete-section {
  max-width: 800px;
  text-align: center;
  padding: 48px 20px;
  background: #e8f5e9;
  border-radius: 10px;
  margin-top: 24px;
}
.complete-section h3 { font-size: 22px; color: #2e7d32; margin-bottom: 8px; }
.complete-section p { font-size: 14px; color: #666; margin-bottom: 20px; }
.btn-report {
  display: inline-block;
  padding: 12px 28px;
  background: #1a73e8;
  color: #fff;
  border: none;
  border-radius: 8px;
  text-decoration: none;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
}
.btn-report:hover:not(:disabled) { background: #1557b0; }
.btn-view-report {
  display: inline-block;
  margin-top: 12px;
  padding: 10px 24px;
  background: #e8f5e9;
  color: #2e7d32;
  border: 1px solid #2e7d32;
  border-radius: 8px;
  text-decoration: none;
  font-size: 14px;
  font-weight: 600;
}
.btn-view-report:hover { background: #c8e6c9; }
</style>
