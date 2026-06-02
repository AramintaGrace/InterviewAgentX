<template>
  <div class="radar-chart-container" v-if="dimensions && Object.keys(dimensions).length">
    <h3>📊 能力维度评估</h3>
    <div class="dimension-list">
      <div v-for="(score, dim) in dimensions" :key="dim" class="dimension-row">
        <span class="dim-label">{{ dimLabel(dim) }}</span>
        <div class="dim-bar">
          <div class="dim-fill" :style="{ width: `${score ?? 0}%` }" :class="barColor(score)"></div>
        </div>
        <span class="dim-score">{{ score ?? '—' }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ report: any }>()
const dimensions = computed<Record<string, number | null>>(() => {
  return props.report?.report_json?.dimension_scores || props.report?.dimension_scores || {}
})

const labelMap: Record<string, string> = {
  technical_ability: '技术能力',
  communication: '沟通表达',
  problem_solving: '问题解决',
  experience_relevance: '经验匹配',
  cultural_fit: '文化契合',
}
function dimLabel(key: string): string { return labelMap[key] || key }
function barColor(s: number | null): string {
  if (s == null) return ''
  if (s >= 80) return 'bar-high'
  if (s >= 60) return 'bar-mid'
  return 'bar-low'
}
</script>

<style scoped>
.radar-chart-container { background: #fff; border-radius: 10px; padding: 28px; box-shadow: 0 2px 10px rgba(0,0,0,0.06); margin-bottom: 16px; }
h3 { font-size: 17px; margin-bottom: 16px; }
.dimension-list { display: flex; flex-direction: column; gap: 10px; }
.dimension-row { display: flex; align-items: center; gap: 10px; }
.dim-label { width: 90px; font-size: 14px; color: #374151; text-align: right; font-weight: 500; }
.dim-bar { flex: 1; height: 10px; background: #e5e7eb; border-radius: 5px; overflow: hidden; }
.dim-fill { height: 100%; border-radius: 5px; transition: width 0.6s ease; background: #6366f1; }
.dim-fill.bar-high { background: #22c55e; }
.dim-fill.bar-mid { background: #eab308; }
.dim-fill.bar-low { background: #ef4444; }
.dim-score { width: 32px; font-size: 14px; font-weight: 700; color: #1f2937; text-align: center; }
</style>
