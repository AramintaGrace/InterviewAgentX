<template>
  <div class="dashboard">
    <h2 class="page-title">📊 首页概览</h2>
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-value">{{ stats.totalResumes }}</div>
        <div class="stat-label">简历总数</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ stats.totalInterviews }}</div>
        <div class="stat-label">面试会话</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ stats.totalReports }}</div>
        <div class="stat-label">面试报告</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ stats.totalKBItems }}</div>
        <div class="stat-label">知识库条目</div>
      </div>
    </div>
    <div class="quick-actions">
      <h3>快捷操作</h3>
      <div class="action-buttons">
        <router-link to="/resumes/upload" class="action-btn">📄 上传简历</router-link>
        <router-link to="/interviews/create" class="action-btn">🎤 创建面试</router-link>
        <router-link to="/knowledge-base/create" class="action-btn">📚 添加知识库</router-link>
        <router-link to="/records" class="action-btn">📋 查看记录</router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const stats = ref({
  totalResumes: 0,
  totalInterviews: 0,
  totalReports: 0,
  totalKBItems: 0,
})
</script>

<style scoped>
.dashboard {
  max-width: 900px;
}

.page-title {
  font-size: 22px;
  margin-bottom: 24px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 32px;
}

.stat-card {
  background: #fff;
  border-radius: 8px;
  padding: 24px;
  text-align: center;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: #1a1a2e;
}

.stat-label {
  font-size: 14px;
  color: #999;
  margin-top: 4px;
}

.quick-actions h3 {
  font-size: 16px;
  margin-bottom: 12px;
}

.action-buttons {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.action-btn {
  display: inline-block;
  padding: 12px 24px;
  background: #4a90d9;
  color: #fff;
  border-radius: 6px;
  text-decoration: none;
  font-size: 14px;
  transition: background 0.2s;
}

.action-btn:hover {
  background: #357abd;
}
</style>
