<template>
  <div class="dimension-breakdown" v-if="report">
    <h3>逐题回顾</h3>
    <div class="question-review" v-for="(qr, idx) in report.questionReviews" :key="idx">
      <div class="review-header">
        <span class="review-number">第 {{ idx + 1 }} 题</span>
        <span class="review-score">{{ qr.score }} 分</span>
      </div>
      <p class="review-question">{{ qr.questionText }}</p>
      <p class="review-feedback">{{ qr.keyFeedback }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ report: any }>()
</script>

<style scoped>
.dimension-breakdown { background: #fff; border-radius: 8px; padding: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
h3 { font-size: 16px; margin-bottom: 16px; }
.question-review { padding: 14px 0; border-bottom: 1px solid #f0f0f0; }
.question-review:last-child { border-bottom: none; }
.review-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.review-number { font-size: 13px; color: #999; }
.review-score { font-size: 16px; font-weight: 700; color: #4a90d9; }
.review-question { font-size: 14px; color: #333; margin-bottom: 4px; }
.review-feedback { font-size: 13px; color: #666; line-height: 1.6; }
</style>
