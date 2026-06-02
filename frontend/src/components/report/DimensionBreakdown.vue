<template>
  <div class="dimension-breakdown" v-if="data">
    <h3>📋 逐题回顾</h3>
    <div class="question-review" v-for="(qr, idx) in data.question_reviews" :key="idx">
      <div class="review-header">
        <span class="review-number">第 {{ idx + 1 }} 题 · {{ sourceLabel(qr.source_type) }}</span>
        <span :class="['review-score', scoreColor(qr.score)]">{{ qr.score }} 分</span>
      </div>
      <p class="review-question">{{ qr.question_text }}</p>
      <p v-if="qr.key_feedback" class="review-feedback">{{ qr.key_feedback }}</p>
      <p v-if="qr.assessment" class="review-assessment">{{ qr.assessment }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ReportData } from '@/types/report'

const props = defineProps<{ report: any }>()
const data = computed<ReportData>(() => props.report?.report_json || props.report || {})

function sourceLabel(s: string): string {
  const map: Record<string, string> = {
    resume_experience: '简历经历', resume_project: '简历项目', knowledge_base: '知识库',
  }
  return map[s] || s
}
function scoreColor(s: number): string {
  if (s >= 80) return 'score-high'
  if (s >= 60) return 'score-mid'
  return 'score-low'
}
</script>

<style scoped>
.dimension-breakdown { background: #fff; border-radius: 10px; padding: 28px; box-shadow: 0 2px 10px rgba(0,0,0,0.06); }
h3 { font-size: 17px; margin-bottom: 20px; }
.question-review { padding: 16px 0; border-bottom: 1px solid #f3f4f6; }
.question-review:last-child { border-bottom: none; }
.review-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.review-number { font-size: 12px; color: #999; }
.review-score { font-size: 16px; font-weight: 700; }
.score-high { color: #22c55e; }
.score-mid { color: #eab308; }
.score-low { color: #ef4444; }
.review-question { font-size: 14px; color: #333; margin-bottom: 6px; line-height: 1.6; }
.review-feedback { font-size: 13px; color: #6366f1; line-height: 1.6; }
.review-assessment { font-size: 13px; color: #6b7280; line-height: 1.6; margin-top: 4px; }
</style>
