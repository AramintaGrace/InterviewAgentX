<template>
  <div class="answer-analysis" v-if="analysis">
    <h3>📊 作答分析</h3>
    <div class="analysis-mode">
      <span class="mode-badge" :class="analysis.evalMode">
        {{ analysis.evalMode === 'rag_hybrid' ? 'RAG混合评估' : 'LLM裁判评估' }}
      </span>
    </div>
    <div class="score-display">
      <div class="score-circle">
        <span class="score-value">{{ analysis.overallScore }}</span>
        <span class="score-label">综合得分</span>
      </div>
    </div>
    <div class="analysis-detail">
      <div v-if="analysis.strengths?.length" class="detail-section">
        <h4>✅ 亮点</h4>
        <ul><li v-for="s in analysis.strengths" :key="s">{{ s }}</li></ul>
      </div>
      <div v-if="analysis.areasForImprovement?.length" class="detail-section">
        <h4>🔧 改进建议</h4>
        <ul><li v-for="a in analysis.areasForImprovement" :key="a">{{ a }}</li></ul>
      </div>
      <div v-if="analysis.assessment" class="detail-section">
        <h4>📝 综合评语</h4>
        <p>{{ analysis.assessment }}</p>
      </div>
      <div v-if="analysis.missingPoints?.length" class="detail-section">
        <h4>❌ 遗漏得分点</h4>
        <ul><li v-for="p in analysis.missingPoints" :key="p">{{ p }}</li></ul>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ analysis: any }>()
</script>

<style scoped>
.answer-analysis { background: #fff; border-radius: 8px; padding: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
h3 { font-size: 16px; margin-bottom: 12px; }
.analysis-mode { margin-bottom: 16px; }
.mode-badge { font-size: 12px; padding: 4px 10px; border-radius: 10px; }
.mode-badge.rag_hybrid { background: #e6f8e6; color: #389e0d; }
.mode-badge.llm_judge { background: #e8f0fe; color: #1a73e8; }
.score-display { display: flex; justify-content: center; margin: 20px 0; }
.score-circle {
  width: 80px; height: 80px; border-radius: 50%;
  background: linear-gradient(135deg, #4a90d9, #67b8a4);
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  color: #fff;
}
.score-value { font-size: 28px; font-weight: 700; }
.score-label { font-size: 10px; opacity: 0.9; }
.detail-section { margin-bottom: 14px; }
h4 { font-size: 13px; color: #666; margin-bottom: 6px; }
p { font-size: 14px; line-height: 1.6; }
ul { padding-left: 20px; }
li { font-size: 14px; line-height: 1.8; }
</style>
