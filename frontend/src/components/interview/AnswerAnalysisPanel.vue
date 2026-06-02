<template>
  <div class="answer-analysis" v-if="analysis">
    <h3>📊 作答分析</h3>

    <!-- 评估模式 -->
    <div class="analysis-mode">
      <span class="mode-badge" :class="analysis.eval_mode">
        {{ analysis.eval_mode === 'rag_hybrid' ? 'RAG混合评估' : 'LLM裁判评估' }}
      </span>
      <span v-if="analysis.agent_model" class="model-badge">🤖 {{ analysis.agent_model }}</span>
    </div>

    <!-- 综合得分 -->
    <div class="score-display">
      <div class="score-circle" :class="scoreColorClass">
        <span class="score-value">{{ data.overall_score ?? '-' }}</span>
        <span class="score-label">综合得分</span>
      </div>
    </div>

    <!-- LLM Judge / RAG 四维评分（仅 LLM Judge 模式显示） -->
    <div v-if="analysis.eval_mode === 'llm_judge' && hasDimensions" class="dimensions">
      <div class="dim-row" v-for="dim in dimensions" :key="dim.key">
        <div class="dim-header">
          <span class="dim-label">{{ dim.label }}</span>
          <span class="dim-score">{{ dim.score }}/5</span>
        </div>
        <div class="dim-bar"><div class="dim-fill" :style="{ width: (dim.score / 5 * 100) + '%' }"></div></div>
        <p v-if="dim.reasoning" class="dim-reason">{{ dim.reasoning }}</p>
      </div>
    </div>

    <!-- RAG 向量相似度 -->
    <div v-if="data.vector_similarity != null" class="detail-section">
      <h4>🔢 向量相似度</h4>
      <div class="similarity-bar-wrap">
        <div class="sim-bar"><div class="sim-fill" :style="{ width: (data.vector_similarity * 100) + '%' }"></div></div>
        <span class="sim-value">{{ (data.vector_similarity * 100).toFixed(0) }}%</span>
      </div>
    </div>

    <!-- RAG 覆盖/遗漏 -->
    <div v-if="data.covered_points?.length" class="detail-section">
      <h4>✅ 覆盖的得分点</h4>
      <ul><li v-for="p in data.covered_points" :key="p">{{ p }}</li></ul>
    </div>
    <div v-if="data.missing_points?.length" class="detail-section">
      <h4>❌ 遗漏的得分点</h4>
      <ul><li v-for="p in data.missing_points" :key="p">{{ p }}</li></ul>
    </div>

    <!-- 评语 -->
    <div v-if="data.assessment" class="detail-section">
      <h4>📝 综合评语</h4>
      <p>{{ data.assessment }}</p>
    </div>

    <!-- 亮点和改进 -->
    <div v-if="data.strengths?.length" class="detail-section">
      <h4>✅ 亮点</h4>
      <ul><li v-for="s in data.strengths" :key="s">{{ s }}</li></ul>
    </div>
    <div v-if="data.areas_for_improvement?.length" class="detail-section">
      <h4>🔧 改进建议</h4>
      <ul><li v-for="a in data.areas_for_improvement" :key="a">{{ a }}</li></ul>
    </div>

    <!-- 真实性标记 -->
    <div v-if="data.authenticity_flag" class="detail-section">
      <h4>🔍 真实性判断</h4>
      <span :class="['flag-badge', `flag-${data.authenticity_flag}`]">{{ flagLabel }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ analysis: any }>()

// 兼容 analysis_json 嵌套和直接展开两种格式
const data = computed(() => props.analysis?.analysis_json || props.analysis || {})

const scoreColorClass = computed(() => {
  const s = data.value.overall_score
  if (s == null) return ''
  if (s >= 80) return 'score-high'
  if (s >= 60) return 'score-mid'
  return 'score-low'
})

const hasDimensions = computed(() =>
  (data.value.accuracy_score || data.value.completeness_score ||
   data.value.clarity_score || data.value.technical_depth_score) != null
)

const dimensions = computed(() => [
  { key: 'accuracy', label: '真实性', score: data.value.accuracy_score ?? 0, reasoning: data.value.accuracy_reasoning },
  { key: 'completeness', label: '完整性', score: data.value.completeness_score ?? 0, reasoning: data.value.completeness_reasoning },
  { key: 'clarity', label: '表达清晰度', score: data.value.clarity_score ?? 0, reasoning: data.value.clarity_reasoning },
  { key: 'technical_depth', label: '技术深度', score: data.value.technical_depth_score ?? 0, reasoning: data.value.technical_depth_reasoning },
])

const flagLabel = computed(() => {
  const map: Record<string, string> = {
    consistent: '与简历一致',
    inconsistent: '存在矛盾',
    uncertain: '无法判断',
  }
  return map[data.value.authenticity_flag] || data.value.authenticity_flag
})
</script>

<style scoped>
.answer-analysis {
  max-width: 800px;
  background: #fff;
  border-radius: 10px;
  padding: 28px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.06);
  margin-top: 16px;
}
h3 { font-size: 17px; margin-bottom: 16px; }

.analysis-mode { display: flex; gap: 8px; align-items: center; margin-bottom: 16px; }
.mode-badge, .model-badge {
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 10px;
}
.mode-badge.rag_hybrid { background: #e6f8e6; color: #389e0d; }
.mode-badge.llm_judge { background: #e8f0fe; color: #1a73e8; }
.model-badge { background: #f3f4f6; color: #666; }

.score-display { display: flex; justify-content: center; margin: 20px 0; }
.score-circle {
  width: 84px; height: 84px; border-radius: 50%;
  background: linear-gradient(135deg, #4a90d9, #67b8a4);
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  color: #fff;
}
.score-circle.score-high { background: linear-gradient(135deg, #22c55e, #16a34a); }
.score-circle.score-mid { background: linear-gradient(135deg, #eab308, #ca8a04); }
.score-circle.score-low { background: linear-gradient(135deg, #ef4444, #dc2626); }
.score-value { font-size: 26px; font-weight: 700; }
.score-label { font-size: 10px; opacity: 0.9; }

.dimensions { margin-bottom: 16px; }
.dim-row {
  margin-bottom: 14px;
  padding: 12px;
  background: #f9fafb;
  border-radius: 8px;
}
.dim-header { display: flex; justify-content: space-between; margin-bottom: 6px; }
.dim-label { font-size: 13px; font-weight: 600; color: #374151; }
.dim-score { font-size: 13px; color: #6366f1; font-weight: 600; }
.dim-bar { height: 6px; background: #e5e7eb; border-radius: 3px; overflow: hidden; }
.dim-fill { height: 100%; background: #6366f1; border-radius: 3px; transition: width 0.4s; }
.dim-reason { font-size: 12px; color: #9ca3af; margin: 6px 0 0 0; line-height: 1.5; }

.detail-section { margin-bottom: 16px; }
.detail-section h4 { font-size: 13px; color: #666; margin-bottom: 6px; font-weight: 600; }
.detail-section p { font-size: 14px; line-height: 1.7; color: #4b5563; }
.detail-section ul { padding-left: 20px; }
.detail-section li { font-size: 14px; line-height: 1.8; color: #4b5563; }

.flag-badge { font-size: 13px; padding: 3px 10px; border-radius: 8px; font-weight: 500; }
.flag-consistent { background: #e8f5e9; color: #2e7d32; }
.flag-inconsistent { background: #fdecea; color: #c62828; }
.flag-uncertain { background: #fff3e0; color: #e65100; }

.similarity-bar-wrap { display: flex; align-items: center; gap: 10px; }
.sim-bar { flex: 1; height: 8px; background: #e5e7eb; border-radius: 4px; overflow: hidden; }
.sim-fill { height: 100%; border-radius: 4px; background: linear-gradient(90deg, #6366f1, #a78bfa); transition: width 0.4s; }
.sim-value { font-size: 13px; font-weight: 600; color: #6366f1; }
</style>
