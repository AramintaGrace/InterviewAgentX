<template>
  <div class="resume-analysis-page">
    <h2 class="page-title">📊 简历分析</h2>

    <!-- Loading -->
    <LoadingSpinner v-if="loading" text="正在调用 AI 分析简历..." />

    <!-- Error -->
    <ErrorBanner v-if="error" :message="error" @dismiss="error = ''" />

    <!-- 分析中（触发后等待） -->
    <div v-if="analyzing" class="analyzing-box">
      <LoadingSpinner text="AI 正在深度分析简历，请稍候..." />
      <p class="analyzing-hint">这可能需要 10-30 秒，取决于简历内容长度</p>
    </div>

    <!-- 结果 -->
    <ResumeAnalysisPanel v-if="analysis" :analysis="analysis" />

    <!-- 操作按钮 -->
    <div v-if="analysis && !analyzing" class="action-section">
      <button class="btn-reanalyze" @click="triggerAnalysis()">🔄 重新分析</button>
      <router-link to="/resumes/upload" class="btn-new-resume">📄 分析新简历</router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import ResumeAnalysisPanel from '@/components/resume/ResumeAnalysisPanel.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import ErrorBanner from '@/components/common/ErrorBanner.vue'
import { resumesApi } from '@/api/resumes'

const route = useRoute()
const analysis = ref<any>(null)
const loading = ref(true)
const analyzing = ref(false)
const error = ref('')

onMounted(async () => {
  const resumeId = route.params.resumeId as string
  // 先尝试获取已有分析
  await loadExistingAnalysis(resumeId)
})

async function loadExistingAnalysis(resumeId: string) {
  loading.value = true
  error.value = ''
  try {
    const res = await resumesApi.getResumeAnalysis(resumeId)
    analysis.value = res.data
  } catch (e: any) {
    // 404 表示还没有分析过，自动触发
    if (e.status === 404) {
      await triggerAnalysis(resumeId)
    } else {
      error.value = e.message || '获取分析结果失败'
    }
  } finally {
    loading.value = false
  }
}

async function triggerAnalysis(resumeId?: string) {
  const id = resumeId || (route.params.resumeId as string)
  analyzing.value = true
  error.value = ''
  try {
    const res = await resumesApi.analyzeResume(id)
    analysis.value = res.data
  } catch (e: any) {
    error.value = e.message || 'AI 分析失败，请稍后重试'
  } finally {
    analyzing.value = false
  }
}
</script>

<style scoped>
.page-title {
  font-size: 22px;
  margin-bottom: 24px;
}

.analyzing-box {
  text-align: center;
  padding: 60px 20px;
}
.analyzing-hint {
  font-size: 13px;
  color: #999;
  margin-top: 12px;
}

.action-section {
  max-width: 800px;
  margin-top: 24px;
  display: flex;
  gap: 12px;
  justify-content: center;
}
.btn-reanalyze {
  padding: 10px 24px;
  font-size: 14px;
  border: 1px solid #6366f1;
  border-radius: 8px;
  background: #eef2ff;
  color: #4f46e5;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-reanalyze:hover { background: #e0e7ff; }
.btn-new-resume {
  display: inline-block;
  padding: 10px 24px;
  font-size: 14px;
  border: none;
  border-radius: 8px;
  background: #1a73e8;
  color: #fff;
  text-decoration: none;
  transition: all 0.2s;
}
.btn-new-resume:hover { background: #1557b0; }
</style>
