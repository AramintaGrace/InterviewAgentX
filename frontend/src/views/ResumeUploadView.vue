<template>
  <div class="resume-upload">
    <h2 class="page-title">📄 上传简历</h2>
    <ResumeUploader @uploaded="onUploaded" />
    <ResumeInfoCard v-if="resume" :resume="resume" />

    <!-- 操作按钮 -->
    <div v-if="resume" class="next-actions">
      <button
        v-if="resume.ocr_status === 'completed'"
        class="btn-analyze"
        @click="startAnalysis"
        :disabled="analyzing"
      >
        {{ analyzing ? '⏳ 分析中...' : analysisResult ? '🔄 重新分析' : '🤖 AI 分析简历' }}
      </button>
      <router-link :to="`/interviews/create?resume_id=${resume.id}`" class="btn-new-interview">
        🎙️ 创建面试
      </router-link>
      <button class="btn-new-resume" @click="resetAll">📄 分析新简历</button>
    </div>

    <!-- 分析中 -->
    <div v-if="analyzing" class="analyzing-box">
      <LoadingSpinner text="AI 正在深度分析简历，请稍候..." />
      <p class="analyzing-hint">这可能需要 10-30 秒，取决于简历内容长度</p>
    </div>

    <!-- 分析错误 -->
    <ErrorBanner v-if="analysisError" :message="analysisError" @dismiss="analysisError = ''" />

    <!-- 分析结果 -->
    <ResumeAnalysisPanel v-if="analysisResult" :analysis="analysisResult" />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import ResumeUploader from '@/components/resume/ResumeUploader.vue'
import ResumeInfoCard from '@/components/resume/ResumeInfoCard.vue'
import ResumeAnalysisPanel from '@/components/resume/ResumeAnalysisPanel.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import ErrorBanner from '@/components/common/ErrorBanner.vue'
import { resumesApi } from '@/api/resumes'

const resume = ref<any>(null)
const analyzing = ref(false)
const analysisError = ref('')
const analysisResult = ref<any>(null)

function onUploaded(data: any) {
  resume.value = data
  // 切换简历时清掉旧分析结果
  if (analysisResult.value) {
    analysisResult.value = null
    analysisError.value = ''
  }
}

async function startAnalysis() {
  if (!resume.value?.id) return
  analyzing.value = true
  analysisError.value = ''
  analysisResult.value = null

  try {
    const res = await resumesApi.analyzeResume(resume.value.id)
    analysisResult.value = res.data
  } catch (e: any) {
    analysisError.value = e.message || 'AI 分析失败，请稍后重试'
  } finally {
    analyzing.value = false
  }
}

function resetAll() {
  resume.value = null
  analysisResult.value = null
  analysisError.value = ''
  analyzing.value = false
}
</script>

<style scoped>
.page-title {
  font-size: 22px;
  margin-bottom: 24px;
}

.next-actions {
  max-width: 720px;
  margin-top: 24px;
  display: flex;
  gap: 12px;
}
.btn-analyze, .btn-new-interview {
  display: inline-block;
  padding: 10px 20px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
}
.btn-analyze {
  background: #1a73e8;
  color: #fff;
  border: none;
}
.btn-analyze:hover:not(:disabled) { background: #1557b0; }
.btn-analyze:disabled { opacity: 0.6; cursor: not-allowed; }
.btn-new-interview {
  background: #e8f0fe;
  color: #1a73e8;
  border: 1px solid #1a73e8;
  text-decoration: none;
}
.btn-new-interview:hover { background: #d2e3fc; }
.btn-new-resume {
  background: #fff;
  color: #1a73e8;
  border: 1px solid #1a73e8;
  padding: 10px 20px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
}
.btn-new-resume:hover { background: #e8f0fe; }

.analyzing-box {
  max-width: 720px;
  text-align: center;
  padding: 48px 20px;
}
.analyzing-hint {
  font-size: 13px;
  color: #999;
  margin-top: 12px;
}
</style>
