<template>
  <div class="report-summary" v-if="data">
    <div class="summary-header">
      <h3>面试报告摘要</h3>
      <span class="recommendation" :class="data.hiring_recommendation">
        {{ recommendationLabel }}
      </span>
    </div>
    <div class="summary-stats">
      <div class="stat">
        <span class="value" :class="scoreColor">{{ data.overall_score ?? '-' }}</span>
        <span class="label">综合评分</span>
      </div>
      <div class="stat">
        <span class="value">{{ data.question_reviews?.length || 0 }}</span>
        <span class="label">答题数</span>
      </div>
    </div>
    <p class="summary-feedback">{{ data.detailed_feedback }}</p>

    <div v-if="data.strengths?.length" class="tag-section">
      <h4>✅ 优势</h4>
      <div class="tags">
        <span v-for="s in data.strengths" :key="s" class="tag tag-good">{{ s }}</span>
      </div>
    </div>
    <div v-if="data.weaknesses?.length" class="tag-section">
      <h4>🔧 待提升</h4>
      <div class="tags">
        <span v-for="w in data.weaknesses" :key="w" class="tag tag-warn">{{ w }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ReportData } from '@/types/report'

const props = defineProps<{ report: any }>()

// 兼容嵌套 report_json 和直接展开
const data = computed<ReportData>(() => props.report?.report_json || props.report || {})

const recommendationMap: Record<string, string> = {
  strongly_recommend: '强烈推荐',
  recommend: '推荐录用',
  consider: '考虑录用',
  not_recommend: '不予推荐',
}
const recommendationLabel = computed(() => recommendationMap[data.value?.hiring_recommendation] || '—')

const scoreColor = computed(() => {
  const s = data.value?.overall_score
  if (s == null) return ''
  if (s >= 80) return 'score-high'
  if (s >= 60) return 'score-mid'
  return 'score-low'
})
</script>

<style scoped>
.report-summary { background: #fff; border-radius: 10px; padding: 28px; box-shadow: 0 2px 10px rgba(0,0,0,0.06); margin-bottom: 16px; }
.summary-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
h3 { font-size: 17px; }
.recommendation { font-size: 13px; padding: 4px 14px; border-radius: 12px; font-weight: 600; }
.strongly_recommend { background: #f6ffed; color: #389e0d; }
.recommend { background: #e8f0fe; color: #1a73e8; }
.consider { background: #fffbe6; color: #d48806; }
.not_recommend { background: #fff2f0; color: #cf1322; }
.summary-stats { display: flex; gap: 40px; margin-bottom: 20px; }
.stat { display: flex; flex-direction: column; }
.stat .value { font-size: 32px; font-weight: 700; color: #1a1a2e; }
.stat .value.score-high { color: #22c55e; }
.stat .value.score-mid { color: #eab308; }
.stat .value.score-low { color: #ef4444; }
.stat .label { font-size: 12px; color: #999; }
.summary-feedback { font-size: 14px; line-height: 1.8; color: #4b5563; margin-bottom: 16px; }
.tag-section { margin-top: 16px; }
.tag-section h4 { font-size: 13px; color: #666; margin-bottom: 8px; }
.tags { display: flex; flex-wrap: wrap; gap: 8px; }
.tag { font-size: 13px; padding: 4px 12px; border-radius: 10px; }
.tag-good { background: #e8f5e9; color: #2e7d32; }
.tag-warn { background: #fff3e0; color: #e65100; }
</style>
