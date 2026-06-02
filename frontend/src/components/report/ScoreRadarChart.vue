<template>
  <div class="radar-chart-container">
    <h3>能力维度评估</h3>
    <div class="chart-placeholder">
      <p>雷达图区域 (ECharts)</p>
      <div class="dimension-list">
        <div v-for="(score, dim) in dimensions" :key="dim" class="dimension-row">
          <span class="dim-label">{{ dimLabel(dim) }}</span>
          <div class="dim-bar"><div class="dim-fill" :style="{ width: `${score}%` }"></div></div>
          <span class="dim-score">{{ score }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ dimensions: Record<string, number> }>()

const labelMap: Record<string, string> = {
  technical_ability: '技术能力',
  communication: '沟通表达',
  problem_solving: '问题解决',
  experience_relevance: '经验匹配',
  cultural_fit: '文化契合',
}

function dimLabel(key: string): string {
  return labelMap[key] || key
}
</script>

<style scoped>
.radar-chart-container { background: #fff; border-radius: 8px; padding: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); margin-bottom: 16px; }
h3 { font-size: 16px; margin-bottom: 16px; }
.chart-placeholder p { color: #999; font-size: 13px; text-align: center; }
.dimension-list { margin-top: 16px; }
.dimension-row { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.dim-label { width: 80px; font-size: 13px; color: #666; text-align: right; }
.dim-bar { flex: 1; height: 8px; background: #e8e8e8; border-radius: 4px; overflow: hidden; }
.dim-fill { height: 100%; background: linear-gradient(90deg, #4a90d9, #67b8a4); border-radius: 4px; transition: width 0.5s; }
.dim-score { width: 30px; font-size: 13px; font-weight: 600; color: #333; }
</style>
