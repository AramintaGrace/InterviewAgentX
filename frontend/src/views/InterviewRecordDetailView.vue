<template>
  <div class="record-detail">
    <h2 class="page-title">📋 记录详情</h2>
    <div v-if="record" class="detail-content">
      <div class="info-card">
        <h3>候选人信息</h3>
        <p>姓名：{{ record.candidateName }}</p>
        <p>邮箱：{{ record.candidateEmail }}</p>
      </div>
      <div class="report-card">
        <h3>面试报告</h3>
        <p>综合评分：{{ record.overallScore }}</p>
        <router-link :to="`/reports/${record.sessionId}`">查看完整报告</router-link>
      </div>
    </div>
    <EmptyState v-else text="未找到记录" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import EmptyState from '@/components/common/EmptyState.vue'

const route = useRoute()
const record = ref(null)

onMounted(async () => {
  // API call
})
</script>

<style scoped>
.page-title { font-size: 22px; margin-bottom: 24px; }
.detail-content { display: flex; flex-direction: column; gap: 16px; }
.info-card, .report-card { background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
</style>
