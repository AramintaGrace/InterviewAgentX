<template>
  <div class="progress-bar-container">
    <div class="progress-info">
      <span>面试进度</span>
      <span>{{ current }} / {{ total }}</span>
    </div>
    <div class="progress-track">
      <div class="progress-fill" :style="{ width: `${percentage}%` }"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ current: number; total: number }>()
const percentage = computed(() => Math.round((props.current / props.total) * 100))
</script>

<style scoped>
.progress-bar-container { margin-bottom: 20px; }
.progress-info { display: flex; justify-content: space-between; font-size: 13px; color: #666; margin-bottom: 6px; }
.progress-track { height: 6px; background: #e8e8e8; border-radius: 3px; overflow: hidden; }
.progress-fill { height: 100%; background: linear-gradient(90deg, #4a90d9, #67b8a4); border-radius: 3px; transition: width 0.3s; }
</style>
