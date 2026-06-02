<template>
  <div class="interview-report">
    <h2 class="page-title">📊 面试报告</h2>

    <ErrorBanner v-if="error" :message="error" @dismiss="error = ''" />

    <!-- Loading -->
    <LoadingSpinner v-if="loading" text="正在加载报告..." />

    <!-- 无报告：提供生成按钮 -->
    <div v-if="!loading && !report && !generating" class="empty-box">
      <p>该会话还没有面试报告</p>
      <button class="btn-generate" @click="doGenerate" :disabled="generating">
        🤖 生成报告
      </button>
    </div>

    <!-- 生成中 -->
    <div v-if="generating" class="generating-box">
      <LoadingSpinner text="AI 正在综合评估生成报告，请稍候..." />
      <p class="gen-hint">这可能需要 15-40 秒</p>
    </div>

    <!-- 报告内容 -->
    <template v-if="report">
      <ReportSummaryCard :report="report" />
      <ScoreRadarChart :report="report" />
      <DimensionBreakdown :report="report" />

      <div class="meta-footer">
        <span v-if="report.agent_model">🤖 {{ report.agent_model }}</span>
        <span v-if="report.tokens_used">🪙 {{ report.tokens_used }} tokens</span>
        <span v-if="report.processing_ms">⏱️ {{ (report.processing_ms / 1000).toFixed(1) }}s</span>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import ReportSummaryCard from '@/components/report/ReportSummaryCard.vue'
import ScoreRadarChart from '@/components/report/ScoreRadarChart.vue'
import DimensionBreakdown from '@/components/report/DimensionBreakdown.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import ErrorBanner from '@/components/common/ErrorBanner.vue'
import { reportsApi } from '@/api/reports'

const route = useRoute()
const sessionId = route.params.sessionId as string

const report = ref<any>(null)
const loading = ref(true)
const generating = ref(false)
const error = ref('')

onMounted(async () => {
  loading.value = true
  try {
    const res = await reportsApi.get(sessionId)
    report.value = res.data
  } catch (e: any) {
    // 404 = 还没生成，前端显示生成按钮
    if (e.status !== 404) {
      error.value = e.message || '加载报告失败'
    }
  } finally {
    loading.value = false
  }
})

async function doGenerate() {
  generating.value = true
  error.value = ''
  try {
    const res = await reportsApi.generate(sessionId)
    report.value = res.data
  } catch (e: any) {
    error.value = e.message || '报告生成失败'
  } finally {
    generating.value = false
  }
}
</script>

<style scoped>
.page-title { font-size: 22px; margin-bottom: 24px; }
.empty-box {
  max-width: 600px;
  text-align: center;
  padding: 48px;
  background: #fff;
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.empty-box p { font-size: 15px; color: #666; margin-bottom: 20px; }
.btn-generate {
  padding: 12px 28px;
  font-size: 15px;
  font-weight: 600;
  background: #1a73e8;
  color: #fff;
  border: none;
  border-radius: 8px;
  cursor: pointer;
}
.btn-generate:hover:not(:disabled) { background: #1557b0; }
.btn-generate:disabled { opacity: 0.6; cursor: not-allowed; }
.generating-box { text-align: center; padding: 60px 20px; }
.gen-hint { font-size: 13px; color: #999; margin-top: 12px; }
.meta-footer {
  max-width: 800px;
  margin-top: 20px;
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: #999;
  justify-content: center;
}
</style>
