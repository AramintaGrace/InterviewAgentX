<template>
  <div class="analysis-panel" v-if="analysis">
    <h3>📊 AI 简历分析</h3>

    <!-- 元信息 -->
    <div class="meta-row" v-if="analysis.tokens_used || analysis.processing_ms">
      <span v-if="analysis.tokens_used" class="meta-badge">🪙 {{ analysis.tokens_used }} tokens</span>
      <span v-if="analysis.processing_ms" class="meta-badge">⏱️ {{ (analysis.processing_ms / 1000).toFixed(1) }}s</span>
      <span v-if="analysis.agent_model" class="meta-badge">🤖 {{ analysis.agent_model }}</span>
    </div>

    <!-- 综合评估 -->
    <div class="analysis-section">
      <h4>📝 综合评估</h4>
      <p>{{ analysis.analysis_json?.overall_assessment || analysis.overall_assessment || '-' }}</p>
    </div>

    <!-- 经验相关度 -->
    <div v-if="expScore != null" class="analysis-section">
      <h4>📈 经验匹配度</h4>
      <div class="score-bar-wrap">
        <div class="score-bar">
          <div class="score-fill" :style="{ width: expScore + '%' }" :class="scoreColorClass"></div>
        </div>
        <span class="score-value">{{ expScore }} / 100</span>
      </div>
    </div>

    <!-- 技能匹配度 -->
    <div v-if="skillMap && Object.keys(skillMap).length" class="analysis-section">
      <h4>🛠 技能评分</h4>
      <div class="skill-scores">
        <div v-for="(score, skill) in skillMap" :key="skill" class="skill-row">
          <span class="skill-name">{{ skill }}</span>
          <div class="skill-bar">
            <div class="skill-fill" :style="{ width: (score / 10 * 100) + '%' }"></div>
          </div>
          <span class="skill-score">{{ score }}/10</span>
        </div>
      </div>
    </div>

    <!-- 优势 -->
    <div v-if="strengths.length" class="analysis-section">
      <h4>✅ 优势 ({{ strengths.length }})</h4>
      <ul>
        <li v-for="(s, i) in strengths" :key="i">{{ s }}</li>
      </ul>
    </div>

    <!-- 待提升 -->
    <div v-if="weaknesses.length" class="analysis-section">
      <h4>⚠️ 待提升 ({{ weaknesses.length }})</h4>
      <ul>
        <li v-for="(w, i) in weaknesses" :key="i">{{ w }}</li>
      </ul>
    </div>

    <!-- 项目亮点 -->
    <div v-if="highlights.length" class="analysis-section">
      <h4>🚀 项目亮点 ({{ highlights.length }})</h4>
      <div v-for="(p, i) in highlights" :key="i" class="project-card">
        <div class="project-name">{{ p.project }}</div>
        <p class="project-depth">{{ p.depth_analysis }}</p>
      </div>
    </div>

    <!-- 风险提示 -->
    <div v-if="redFlags.length" class="analysis-section">
      <h4>🔴 风险提示 ({{ redFlags.length }})</h4>
      <ul class="red-flag-list">
        <li v-for="(f, i) in redFlags" :key="i">{{ f }}</li>
      </ul>
    </div>

    <!-- 建议面试题目 -->
    <div v-if="questions.length" class="analysis-section">
      <h4>💬 建议面试题目 ({{ questions.length }})</h4>
      <ol class="question-list">
        <li v-for="(q, i) in questions" :key="i">{{ q }}</li>
      </ol>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ analysis: any }>()

const json = computed(() => props.analysis?.analysis_json || props.analysis || {})

const expScore = computed(() => {
  return json.value?.experience_relevance_score ?? null
})

const scoreColorClass = computed(() => {
  if (expScore.value >= 80) return 'score-high'
  if (expScore.value >= 50) return 'score-mid'
  return 'score-low'
})

const skillMap = computed(() => json.value?.skill_match || {})

const strengths = computed<string[]>(() => json.value?.strengths || [])
const weaknesses = computed<string[]>(() => json.value?.weaknesses || [])
const redFlags = computed<string[]>(() => json.value?.red_flags || [])
const questions = computed<string[]>(() => json.value?.suggested_questions || [])

const highlights = computed<any[]>(() => json.value?.project_highlights || [])
</script>

<style scoped>
.analysis-panel {
  max-width: 800px;
  background: #fff;
  border-radius: 12px;
  padding: 32px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.06);
}
h3 { font-size: 20px; margin-bottom: 20px; }

.meta-row {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}
.meta-badge {
  font-size: 12px;
  color: #666;
  background: #f3f4f6;
  padding: 4px 10px;
  border-radius: 10px;
}

.analysis-section { margin-bottom: 24px; }
.analysis-section h4 {
  font-size: 15px;
  font-weight: 600;
  color: #374151;
  margin-bottom: 10px;
}
.analysis-section p { font-size: 14px; line-height: 1.7; color: #4b5563; }
.analysis-section ul, .analysis-section ol { padding-left: 20px; }
.analysis-section li { font-size: 14px; line-height: 2; color: #4b5563; }

/* Score bar */
.score-bar-wrap {
  display: flex;
  align-items: center;
  gap: 12px;
}
.score-bar {
  flex: 1;
  height: 10px;
  background: #e5e7eb;
  border-radius: 5px;
  overflow: hidden;
}
.score-fill {
  height: 100%;
  border-radius: 5px;
  transition: width 0.6s ease;
}
.score-high { background: #22c55e; }
.score-mid  { background: #eab308; }
.score-low  { background: #ef4444; }
.score-value {
  font-size: 14px;
  font-weight: 600;
  color: #374151;
  min-width: 60px;
  text-align: right;
}

/* Skill scores */
.skill-scores {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.skill-row {
  display: flex;
  align-items: center;
  gap: 10px;
}
.skill-name {
  width: 120px;
  font-size: 13px;
  color: #4b5563;
  flex-shrink: 0;
}
.skill-bar {
  flex: 1;
  height: 8px;
  background: #e5e7eb;
  border-radius: 4px;
  overflow: hidden;
}
.skill-fill {
  height: 100%;
  background: #6366f1;
  border-radius: 4px;
  transition: width 0.4s ease;
}
.skill-score {
  font-size: 13px;
  color: #6366f1;
  font-weight: 600;
  min-width: 36px;
  text-align: right;
}

/* Project cards */
.project-card {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 12px 16px;
  margin-bottom: 10px;
}
.project-name {
  font-weight: 600;
  font-size: 14px;
  color: #1f2937;
  margin-bottom: 4px;
}
.project-depth {
  font-size: 13px;
  color: #6b7280;
  line-height: 1.6;
  margin: 0;
}

/* Red flags */
.red-flag-list li { color: #dc2626; }

/* Questions */
.question-list li {
  padding: 8px 0;
  border-bottom: 1px solid #f3f4f6;
}
.question-list li:last-child { border-bottom: none; }
</style>
