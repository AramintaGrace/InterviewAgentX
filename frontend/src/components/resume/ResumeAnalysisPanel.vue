<template>
  <div class="analysis-panel" v-if="analysis">
    <h3>简历分析结果</h3>
    <div class="analysis-section">
      <h4>综合评估</h4>
      <p>{{ analysis.overallAssessment }}</p>
    </div>
    <div class="analysis-section">
      <h4>优势</h4>
      <ul><li v-for="s in analysis.strengths" :key="s">{{ s }}</li></ul>
    </div>
    <div class="analysis-section">
      <h4>待提升</h4>
      <ul><li v-for="w in analysis.weaknesses" :key="w">{{ w }}</li></ul>
    </div>
    <div class="analysis-section">
      <h4>建议面试题目</h4>
      <ul><li v-for="q in analysis.suggestedQuestions" :key="q">{{ q }}</li></ul>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ analysis: any }>()
</script>

<style scoped>
.analysis-panel { background: #fff; border-radius: 8px; padding: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
h3 { font-size: 16px; margin-bottom: 16px; }
.analysis-section { margin-bottom: 16px; }
h4 { font-size: 14px; color: #666; margin-bottom: 6px; }
p { font-size: 14px; line-height: 1.6; }
ul { padding-left: 20px; }
li { font-size: 14px; line-height: 1.8; }
</style>
