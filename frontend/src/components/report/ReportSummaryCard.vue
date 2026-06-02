<template>
  <div class="report-summary" v-if="report">
    <div class="summary-header">
      <h3>面试报告摘要</h3>
      <span class="recommendation" :class="report.hiringRecommendation">
        {{ recommendationLabel }}
      </span>
    </div>
    <div class="summary-stats">
      <div class="stat"><span class="value">{{ report.overallScore }}</span><span class="label">综合评分</span></div>
      <div class="stat"><span class="value">{{ report.questionReviews?.length || 0 }}</span><span class="label">答题数</span></div>
    </div>
    <p class="summary-feedback">{{ report.detailedFeedback }}</p>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ report: any }>()

const recommendationMap: Record<string, string> = {
  strongly_recommend: '强烈推荐',
  recommend: '推荐录用',
  consider: '考虑录用',
  not_recommend: '不予推荐',
}

const recommendationLabel = computed(() => recommendationMap[props.report?.hiringRecommendation] || '未知')
</script>

<style scoped>
.report-summary { background: #fff; border-radius: 8px; padding: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); margin-bottom: 16px; }
.summary-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
h3 { font-size: 16px; }
.recommendation { font-size: 13px; padding: 4px 12px; border-radius: 12px; font-weight: 600; }
.recommendation.strongly_recommend { background: #f6ffed; color: #389e0d; }
.recommendation.recommend { background: #e8f0fe; color: #1a73e8; }
.recommendation.consider { background: #fffbe6; color: #d48806; }
.recommendation.not_recommend { background: #fff2f0; color: #cf1322; }
.summary-stats { display: flex; gap: 32px; margin-bottom: 16px; }
.stat { display: flex; flex-direction: column; }
.stat .value { font-size: 28px; font-weight: 700; color: #1a1a2e; }
.stat .label { font-size: 12px; color: #999; }
.summary-feedback { font-size: 14px; line-height: 1.6; color: #555; }
</style>
