<template>
  <div class="resume-analysis">
    <h2 class="page-title">📊 简历分析</h2>
    <ResumeAnalysisPanel v-if="analysis" :analysis="analysis" />
    <LoadingSpinner v-else-if="loading" text="正在分析简历..." />
    <EmptyState v-else text="暂无分析结果" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import ResumeAnalysisPanel from '@/components/resume/ResumeAnalysisPanel.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import EmptyState from '@/components/common/EmptyState.vue'

const route = useRoute()
const analysis = ref(null)
const loading = ref(true)

onMounted(async () => {
  const resumeId = route.params.resumeId
  // API call would go here
  loading.value = false
})
</script>

<style scoped>
.page-title {
  font-size: 22px;
  margin-bottom: 24px;
}
</style>
