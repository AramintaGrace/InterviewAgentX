<template>
  <div class="interview-session">
    <h2 class="page-title">🎤 面试作答</h2>
    <InterviewProgressBar :current="currentQuestion" :total="totalQuestions" />
    <div v-if="currentQuestionObj" class="question-area">
      <QuestionCard :question="currentQuestionObj" />
      <AudioRecordButton @transcript="onTranscript" />
      <TranscriptDisplay :text="transcript" />
      <div class="action-buttons">
        <button class="btn-primary" @click="submitAnswer" :disabled="!transcript">提交答案</button>
        <button class="btn-secondary" @click="skipQuestion">跳过</button>
      </div>
    </div>
    <AnswerAnalysisPanel v-if="currentAnalysis" :analysis="currentAnalysis" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import InterviewProgressBar from '@/components/interview/InterviewProgressBar.vue'
import QuestionCard from '@/components/interview/QuestionCard.vue'
import AudioRecordButton from '@/components/interview/AudioRecordButton.vue'
import TranscriptDisplay from '@/components/interview/TranscriptDisplay.vue'
import AnswerAnalysisPanel from '@/components/interview/AnswerAnalysisPanel.vue'

const currentQuestion = ref(1)
const totalQuestions = ref(5)
const transcript = ref('')
const currentAnalysis = ref(null)

const currentQuestionObj = computed(() => ({
  text: '请介绍一下你在项目中遇到的最大技术挑战？',
  sourceType: 'resume_project',
  questionOrder: currentQuestion.value,
}))

function onTranscript(text: string) {
  transcript.value = text
}

function submitAnswer() {
  currentAnalysis.value = {
    overallScore: 85,
    evalMode: 'llm_judge',
    strengths: ['逻辑清晰', '技术深度好'],
    areasForImprovement: ['可以更具体'],
    assessment: '回答整体表现良好。',
  }
}

function skipQuestion() {
  currentQuestion.value++
  transcript.value = ''
  currentAnalysis.value = null
}
</script>

<style scoped>
.page-title { font-size: 22px; margin-bottom: 24px; }
.question-area { background: #fff; padding: 24px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); margin-bottom: 16px; }
.action-buttons { display: flex; gap: 12px; margin-top: 16px; }
.btn-primary { padding: 10px 24px; background: #4a90d9; color: #fff; border: none; border-radius: 6px; cursor: pointer; }
.btn-primary:disabled { background: #ccc; cursor: not-allowed; }
.btn-secondary { padding: 10px 24px; background: #f5f5f5; color: #666; border: 1px solid #ddd; border-radius: 6px; cursor: pointer; }
</style>
