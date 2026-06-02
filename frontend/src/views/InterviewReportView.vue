<template>
  <div class="interview-report">
    <h2 class="page-title">📊 面试报告</h2>
    <ReportSummaryCard v-if="report" :report="report" />
    <ScoreRadarChart v-if="report" :dimensions="report.dimensionScores" />
    <DimensionBreakdown v-if="report" :report="report" />
    <EmptyState v-else text="暂无报告" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import ReportSummaryCard from '@/components/report/ReportSummaryCard.vue'
import ScoreRadarChart from '@/components/report/ScoreRadarChart.vue'
import DimensionBreakdown from '@/components/report/DimensionBreakdown.vue'
import EmptyState from '@/components/common/EmptyState.vue'

const route = useRoute()
const report = ref(null)

onMounted(async () => {
  const sessionId = route.params.sessionId
  // API call would go here
})
</script>

<style scoped>
.page-title { font-size: 22px; margin-bottom: 24px; }
</style>
